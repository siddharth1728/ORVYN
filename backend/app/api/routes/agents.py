"""Agent inspection routes."""

from typing import Any, Dict, List
from fastapi import APIRouter
from app.infrastructure.tools.base import tool_registry

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("")
def list_agents() -> List[Dict[str, Any]]:
    """Lists registered autonomous agents and their capabilities."""
    tools = tool_registry.list_definitions()
    return [
        {
            "name": "ORVYN-Core",
            "description": "Autonomous execution engine with Human-in-the-Loop decision gateway.",
            "version": "0.1.0",
            "status": "ready",
            "capabilities": [t.name for t in tools],
        }
    ]
