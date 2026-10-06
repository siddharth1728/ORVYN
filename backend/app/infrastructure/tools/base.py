"""Tool calling primitives, permission boundaries, and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.domain.policies.models import AgentPolicy, ToolPermission, default_policy


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    permission: ToolPermission = ToolPermission.READ_ONLY


class ToolCall(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class ToolResult(BaseModel):
    call_id: str
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    permission_blocked: bool = False


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Returns the JSON schema definition for the tool."""
        pass

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Executes the tool with given arguments."""
        pass


class ToolRegistry:
    """Registry maintaining available tools with permission enforcement."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._idempotency_cache: Dict[str, ToolResult] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.definition.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_definitions(self) -> List[ToolDefinition]:
        return [t.definition for t in self._tools.values()]

    async def execute(
        self,
        tool_call: ToolCall,
        policy: Optional[AgentPolicy] = None,
    ) -> ToolResult:
        pol = policy or default_policy

        # 1. Idempotency check for external or critical actions
        if tool_call.idempotency_key and tool_call.idempotency_key in self._idempotency_cache:
            cached = self._idempotency_cache[tool_call.idempotency_key]
            return cached

        # 2. Tool existence check
        tool = self.get_tool(tool_call.tool_name)
        if not tool:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                error=f"Tool '{tool_call.tool_name}' is not registered in ToolRegistry.",
            )

        # 3. Policy & Permission enforcement
        perm = tool.definition.permission
        if perm == ToolPermission.HUMAN_APPROVAL_REQUIRED:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                permission_blocked=True,
                error=f"Tool '{tool_call.tool_name}' requires explicit human approval before execution.",
            )

        if perm == ToolPermission.EXTERNAL_ACTION and pol.require_approval_for_external_actions:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                permission_blocked=True,
                error=f"Tool '{tool_call.tool_name}' is an external action requiring human approval by policy.",
            )

        if tool_call.tool_name in pol.prohibited_tools:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                permission_blocked=True,
                error=f"Tool '{tool_call.tool_name}' is prohibited by policy.",
            )

        # 4. Tool Execution
        try:
            result = await tool.execute(tool_call.arguments)
            if tool_call.idempotency_key and result.success:
                self._idempotency_cache[tool_call.idempotency_key] = result
            return result
        except Exception as exc:
            return ToolResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                error=f"Tool execution failed: {str(exc)}",
            )


# Global tool registry
tool_registry = ToolRegistry()
