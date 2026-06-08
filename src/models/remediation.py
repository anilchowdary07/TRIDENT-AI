"""
TRIDENT-AI Remediation Option Model.

Defines the structure for AI-generated remediation recommendations.
Each incident package includes 3 prioritised remediation options
with risk levels, recovery time estimates, and MCP tool call specs.

Usage:
    from src.models.remediation import RemediationOption
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level for a remediation action."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RemediationStatus(str, Enum):
    """Status of a remediation action."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class MCPToolCall(BaseModel):
    """Specification for an MCP tool call to execute a remediation action."""
    tool: str = Field(..., description="MCP tool name to invoke")
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the MCP tool",
    )


class RemediationOption(BaseModel):
    """
    A single remediation option for an incident.

    Bedrock generates 3 of these per incident, prioritised 1-3.
    The analyst approves one, which triggers an MCP tool call.
    """
    priority: int = Field(
        ..., ge=1, le=3,
        description="Priority ranking (1 = highest priority)",
    )
    action: str = Field(
        ...,
        description="Human-readable action description",
    )
    rationale: str = Field(
        default="",
        description="Why this remediation is recommended",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Risk level of executing this action",
    )
    estimated_recovery_minutes: int = Field(
        default=5, ge=0,
        description="Estimated time to recover after executing this action",
    )
    requires_approval: bool = Field(
        default=True,
        description="Whether this action requires human approval",
    )
    mcp_tool_call: Optional[MCPToolCall] = Field(
        default=None,
        description="MCP tool call specification for automated execution",
    )
    status: RemediationStatus = Field(
        default=RemediationStatus.PENDING,
        description="Current status of this remediation option",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Username of the approver",
    )
    approved_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when approved",
    )
    execution_log: list[str] = Field(
        default_factory=list,
        description="Log of execution steps",
    )
