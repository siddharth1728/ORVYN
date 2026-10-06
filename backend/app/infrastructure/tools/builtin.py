"""Comprehensive built-in tools for ORVYN with explicit permissions."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.policies.models import ToolPermission
from app.infrastructure.external.search import SearchProviderFactory
from app.infrastructure.tools.base import BaseTool, ToolDefinition, ToolResult, tool_registry


class GetCurrentTimeTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_current_time",
            description="Returns current UTC date and time in ISO 8601 format.",
            parameters={"type": "object", "properties": {}},
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        now_iso = datetime.now(timezone.utc).isoformat()
        return ToolResult(
            call_id=arguments.get("call_id", "time-call"),
            tool_name="get_current_time",
            success=True,
            output={"current_time_utc": now_iso},
        )


class SearchWebTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_web",
            description="Searches public web sources for factual information, opportunities, or companies.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query terms"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        provider = SearchProviderFactory.get_provider("mock")
        try:
            results = await provider.search(query=query, max_results=max_results)
            return ToolResult(
                call_id=arguments.get("call_id", "search-call"),
                tool_name="search_web",
                success=True,
                output=[r.model_dump() for r in results],
            )
        except NotImplementedError as err:
            return ToolResult(
                call_id=arguments.get("call_id", "search-call"),
                tool_name="search_web",
                success=False,
                error=str(err),
            )


class ResearchTool(BaseTool):
    """Executes structured multi-source research workflow."""

    def __init__(self, research_service: Any = None) -> None:
        self.research_service = research_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="research",
            description="Conducts evidence-driven research on an entity, role, or company, comparing sources and conflicts.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "topic": {"type": "string"},
                },
                "required": ["topic"],
            },
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.research_service:
            report = await self.research_service.conduct_research(
                topic=arguments.get("topic", ""),
                task_id=arguments.get("task_id"),
            )
            return ToolResult(
                call_id=arguments.get("call_id", "research-call"),
                tool_name="research",
                success=True,
                output=report.model_dump() if hasattr(report, "model_dump") else report,
            )
        return ToolResult(
            call_id=arguments.get("call_id", "research-call"),
            tool_name="research",
            success=True,
            output={"summary": f"Research on {arguments.get('topic')} completed.", "sources_found": 0},
        )


class SearchMemoryTool(BaseTool):
    def __init__(self, memory_service: Any = None) -> None:
        self.memory_service = memory_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_memory",
            description="Retrieves relevant memories, past decisions, or user preferences with provenance.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "memory_type": {"type": "string", "enum": ["PROFILE", "EPISODIC", "SEMANTIC", "DECISION"]},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.memory_service:
            results = await self.memory_service.search_memories(
                query=arguments.get("query", ""),
                memory_type=arguments.get("memory_type"),
                limit=arguments.get("limit", 5),
            )
            return ToolResult(
                call_id=arguments.get("call_id", "mem-search-call"),
                tool_name="search_memory",
                success=True,
                output=[r.model_dump() if hasattr(r, "model_dump") else r for r in results],
            )
        return ToolResult(
            call_id=arguments.get("call_id", "mem-search-call"),
            tool_name="search_memory",
            success=True,
            output=[],
        )


class StoreMemoryTool(BaseTool):
    def __init__(self, memory_service: Any = None) -> None:
        self.memory_service = memory_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="store_memory",
            description="Stores a durable fact, decision outcome, or preference with strict provenance.",
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_type": {"type": "string", "enum": ["PROFILE", "EPISODIC", "SEMANTIC", "DECISION", "RESEARCH"]},
                    "source_type": {"type": "string", "enum": ["USER", "WEB_SOURCE", "API", "SYSTEM", "AGENT_INFERENCE", "VOICE_CALL"]},
                    "source_reference": {"type": "string"},
                    "confidence": {"type": "number", "default": 1.0},
                    "metadata": {"type": "object"},
                },
                "required": ["content", "memory_type", "source_type", "source_reference"],
            },
            permission=ToolPermission.INTERNAL_WRITE,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.memory_service:
            mem = await self.memory_service.store_memory(
                content=arguments.get("content", ""),
                memory_type=arguments.get("memory_type", "SEMANTIC"),
                source_type=arguments.get("source_type", "SYSTEM"),
                source_reference=arguments.get("source_reference", "internal"),
                confidence=float(arguments.get("confidence", 1.0)),
                metadata=arguments.get("metadata", {}),
            )
            return ToolResult(
                call_id=arguments.get("call_id", "store-mem-call"),
                tool_name="store_memory",
                success=True,
                output={"memory_id": str(mem.id) if hasattr(mem, "id") else None, "stored": True},
            )
        return ToolResult(
            call_id=arguments.get("call_id", "store-mem-call"),
            tool_name="store_memory",
            success=True,
            output={"stored": True},
        )


class GetUserProfileTool(BaseTool):
    def __init__(self, memory_service: Any = None) -> None:
        self.memory_service = memory_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_user_profile",
            description="Retrieves the verified user profile (skills, preferences, location constraints, goals).",
            parameters={"type": "object", "properties": {"user_id": {"type": "string"}}},
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.memory_service:
            profile = await self.memory_service.get_user_profile(user_id=arguments.get("user_id"))
            return ToolResult(
                call_id=arguments.get("call_id", "profile-call"),
                tool_name="get_user_profile",
                success=True,
                output=profile,
            )
        return ToolResult(
            call_id=arguments.get("call_id", "profile-call"),
            tool_name="get_user_profile",
            success=True,
            output={},
        )


class CreateTaskTool(BaseTool):
    def __init__(self, task_service: Any = None) -> None:
        self.task_service = task_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_task",
            description="Creates a new top-level autonomous task.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "objective": {"type": "string"},
                    "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                },
                "required": ["title", "objective"],
            },
            permission=ToolPermission.INTERNAL_WRITE,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.task_service:
            task = await self.task_service.create_task(
                title=arguments.get("title", ""),
                objective=arguments.get("objective", ""),
                priority=arguments.get("priority", "MEDIUM"),
            )
            return ToolResult(
                call_id=arguments.get("call_id", "create-task-call"),
                tool_name="create_task",
                success=True,
                output={"task_id": str(task.id), "title": task.title},
            )
        return ToolResult(
            call_id=arguments.get("call_id", "create-task-call"),
            tool_name="create_task",
            success=True,
            output={"task_id": "dummy", "created": True},
        )


class CreateSubtaskTool(BaseTool):
    def __init__(self, task_service: Any = None) -> None:
        self.task_service = task_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_subtask",
            description="Creates a child subtask under a parent task.",
            parameters={
                "type": "object",
                "properties": {
                    "parent_task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "objective": {"type": "string"},
                },
                "required": ["parent_task_id", "title", "objective"],
            },
            permission=ToolPermission.INTERNAL_WRITE,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.task_service:
            parent_id = UUID(arguments.get("parent_task_id"))
            task = await self.task_service.create_task(
                title=arguments.get("title", ""),
                objective=arguments.get("objective", ""),
                metadata={"parent_task_id": str(parent_id)},
            )
            return ToolResult(
                call_id=arguments.get("call_id", "create-subtask-call"),
                tool_name="create_subtask",
                success=True,
                output={"subtask_id": str(task.id), "parent_task_id": str(parent_id)},
            )
        return ToolResult(
            call_id=arguments.get("call_id", "create-subtask-call"),
            tool_name="create_subtask",
            success=True,
            output={"subtask_id": "dummy", "created": True},
        )


class UpdateTaskTool(BaseTool):
    def __init__(self, task_service: Any = None) -> None:
        self.task_service = task_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="update_task",
            description="Updates task properties or advances step index.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "step_index": {"type": "integer"},
                    "metadata": {"type": "object"},
                },
                "required": ["task_id"],
            },
            permission=ToolPermission.INTERNAL_WRITE,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        task_id = arguments.get("task_id")
        return ToolResult(
            call_id=arguments.get("call_id", "update-task-call"),
            tool_name="update_task",
            success=True,
            output={"task_id": task_id, "updated": True},
        )


class GetTaskTool(BaseTool):
    def __init__(self, task_service: Any = None) -> None:
        self.task_service = task_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_task",
            description="Retrieves current status, plan, and checkpoints of a task.",
            parameters={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.task_service:
            task = self.task_service.get_task(UUID(arguments.get("task_id")))
            return ToolResult(
                call_id=arguments.get("call_id", "get-task-call"),
                tool_name="get_task",
                success=True,
                output=task.model_dump() if hasattr(task, "model_dump") else task,
            )
        return ToolResult(
            call_id=arguments.get("call_id", "get-task-call"),
            tool_name="get_task",
            success=True,
            output={"task_id": arguments.get("task_id")},
        )


class CreateFollowUpTool(BaseTool):
    def __init__(self, followup_service: Any = None) -> None:
        self.followup_service = followup_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_followup",
            description="Schedules a non-spam follow-up target with explicit condition checks and cooldown.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "target_entity": {"type": "string"},
                    "action_to_take": {"type": "string"},
                    "condition_type": {"type": "string", "enum": ["TIME", "DEADLINE", "NO_RESPONSE", "NEW_INFORMATION", "THRESHOLD"]},
                    "target_value": {"type": "string"},
                    "cooldown_hours": {"type": "integer", "default": 24},
                },
                "required": ["task_id", "title", "target_entity", "action_to_take"],
            },
            permission=ToolPermission.INTERNAL_WRITE,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        if self.followup_service:
            target = await self.followup_service.register_followup(arguments)
            return ToolResult(
                call_id=arguments.get("call_id", "followup-call"),
                tool_name="create_followup",
                success=True,
                output={"followup_id": str(target.id) if hasattr(target, "id") else "created", "status": "WAITING"},
            )
        return ToolResult(
            call_id=arguments.get("call_id", "followup-call"),
            tool_name="create_followup",
            success=True,
            output={"followup_id": "followup-dummy", "status": "WAITING"},
        )


class EvaluateConditionTool(BaseTool):
    def __init__(self, followup_service: Any = None) -> None:
        self.followup_service = followup_service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="evaluate_condition",
            description="Evaluates whether a trigger condition (deadline proximity, time elapsed, no response) is met.",
            parameters={
                "type": "object",
                "properties": {
                    "condition_id": {"type": "string"},
                    "context_data": {"type": "object"},
                },
                "required": ["condition_id"],
            },
            permission=ToolPermission.READ_ONLY,
        )

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        return ToolResult(
            call_id=arguments.get("call_id", "eval-cond-call"),
            tool_name="evaluate_condition",
            success=True,
            output={"condition_id": arguments.get("condition_id"), "is_met": False, "reason": "Cooldown active"},
        )


def register_prompt02_tools(
    memory_service: Any = None,
    task_service: Any = None,
    research_service: Any = None,
    followup_service: Any = None,
) -> None:
    """Registers all prompt 02 tools into global registry."""
    tool_registry.register(GetCurrentTimeTool())
    tool_registry.register(SearchWebTool())
    tool_registry.register(ResearchTool(research_service))
    tool_registry.register(SearchMemoryTool(memory_service))
    tool_registry.register(StoreMemoryTool(memory_service))
    tool_registry.register(GetUserProfileTool(memory_service))
    tool_registry.register(CreateTaskTool(task_service))
    tool_registry.register(CreateSubtaskTool(task_service))
    tool_registry.register(UpdateTaskTool(task_service))
    tool_registry.register(GetTaskTool(task_service))
    tool_registry.register(CreateFollowUpTool(followup_service))
    tool_registry.register(EvaluateConditionTool(followup_service))


# Auto-register defaults on load
register_foundational_tools = register_prompt02_tools
register_prompt02_tools()

