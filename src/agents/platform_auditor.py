"""
TRIDENT-AI Platform Auditor Agent.

Lightweight SPL-only agent — no AI model required.
Runs 3 SPL queries in parallel to detect:
  1. CPU-hungry scheduled searches consuming excessive resources
  2. Deployment/configuration changes in the last 60 minutes
  3. Indexer queue fill rate warnings

This is the simplest agent and should be built first to validate the
full agent → coordinator pipeline.

Usage:
    from src.agents.platform_auditor import PlatformAuditor
    auditor = PlatformAuditor(search_client)
    finding = await auditor.investigate()
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models.agent_finding import (
    AgentFinding,
    AgentStatus,
    ConfigChange,
    HeavySearch,
    PlatformFinding,
    QueueWarning,
)
from src.splunk.search_client import SearchClient
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# ─── SPL Queries ────────────────────────────────────────────────────────
SPL_HEAVY_SEARCHES = """
| rest /services/search/jobs
| where dispatchState="RUNNING" AND runDuration > 300
| eval cpu_estimate = (scanCount / 1000000) * 2.3
| where cpu_estimate > 80
| table title, owner, runDuration, cpu_estimate
"""

SPL_CONFIG_CHANGES = """
search index=_internal sourcetype=splunkd
earliest=-60m
(props.conf OR transforms.conf OR inputs.conf OR outputs.conf)
| stats count by host, file, action, user
| where count > 0
"""

SPL_QUEUE_WARNINGS = """
search index=_internal sourcetype=metrics group=queue
earliest=-5m
| stats avg(current_size_kb) as avg_fill by name
| where avg_fill > 5000
"""


class PlatformAuditor(BaseAgent):
    """
    Platform health monitoring agent using pure SPL queries.

    Detects resource-hogging searches, configuration changes, and
    indexer queue congestion — all without requiring any AI model.
    """

    def __init__(self, search_client: SearchClient) -> None:
        """
        Initialize the Platform Auditor.

        Args:
            search_client: SearchClient for executing SPL queries.
        """
        super().__init__("PlatformAuditor")
        self._search = search_client

    async def _investigate(self, context: dict[str, Any]) -> PlatformFinding:
        """
        Run all 3 platform health queries in parallel.

        Args:
            context: Investigation context (not used by this agent).

        Returns:
            PlatformFinding with heavy searches, config changes, and queue warnings.
        """
        # Add a realistic delay to show the agent "working" in the UI
        await asyncio.sleep(2.5)

        log.info("platform_auditor_starting", demo_mode=settings.DEMO_MODE)
        
        if settings.DEMO_MODE:
            log.info("platform_auditor_demo_mode", path="demo/sample_data/platform_data.json")
            file_path = os.path.join("demo", "sample_data", "platform_data.json")
            try:
                with open(file_path, "r") as f:
                    mock_data = json.load(f)
                
                heavy_searches = [HeavySearch(**hs) for hs in mock_data.get("heavy_searches", [])]
                config_changes = [ConfigChange(**cc) for cc in mock_data.get("config_changes", [])]
                queue_warnings = [QueueWarning(**qw) for qw in mock_data.get("queue_warnings", [])]
            except Exception as e:
                log.error("Failed to load local platform mock data", error=str(e))
                heavy_searches = []
                config_changes = []
                queue_warnings = []
        else:
            # Run all 3 queries concurrently
            results = await asyncio.gather(
                self._check_heavy_searches(),
                self._check_config_changes(),
                self._check_queue_fill(),
                return_exceptions=True,
            )

            heavy_searches = results[0] if not isinstance(results[0], Exception) else []
            config_changes = results[1] if not isinstance(results[1], Exception) else []
            queue_warnings = results[2] if not isinstance(results[2], Exception) else []

            # Log any errors from individual queries
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    query_names = ["heavy_searches", "config_changes", "queue_fill"]
                    log.warning(
                        "platform_query_failed",
                        query=query_names[i],
                        error=str(result),
                    )

        # Determine overall platform health
        platform_healthy = (
            len(heavy_searches) == 0
            and len(queue_warnings) == 0
        )

        finding = PlatformFinding(
            status=AgentStatus.COMPLETE,
            heavy_searches=heavy_searches,
            config_changes=config_changes,
            queue_warnings=queue_warnings,
            platform_healthy=platform_healthy,
            raw_data={
                "heavy_search_count": len(heavy_searches),
                "config_change_count": len(config_changes),
                "queue_warning_count": len(queue_warnings),
            },
        )

        log.info(
            "platform_auditor_complete",
            heavy_searches=len(heavy_searches),
            config_changes=len(config_changes),
            queue_warnings=len(queue_warnings),
            platform_healthy=platform_healthy,
        )

        return finding

    async def _check_heavy_searches(self) -> list[HeavySearch]:
        """
        Query for CPU-hungry scheduled searches.

        Returns:
            List of HeavySearch objects for searches with estimated CPU > 80%.
        """
        results = await self._search.execute_search(
            SPL_HEAVY_SEARCHES,
            earliest_time="-5m",
        )

        searches = []
        for row in results:
            searches.append(HeavySearch(
                title=row.get("title", "Unknown"),
                owner=row.get("owner", "Unknown"),
                run_duration=float(row.get("runDuration", 0)),
                cpu_estimate=float(row.get("cpu_estimate", 0)),
            ))

        return searches

    async def _check_config_changes(self) -> list[ConfigChange]:
        """
        Query for configuration file changes in the last 60 minutes.

        Returns:
            List of ConfigChange objects.
        """
        results = await self._search.execute_search(
            SPL_CONFIG_CHANGES,
            earliest_time="-60m",
        )

        changes = []
        for row in results:
            changes.append(ConfigChange(
                host=row.get("host", ""),
                file=row.get("file", ""),
                action=row.get("action", ""),
                user=row.get("user", ""),
                count=int(row.get("count", 0)),
            ))

        return changes

    async def _check_queue_fill(self) -> list[QueueWarning]:
        """
        Query for indexer queues with high fill rates.

        Returns:
            List of QueueWarning objects for queues above 5000 KB.
        """
        results = await self._search.execute_search(
            SPL_QUEUE_WARNINGS,
            earliest_time="-5m",
        )

        warnings = []
        for row in results:
            warnings.append(QueueWarning(
                queue_name=row.get("name", ""),
                avg_fill_kb=float(row.get("avg_fill", 0)),
            ))

        return warnings
