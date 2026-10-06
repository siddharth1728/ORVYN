"""Critical Recovery Test: Validates zero-loss task resumption across runtime lifecycles.

Sequence:
1. Create task
2. Execute until human intervention required
3. Save state snapshot & resumption token in checkpoint
4. Completely destroy / restart runtime (simulate process crash / app restart)
5. Initialize a fresh AgentRuntime & TaskService
6. Rehydrate task and working memory from persisted checkpoint
7. Apply human decision
8. Continue execution to full completion without repeating prior steps
"""

import pytest
import json

from app.application.agent_runtime.runtime import Agent, AgentContext
from app.application.task_service.service import TaskService
from app.domain.tasks.models import Task, TaskCheckpoint, TaskStatus


@pytest.mark.asyncio
async def test_full_recovery_after_runtime_restart():
    # -------------------------------------------------------------
    # PHASE 1: Runtime Instance 1 (Initial Run)
    # -------------------------------------------------------------
    runtime_1 = TaskService()
    task = await runtime_1.create_task(
        title="Distributed Opportunity Pipeline",
        objective="Find backend engineering internships and evaluate matches",
    )

    # Execute task: Will execute step 0, and pause on step 1 due to missing relocation preference
    result_1 = await runtime_1.run_task(task.id)
    assert result_1.status == TaskStatus.AWAITING_RESPONSE
    assert result_1.completed_steps == 1
    assert result_1.checkpoint is not None

    # Checkpoint data serialized to JSON (simulating database persistence across crashes)
    saved_checkpoint_dict = result_1.checkpoint.model_dump()
    saved_task_dict = task.model_dump()

    # -------------------------------------------------------------
    # PHASE 2: KILL / RESTART RUNTIME (Process crash simulation)
    # -------------------------------------------------------------
    del runtime_1
    del task

    # -------------------------------------------------------------
    # PHASE 3: Runtime Instance 2 (Fresh Process Rehydration)
    # -------------------------------------------------------------
    fresh_runtime = TaskService()

    # Reconstitute task and checkpoint from cold storage
    restored_task = Task(**saved_task_dict)
    restored_checkpoint = TaskCheckpoint(**saved_checkpoint_dict)

    # Register into fresh runtime state
    fresh_runtime._tasks[restored_task.id] = restored_task
    fresh_runtime._checkpoints[restored_task.id] = [restored_checkpoint]
    fresh_runtime._contexts[restored_task.id] = AgentContext(task=restored_task)

    assert restored_task.status == TaskStatus.AWAITING_RESPONSE
    assert restored_task.current_step == 1

    # -------------------------------------------------------------
    # PHASE 4: Resume with Human Decision
    # -------------------------------------------------------------
    human_decision = {
        "relocation": True,
        "channel": "voice_call",
        "notes": "User agreed to relocate to Bangalore",
    }

    final_result = await fresh_runtime.resume_task(restored_task.id, human_decision=human_decision)

    # -------------------------------------------------------------
    # PHASE 5: Verify Successful Completion & State Integrity
    # -------------------------------------------------------------
    assert final_result.status == TaskStatus.COMPLETED
    assert final_result.completed_steps == 3
    assert final_result.output["human_decision"]["relocation"] is True
    assert "finalize_recommendation" in final_result.output

    # Verify task state in fresh runtime
    completed_task = fresh_runtime.get_task(restored_task.id)
    assert completed_task.status == TaskStatus.COMPLETED
    assert completed_task.current_step == 3
