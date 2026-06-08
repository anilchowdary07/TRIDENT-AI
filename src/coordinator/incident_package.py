"""
TRIDENT-AI Incident Package Builder.

The crown jewel. Takes findings from all 3 agents, synthesises them via
AWS Bedrock (Claude claude-sonnet-4-5), and writes the complete incident package
to the Splunk `trident_incidents` index.

Usage:
    from src.coordinator.incident_package import IncidentPackageBuilder
    builder = IncidentPackageBuilder(bedrock_client, search_client)
    package = await builder.build(telemetry, threat, platform)
"""

from __future__ import annotations

import json
from typing import Any

from src.coordinator.bedrock_client import BedrockClient
from src.models.agent_finding import (
    AgentFinding,
    PlatformFinding,
    TelemetryFinding,
    ThreatFinding,
)
from src.models.incident import IncidentPackage
from src.splunk.search_client import SearchClient
from src.utils.logger import get_logger

log = get_logger(__name__)


class IncidentPackageBuilder:
    """
    Builds complete incident packages from agent findings.

    Flow:
    1. Collects typed findings from all 3 agents
    2. Sends them to Bedrock for intelligent synthesis
    3. Validates the response with IncidentPackage pydantic model
    4. Writes the package to Splunk index 'trident_incidents'
    5. Returns the validated package for dashboard display
    """

    def __init__(
        self,
        bedrock_client: BedrockClient,
        search_client: SearchClient,
    ) -> None:
        """
        Initialize the package builder.

        Args:
            bedrock_client: BedrockClient for Claude synthesis.
            search_client: SearchClient for writing to Splunk.
        """
        self._bedrock = bedrock_client
        self._search = search_client

    async def build(
        self,
        telemetry_finding: TelemetryFinding | AgentFinding,
        threat_finding: ThreatFinding | AgentFinding,
        platform_finding: PlatformFinding | AgentFinding,
    ) -> IncidentPackage:
        """
        Build a complete incident package from all 3 agent findings.

        Args:
            telemetry_finding: Finding from Telemetry Sentinel (CDTSM).
            threat_finding: Finding from Threat Marshall (Foundation AI).
            platform_finding: Finding from Platform Auditor (SPL).

        Returns:
            Validated IncidentPackage ready for dashboard display.
        """
        log.info(
            "incident_package_building",
            telemetry_status=telemetry_finding.status.value,
            threat_status=threat_finding.status.value,
            platform_status=platform_finding.status.value,
        )

        # Prepare findings for Bedrock synthesis
        findings_dict = {
            "telemetry_sentinel": telemetry_finding.model_dump(mode="json"),
            "threat_marshall": threat_finding.model_dump(mode="json"),
            "platform_auditor": platform_finding.model_dump(mode="json"),
        }

        # Synthesize via Bedrock
        try:
            raw_package = await self._bedrock.synthesize_incident_package(findings_dict)
        except Exception as e:
            log.error("bedrock_synthesis_failed", error=str(e))
            # Build a fallback package from raw findings
            raw_package = self._build_fallback_package(
                telemetry_finding, threat_finding, platform_finding
            )

        # Validate with pydantic model
        package = self._validate_package(raw_package, findings_dict)

        # Write to Splunk
        await self._write_to_splunk(package)

        log.info(
            "incident_package_complete",
            incident_id=package.incident_id,
            severity=package.severity.value,
            severity_score=package.severity_score,
        )

        return package

    def _validate_package(
        self,
        raw: dict[str, Any],
        original_findings: dict[str, Any],
    ) -> IncidentPackage:
        """
        Validate and enrich the raw Bedrock output with pydantic.

        Ensures the agent_trace field contains the original raw findings
        for transparency and audit purposes.

        Args:
            raw: Raw dict from Bedrock synthesis.
            original_findings: Original agent findings for the trace.

        Returns:
            Validated IncidentPackage.
        """
        # Ensure agent_trace contains original findings
        if "agent_trace" not in raw:
            raw["agent_trace"] = {}
        raw["agent_trace"]["telemetry_sentinel"] = original_findings.get(
            "telemetry_sentinel", {}
        )
        raw["agent_trace"]["threat_marshall"] = original_findings.get(
            "threat_marshall", {}
        )
        raw["agent_trace"]["platform_auditor"] = original_findings.get(
            "platform_auditor", {}
        )

        try:
            package = IncidentPackage.model_validate(raw)
        except Exception as e:
            log.warning(
                "incident_package_validation_warning",
                error=str(e),
            )
            # Partial validation — set what we can
            package = IncidentPackage(
                title=raw.get("title", "Unvalidated Incident"),
                severity=raw.get("severity", "MEDIUM"),
                severity_score=raw.get("severity_score", 50),
                executive_summary=raw.get("executive_summary", ""),
                technical_summary=raw.get("technical_summary", ""),
                root_cause=raw.get("root_cause", ""),
                confidence=raw.get("confidence", 0.5),
            )

        return package

    def _build_fallback_package(
        self,
        telemetry: TelemetryFinding | AgentFinding,
        threat: ThreatFinding | AgentFinding,
        platform: PlatformFinding | AgentFinding,
    ) -> dict[str, Any]:
        """
        Build a fallback incident package when Bedrock is unavailable.

        Uses raw agent findings to construct a basic but complete package.

        Args:
            telemetry: Telemetry Sentinel finding.
            threat: Threat Marshall finding.
            platform: Platform Auditor finding.

        Returns:
            Dict matching the incident package schema.
        """
        log.info("building_fallback_package")

        # Determine severity from findings
        severity = "MEDIUM"
        severity_score = 50

        if isinstance(threat, ThreatFinding) and threat.confidence_score >= 0.7:
            severity = "CRITICAL" if threat.confidence_score >= 0.85 else "HIGH"
            severity_score = int(threat.confidence_score * 100)
        elif isinstance(telemetry, TelemetryFinding) and telemetry.anomaly_severity > 2.0:
            severity = "HIGH"
            severity_score = min(90, int(50 + telemetry.anomaly_severity * 10))

        title = "Autonomous Detection: "
        if isinstance(threat, ThreatFinding) and threat.threat_type.value != "None":
            title += f"{threat.threat_type.value} attack detected"
        elif isinstance(telemetry, TelemetryFinding) and telemetry.anomaly_detected:
            title += f"Anomaly in {telemetry.metric_name}"
        else:
            title += "Platform health anomaly"

        return {
            "severity": severity,
            "severity_score": severity_score,
            "title": title,
            "executive_summary": (
                f"TRIDENT-AI autonomous agents detected an incident requiring attention. "
                f"Severity: {severity}. Bedrock synthesis unavailable — using raw agent data."
            ),
            "technical_summary": "Fallback package built from raw agent findings.",
            "root_cause": "Automated analysis pending — review agent trace for details.",
            "contributing_factors": [],
            "attack_timeline": [],
            "mitre_techniques": [],
            "iocs": {"ips": [], "domains": [], "users": []},
            "affected_services": [],
            "blast_radius": "Unknown — manual assessment required",
            "business_impact": "Unknown — manual assessment required",
            "remediation_options": [
                {
                    "priority": 1,
                    "action": "Review agent findings and assess manually",
                    "rationale": "Automated synthesis unavailable",
                    "risk_level": "LOW",
                    "estimated_recovery_minutes": 15,
                    "requires_approval": True,
                },
            ],
            "confidence": 0.3,
        }

    async def _write_to_splunk(self, package: IncidentPackage) -> None:
        """
        Write the incident package to Splunk index 'trident_incidents'.

        Args:
            package: Validated IncidentPackage to write.
        """
        try:
            success = await self._search.write_event(
                event_data=package.to_splunk_event(),
                index="trident_incidents",
                sourcetype="trident:incident",
            )
            if success:
                log.info(
                    "incident_written_to_splunk",
                    incident_id=package.incident_id,
                    index="trident_incidents",
                )
            else:
                log.error(
                    "incident_write_failed",
                    incident_id=package.incident_id,
                )
        except Exception as e:
            log.error(
                "incident_write_error",
                incident_id=package.incident_id,
                error=str(e),
            )
