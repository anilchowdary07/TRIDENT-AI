"""
TRIDENT-AI Agent Finding Models.

Pydantic v2 models for the output of each autonomous agent.
These typed models enforce data quality at agent boundaries.

Usage:
    from src.models.agent_finding import TelemetryFinding, ThreatFinding, PlatformFinding
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an agent's investigation."""
    IDLE = "IDLE"
    POLLING = "POLLING"
    TRIGGERED = "TRIGGERED"
    INVESTIGATING = "INVESTIGATING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    NO_THREAT = "NO_THREAT"


class ThreatType(str, Enum):
    """Types of threats detected by Foundation AI."""
    BRUTE_FORCE = "BruteForce"
    EXFILTRATION = "Exfiltration"
    INJECTION = "Injection"
    RECONNAISSANCE = "Reconnaissance"
    PRIVILEGE_ESCALATION = "PrivilegeEscalation"
    NONE = "None"


class AgentFinding(BaseModel):
    """Base model for all agent findings."""
    agent_name: str = Field(..., description="Name of the reporting agent")
    status: AgentStatus = Field(..., description="Agent status after investigation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When finding was produced")
    duration_seconds: float = Field(default=0.0, description="How long the investigation took")
    error_message: Optional[str] = Field(default=None, description="Error details if status=ERROR")
    raw_data: Optional[dict[str, Any]] = Field(default=None, description="Raw unprocessed data")


class TelemetryFinding(AgentFinding):
    """
    Output from the Telemetry Sentinel agent (CDTSM forecasting).

    Contains the forecast results, quantile band data, and anomaly detection.
    """
    agent_name: str = "TelemetrySentinel"
    metric_name: str = Field(default="", description="Name of the anomalous metric")
    anomaly_detected: bool = Field(default=False, description="Whether anomaly was found")
    anomaly_severity: float = Field(
        default=0.0, ge=0.0,
        description="How far outside the quantile band (0 = within band)",
    )
    anomaly_timestamp: Optional[str] = Field(
        default=None,
        description="ISO timestamp of the peak anomaly",
    )
    forecast_band: dict[str, list[float]] = Field(
        default_factory=lambda: {"lower": [], "upper": []},
        description="Q20 and Q80 quantile bands",
    )
    actual_vs_forecast: dict[str, list[float]] = Field(
        default_factory=lambda: {"actual": [], "forecast": []},
        description="Actual vs predicted values",
    )
    forecast_k: int = Field(default=24, description="Number of forecast steps")
    holdback: int = Field(default=12, description="Number of holdback steps")


class ThreatFinding(AgentFinding):
    """
    Output from the Threat Marshall agent (Foundation AI Security Model).

    Contains threat classification, MITRE ATT&CK mapping, IoCs, and narrative.
    """
    agent_name: str = "ThreatMarshall"
    threat_type: ThreatType = Field(
        default=ThreatType.NONE,
        description="Classified threat type",
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model confidence in the threat classification",
    )
    attack_timeline: list[dict[str, str]] = Field(
        default_factory=list,
        description="Timestamped sequence of attack events",
    )
    ioc_list: list[str] = Field(
        default_factory=list,
        description="IPs, domains, user agents flagged as malicious",
    )
    mitre_techniques: list[str] = Field(
        default_factory=list,
        description="MITRE ATT&CK T-codes detected",
    )
    affected_users: list[str] = Field(
        default_factory=list,
        description="Usernames targeted in the attack",
    )
    narrative: str = Field(
        default="",
        description="Human-readable investigation summary",
    )


class HeavySearch(BaseModel):
    """A CPU-hungry search detected by Platform Auditor."""
    title: str = ""
    owner: str = ""
    run_duration: float = 0.0
    cpu_estimate: float = 0.0


class ConfigChange(BaseModel):
    """A configuration change detected by Platform Auditor."""
    host: str = ""
    file: str = ""
    action: str = ""
    user: str = ""
    count: int = 0


class QueueWarning(BaseModel):
    """An indexer queue warning detected by Platform Auditor."""
    queue_name: str = ""
    avg_fill_kb: float = 0.0


class PlatformFinding(AgentFinding):
    """
    Output from the Platform Auditor agent (SPL-only).

    Contains results from 3 platform health queries:
    heavy searches, config changes, and queue warnings.
    """
    agent_name: str = "PlatformAuditor"
    heavy_searches: list[HeavySearch] = Field(
        default_factory=list,
        description="CPU-hungry scheduled searches detected",
    )
    config_changes: list[ConfigChange] = Field(
        default_factory=list,
        description="Configuration file changes in last 60 minutes",
    )
    queue_warnings: list[QueueWarning] = Field(
        default_factory=list,
        description="Indexer queues with high fill rates",
    )
    platform_healthy: bool = Field(
        default=True,
        description="Overall platform health assessment",
    )
