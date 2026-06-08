"""
TRIDENT-AI Incident Package Model.

The crown jewel data model — represents a complete incident package
synthesised by AWS Bedrock from all 3 agent findings. This is what
gets written to the Splunk `trident_incidents` index and displayed
in the dashboard.

Usage:
    from src.models.incident import IncidentPackage
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Incident severity level."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentStatus(str, Enum):
    """Lifecycle status of an incident."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    REMEDIATING = "REMEDIATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class MitreTechnique(BaseModel):
    """A MITRE ATT&CK technique entry."""
    id: str = Field(..., description="T-code (e.g., T1110)")
    name: str = Field(default="", description="Technique name")
    tactic: str = Field(default="", description="Associated tactic phase")


class TimelineEvent(BaseModel):
    """A single event in the attack timeline."""
    timestamp: str = Field(..., description="ISO8601 timestamp")
    event: str = Field(..., description="Description of what happened")
    source: str = Field(
        default="telemetry",
        description="Source agent: telemetry | security | platform",
    )


class IOCs(BaseModel):
    """Indicators of Compromise extracted from the incident."""
    ips: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    users: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    """Raw agent output preserved for transparency and trust."""
    telemetry_sentinel: dict[str, Any] = Field(default_factory=dict)
    threat_marshall: dict[str, Any] = Field(default_factory=dict)
    platform_auditor: dict[str, Any] = Field(default_factory=dict)


class RemediationOption(BaseModel):
    """Embedded remediation option within the incident package."""
    priority: int = Field(..., ge=1, le=3)
    action: str = Field(...)
    rationale: str = Field(default="")
    risk_level: str = Field(default="MEDIUM")
    estimated_recovery_minutes: int = Field(default=5)
    requires_approval: bool = Field(default=True)
    mcp_tool_call: Optional[dict[str, Any]] = Field(default=None)


def generate_incident_id() -> str:
    """Generate a unique incident ID in TRIDENT format."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:8]
    return f"TRIDENT-{date_str}-{short_uuid}"


class IncidentPackage(BaseModel):
    """
    The complete incident package synthesised by AWS Bedrock.

    This is the JSON that gets:
    1. Written to Splunk index 'trident_incidents'
    2. Displayed in the TRIDENT dashboard
    3. Used by the analyst for one-click remediation

    Every field maps to a section in the dashboard UI.
    """
    # ─── Identity ────────────────────────────────────────────────────
    incident_id: str = Field(
        default_factory=generate_incident_id,
        description="Unique incident identifier",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO8601 creation timestamp",
    )
    status: IncidentStatus = Field(
        default=IncidentStatus.OPEN,
        description="Current lifecycle status",
    )

    # ─── Severity ────────────────────────────────────────────────────
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Incident severity classification",
    )
    severity_score: int = Field(
        default=50, ge=0, le=100,
        description="Numeric severity score for sorting",
    )

    # ─── Summary ─────────────────────────────────────────────────────
    title: str = Field(
        default="Untitled Incident",
        description="One-sentence incident title",
    )
    executive_summary: str = Field(
        default="",
        description="2-3 sentences, non-technical, for VP/CTO",
    )
    technical_summary: str = Field(
        default="",
        description="Detailed technical root cause paragraph",
    )

    # ─── Root Cause ──────────────────────────────────────────────────
    root_cause: str = Field(
        default="",
        description="Single most likely root cause",
    )
    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Additional contributing factors",
    )

    # ─── Attack Intelligence ─────────────────────────────────────────
    attack_timeline: list[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological attack events",
    )
    mitre_techniques: list[MitreTechnique] = Field(
        default_factory=list,
        description="Mapped MITRE ATT&CK techniques",
    )
    iocs: IOCs = Field(
        default_factory=IOCs,
        description="Indicators of Compromise",
    )

    # ─── Impact Assessment ───────────────────────────────────────────
    affected_services: list[str] = Field(
        default_factory=list,
        description="List of affected microservices/systems",
    )
    blast_radius: str = Field(
        default="",
        description="Estimated scope of impact",
    )
    business_impact: str = Field(
        default="",
        description="Dollar estimate of loss per hour",
    )

    # ─── Remediation ─────────────────────────────────────────────────
    remediation_options: list[RemediationOption] = Field(
        default_factory=list,
        description="3 prioritised remediation options",
    )

    # ─── Confidence & Trace ──────────────────────────────────────────
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall confidence in the incident analysis",
    )
    agent_trace: AgentTrace = Field(
        default_factory=AgentTrace,
        description="Raw outputs from each agent for transparency",
    )

    def to_splunk_event(self) -> dict[str, Any]:
        """
        Convert the incident package to a Splunk-ingestible event dict.

        Returns:
            Dict suitable for POSTing to /services/receivers/simple.
        """
        return self.model_dump(mode="json")
