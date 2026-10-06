"""Task application service coordinating state, persistence, and execution."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.agent_runtime.runtime import Agent, AgentContext, AgentResult
from app.core.exceptions import OrvynError
from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.tasks.models import Task, TaskCheckpoint, TaskPriority, TaskStatus
from app.domain.tasks.state_machine import TaskStateMachine


class TaskNotFoundError(OrvynError):
    pass


class TaskService:
    """Manages the full lifecycle of tasks, checkpoints, and execution."""

    def __init__(self, agent: Optional[Agent] = None) -> None:
        self.agent = agent or Agent()
        # In-memory storage for tasks and checkpoints (backed by DB in persistence layer)
        self._tasks: Dict[UUID, Task] = {}
        self._checkpoints: Dict[UUID, List[TaskCheckpoint]] = {}
        self._contexts: Dict[UUID, AgentContext] = {}

    async def create_task(
        self,
        title: str,
        objective: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        task = Task(
            title=title,
            objective=objective,
            priority=priority,
            metadata=metadata or {},
        )
        self._tasks[task.id] = task
        self._checkpoints[task.id] = []
        self._contexts[task.id] = AgentContext(task=task)

        # Dispatch creation event
        await dispatcher.dispatch(
            Event(
                event_type="TASK_CREATED",
                task_id=task.id,
                payload={"title": task.title, "objective": task.objective},
            )
        )
        return task

    def get_task(self, task_id: UUID) -> Task:
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(f"Task '{task_id}' not found.")
        return task

    def list_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def get_checkpoints(self, task_id: UUID) -> List[TaskCheckpoint]:
        return self._checkpoints.get(task_id, [])

    async def run_task(self, task_id: UUID) -> AgentResult:
        task = self.get_task(task_id)
        context = self._contexts[task_id]
        result = await self.agent.run(context)
        if result.checkpoint:
            self._checkpoints[task_id].append(result.checkpoint)
        return result

    async def pause_task(self, task_id: UUID, reason: str = "User requested pause") -> Task:
        task = self.get_task(task_id)
        TaskStateMachine.transition(task, TaskStatus.WAITING, reason=reason)
        await dispatcher.dispatch(
            Event(event_type="TASK_PAUSED", task_id=task.id, payload={"reason": reason})
        )
        return task

    async def resume_task(self, task_id: UUID, human_decision: Optional[Dict[str, Any]] = None) -> AgentResult:
        task = self.get_task(task_id)
        context = self._contexts[task_id]
        checkpoints = self.get_checkpoints(task_id)

        if not checkpoints:
            # If no prior checkpoint, continue from current context
            return await self.agent.run(context)

        latest_checkpoint = checkpoints[-1]
        result = await self.agent.resume(context, latest_checkpoint, human_decision or {})
        if result.checkpoint:
            self._checkpoints[task_id].append(result.checkpoint)
        return result

    async def cancel_task(self, task_id: UUID, reason: str = "User requested cancellation") -> Task:
        task = self.get_task(task_id)
        TaskStateMachine.transition(task, TaskStatus.CANCELLED, reason=reason)
        await dispatcher.dispatch(
            Event(event_type="TASK_CANCELLED", task_id=task.id, payload={"reason": reason})
        )
        return task


# Global singleton instance
task_service = TaskService()
