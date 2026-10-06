"""Agent policies and tool permission models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ToolPermission(str, Enum):
    """Permission classifications for agent actions."""
    READ_ONLY = "READ_ONLY"
    INTERNAL_WRITE = "INTERNAL_WRITE"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


class AgentPolicy(BaseModel):
    """Deterministic policy rules governing agent autonomy."""
    allow_autonomous_internal_writes: bool = True
    allow_autonomous_read_only: bool = True
    require_approval_for_external_actions: bool = True
    require_approval_for_destructive_actions: bool = True
    max_step_retries: int = 3
    step_timeout_seconds: int = 120
    max_autonomous_iterations: int = 15
    prohibited_tools: List[str] = Field(default_factory=list)
    call_escalation_urgency_threshold: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"


# Default system policy
default_policy = AgentPolicy()
