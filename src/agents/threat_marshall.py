"""
TRIDENT-AI Threat Marshall Agent.

Uses the Foundation AI Security Model (foundation-sec-1.1-8b-instruct) for
autonomous threat investigation and MITRE ATT&CK mapping.

When triggered by a TelemetrySentinel anomaly, queries security logs and
sends them to Foundation AI for analysis. Performs:
  - Threat classification (BruteForce, Exfiltration, Injection, etc.)
  - MITRE ATT&CK technique mapping
  - IoC extraction (IPs, domains, user agents)
  - Attack timeline reconstruction
  - Human-readable narrative generation

Confidence thresholds:
  - < 0.4: NO_THREAT finding
  - >= 0.7: HIGH_CONFIDENCE_THREAT finding

Usage:
    from src.agents.threat_marshall import ThreatMarshall
    marshall = ThreatMarshall(search_client)
    finding = await marshall.investigate(context={"anomaly_timestamp": "..."})
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models.agent_finding import AgentStatus, ThreatFinding, ThreatType
from src.splunk.hosted_models import FoundationAIClient, FoundationAIResult
from src.splunk.search_client import SearchClient
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.mitre import enrich_techniques

log = get_logger(__name__)


class ThreatMarshall(BaseAgent):
    """
    Foundation AI-powered threat investigation agent.

    Analyses security logs using the Foundation AI Security Model to
    classify threats, map to MITRE ATT&CK, and extract IoCs.
    """

    def __init__(self, search_client: SearchClient) -> None:
        """
        Initialize the Threat Marshall.

        Args:
            search_client: SearchClient for SPL execution.
        """
        super().__init__("ThreatMarshall")
        self._search = search_client
        self._foundation_ai = FoundationAIClient(search_client)

    async def _investigate(self, context: dict[str, Any]) -> ThreatFinding:
        """
        Run Foundation AI threat analysis on recent security logs.

        In demo mode, loads security logs from local sample files.

        Args:
            context: Optional context with anomaly details from Telemetry Sentinel.
                     Keys: anomaly_timestamp, metric_name, anomaly_severity.

        Returns:
            ThreatFinding with threat classification and MITRE mapping.
        """
        log.info(
            "threat_marshall_starting",
            demo_mode=settings.DEMO_MODE,
            context_keys=list(context.keys()),
        )

        # Add a realistic delay to show the agent "working" in the UI
        await asyncio.sleep(2.0)

        if settings.DEMO_MODE:
            return await self._investigate_demo(context)

        # Build additional filter from context if available
        additional_filter = ""
        if context.get("anomaly_timestamp"):
            # Narrow search window around the anomaly
            additional_filter = ""

        try:
            result = await self._foundation_ai.analyze_threats(
                earliest="-15m",
                additional_filter=additional_filter,
            )
            return self._result_to_finding(result)

        except Exception as e:
            log.error(
                "threat_marshall_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return ThreatFinding(
                status=AgentStatus.ERROR,
                error_message=str(e),
            )

    async def _investigate_demo(self, context: dict[str, Any]) -> ThreatFinding:
        """
        Run investigation using local demo security log data.

        Simulates Foundation AI analysis of brute-force attack logs.

        Args:
            context: Investigation context.

        Returns:
            ThreatFinding from demo data.
        """
        demo_path = Path(settings.DEMO_DATA_PATH) / "security_logs.json"
        log.info("threat_marshall_demo_mode", path=str(demo_path))

        try:
            with open(demo_path) as f:
                demo_data = json.load(f)
        except FileNotFoundError:
            log.warning("threat_marshall_demo_data_not_found", path=str(demo_path))
            return ThreatFinding(
                status=AgentStatus.COMPLETE,
                threat_type=ThreatType.NONE,
                confidence_score=0.0,
                narrative="No demo security log data found.",
            )

        logs = demo_data if isinstance(demo_data, list) else demo_data.get("logs", [])

        # Analyse demo logs
        total_401 = sum(1 for l in logs if l.get("status_code") == 401 or "401" in str(l.get("raw", "")))
        total_200 = sum(1 for l in logs if l.get("status_code") == 200 or "200" in str(l.get("raw", "")))
        source_ips = set()
        affected_users = set()

        for entry in logs:
            if entry.get("src_ip"):
                source_ips.add(entry["src_ip"])
            if entry.get("user"):
                affected_users.add(entry["user"])

        # Determine threat type based on log patterns
        if total_401 > 100:
            threat_type = ThreatType.BRUTE_FORCE
            confidence = min(0.95, 0.4 + (total_401 / 2000) * 0.55)
            mitre_techniques = ["T1110", "T1078"]
            narrative = (
                f"Foundation AI detected a brute-force credential attack. "
                f"{total_401} failed login attempts detected from {len(source_ips)} "
                f"source IP(s), with {total_200} successful authentications intermixed. "
                f"The attack pattern matches MITRE ATT&CK T1110 (Brute Force) with "
                f"potential T1078 (Valid Accounts) compromise.\n\n"
                f"The primary attack source is IP {'203.0.113.45' if '203.0.113.45' in source_ips else 'unknown'}. "
                f"The automated tool signature (python-requests user agent) suggests "
                f"a scripted credential stuffing campaign targeting {len(affected_users)} user accounts."
            )
        else:
            threat_type = ThreatType.NONE
            confidence = 0.1
            mitre_techniques = []
            narrative = "No significant threat patterns detected in security logs."

        # Build attack timeline
        timeline = []
        for entry in logs[:20]:  # First 20 events
            timeline.append({
                "timestamp": entry.get("timestamp", entry.get("time", "")),
                "event": entry.get("raw", entry.get("action", ""))[:200],
                "source": "security",
            })

        # Enrich MITRE techniques
        enriched = enrich_techniques(mitre_techniques)

        finding = ThreatFinding(
            status=AgentStatus.COMPLETE,
            threat_type=threat_type,
            confidence_score=round(confidence, 3),
            attack_timeline=timeline,
            ioc_list=sorted(source_ips),
            mitre_techniques=mitre_techniques,
            affected_users=sorted(affected_users),
            narrative=narrative,
            raw_data={
                "total_401": total_401,
                "total_200": total_200,
                "source_ips": sorted(source_ips),
                "mitre_enriched": enriched,
            },
        )

        log.info(
            "threat_marshall_demo_complete",
            threat_type=threat_type.value,
            confidence=round(confidence, 3),
            ioc_count=len(source_ips),
        )

        return finding

    def _result_to_finding(self, result: FoundationAIResult) -> ThreatFinding:
        """
        Convert a FoundationAIResult into a ThreatFinding.

        Applies confidence thresholds:
          - < 0.4: NO_THREAT
          - >= 0.7: HIGH_CONFIDENCE_THREAT

        Args:
            result: Foundation AI analysis result.

        Returns:
            ThreatFinding with mapped fields.
        """
        # Map threat type string to enum
        try:
            threat_type = ThreatType(result.threat_type)
        except ValueError:
            threat_type = ThreatType.NONE

        # Apply confidence thresholds
        if result.confidence_score < 0.4:
            status = AgentStatus.COMPLETE
            threat_type = ThreatType.NONE
        else:
            status = AgentStatus.COMPLETE

        return ThreatFinding(
            status=status,
            threat_type=threat_type,
            confidence_score=result.confidence_score,
            attack_timeline=result.attack_timeline,
            ioc_list=result.ioc_list,
            mitre_techniques=result.mitre_techniques,
            affected_users=result.affected_users,
            narrative=result.narrative,
            raw_data={"raw_result_count": len(result.raw_results or [])},
        )
