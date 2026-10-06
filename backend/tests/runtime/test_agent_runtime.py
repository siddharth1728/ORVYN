"""Agent runtime execution tests: task creation, execution, pause, and resumption."""

import pytest

from app.application.agent_runtime.runtime import Agent, AgentContext
from app.application.task_service.service import TaskService
from app.domain.tasks.models import Task, TaskStatus


@pytest.mark.asyncio
async def test_agent_autonomous_execution_to_completion():
    """When all required preferences are known, agent executes all steps to completion."""
    task = Task(title="Autonomous Search", objective="Find roles")
    # Provide known preference so decision engine does not block
    context = AgentContext(task=task, user_preferences={"relocation": True})

    agent = Agent()
    result = await agent.run(context)

    assert result.status == TaskStatus.COMPLETED
    assert result.completed_steps == 3
    assert "finalize_recommendation" in result.output


@pytest.mark.asyncio
async def test_agent_interrupts_when_preference_missing():
    """When relocation preference is missing, agent interrupts, saves checkpoint, and pauses."""
    task = Task(title="Interrupted Search", objective="Find roles")
    context = AgentContext(task=task, user_preferences={})  # Missing "relocation"

    agent = Agent()
    result = await agent.run(context)

    assert result.status == TaskStatus.AWAITING_RESPONSE
    assert result.checkpoint is not None
    assert result.interrupted_reason is not None
    assert "relocation" in result.interrupted_reason


@pytest.mark.asyncio
async def test_task_service_pause_and_cancel():
    service = TaskService()
    task = await service.create_task(title="Pause Task", objective="Test pause")

    # Start/run to EXECUTING before pausing
    from app.domain.tasks.state_machine import TaskStateMachine
    TaskStateMachine.transition(task, TaskStatus.PLANNING)
    TaskStateMachine.transition(task, TaskStatus.EXECUTING)

    # Pause task
    paused_task = await service.pause_task(task.id, reason="User clicked pause")
    assert paused_task.status == TaskStatus.WAITING

    # Cancel task
    cancelled_task = await service.cancel_task(task.id)
    assert cancelled_task.status == TaskStatus.CANCELLED
