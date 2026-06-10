"""
TRIDENT-AI Autonomous Loop — THE CORE.

Runs forever as a background daemon thread. No human trigger. No manual start.
It wakes, polls, decides, acts.

Every POLL_INTERVAL_SECONDS (default: 60) it:
1. Calls CDTSM via Splunk for all configured metric streams
2. If any metric breaches [Q20, Q80] quantile band by ANOMALY_DEVIATION_THRESHOLD:
   a. Prevents re-triggering for ANOMALY_COOLDOWN_SECONDS
   b. Spawns concurrent investigation tasks for all 3 agents (asyncio.gather)
   c. Passes all agent findings to BedrockClient.synthesize_incident_package()
   d. Writes the complete IncidentPackage to Splunk index via search_client
   e. Logs the full agent trace for the audit trail
3. If no anomaly: logs heartbeat and sleeps

Key design decisions:
- threading.Thread(daemon=True) for the outer loop
- asyncio.run() inside the thread for async agent calls
- asyncio.gather() to run all 3 agents in parallel (not sequential)
- Exponential backoff for failed Splunk API calls
- Cooldown tracker prevents incident queue flooding
- ALL exceptions caught — one agent crash never kills the loop

Usage:
    from src.coordinator.autonomous_loop import AutonomousLoop
    loop = AutonomousLoop()
    loop.start()  # returns immediately, runs in background
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

from src.agents.platform_auditor import PlatformAuditor
from src.agents.telemetry_sentinel import TelemetrySentinel
from src.agents.threat_marshall import ThreatMarshall
from src.coordinator.bedrock_client import BedrockClient
from src.coordinator.incident_package import IncidentPackageBuilder
from src.coordinator.state_manager import StateManager
from src.models.agent_finding import TelemetryFinding
from src.splunk.search_client import SearchClient
from src.splunk.token_auth import SplunkAuth
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class AutonomousLoop:
    """
    The autonomous coordinator — runs continuously without human intervention.

    Polls CDTSM for anomalies, triggers parallel agent investigations,
    synthesises incident packages via Bedrock, and writes them to Splunk.
    """

    def __init__(self) -> None:
        """Initialize all components of the autonomous loop."""
        log.info("autonomous_loop_initializing")

        # ─── Splunk clients ──────────────────────────────────────────
        self._auth = SplunkAuth()
        self._search = SearchClient(self._auth)

        # ─── Agents ──────────────────────────────────────────────────
        self._telemetry = TelemetrySentinel(self._search)
        self._threat = ThreatMarshall(self._search)
        self._platform = PlatformAuditor(self._search)

        # ─── Coordinator components ──────────────────────────────────
        self._bedrock = BedrockClient()
        self._package_builder = IncidentPackageBuilder(self._bedrock, self._search)
        self._state = StateManager()

        # ─── Thread control ──────────────────────────────────────────
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._poll_event = threading.Event()
        self._running = False

        log.info(
            "autonomous_loop_initialized",
            poll_interval=settings.POLL_INTERVAL_SECONDS,
            cooldown=settings.ANOMALY_COOLDOWN_SECONDS,
            threshold=settings.ANOMALY_DEVIATION_THRESHOLD,
            demo_mode=settings.DEMO_MODE,
        )

    def start(self) -> None:
        """
        Start the autonomous loop in a daemon background thread.

        Returns immediately — the loop runs in the background.
        """
        if self._running:
            log.warning("autonomous_loop_already_running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="trident-autonomous-loop",
            daemon=True,
        )
        self._thread.start()
        self._running = True

        log.info(
            "autonomous_loop_started",
            thread_name=self._thread.name,
            daemon=True,
        )

    def stop(self) -> None:
        """Signal the loop to stop gracefully."""
        log.info("autonomous_loop_stopping")
        self._stop_event.set()
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        log.info("autonomous_loop_stopped")

    @property
    def is_running(self) -> bool:
        """Check if the loop is currently running."""
        return self._running and self._thread is not None and self._thread.is_alive()

    def trigger_immediate_poll(self) -> None:
        """Interrupt sleep to force an immediate poll cycle."""
        self._poll_event.set()

    @property
    def state(self) -> StateManager:
        """Access the state manager for dashboard queries."""
        return self._state

    def _run_loop(self) -> None:
        """
        Main loop body — runs inside the daemon thread.

        Uses asyncio.run() for each poll cycle to handle async agent calls.
        """
        log.info("autonomous_loop_thread_started")

        consecutive_errors = 0
        max_consecutive_errors = 10

        while not self._stop_event.is_set():
            poll_num = self._state.increment_poll()

            try:
                log.info(
                    "poll_cycle_start",
                    poll_number=poll_num,
                    active_incidents=len(self._state.get_active_incidents()),
                )

                # Run the async poll cycle
                asyncio.run(self._poll_cycle(poll_num))
                consecutive_errors = 0  # Reset on success

            except Exception as e:
                consecutive_errors += 1
                log.error(
                    "poll_cycle_error",
                    poll_number=poll_num,
                    error=str(e),
                    error_type=type(e).__name__,
                    consecutive_errors=consecutive_errors,
                )

                if consecutive_errors >= max_consecutive_errors:
                    log.critical(
                        "autonomous_loop_too_many_errors",
                        consecutive_errors=consecutive_errors,
                    )
                    # Back off significantly but don't die
                    self._stop_event.wait(timeout=settings.POLL_INTERVAL_SECONDS * 5)
                    consecutive_errors = 0
                    continue

            # Clean up expired cooldowns periodically
            if poll_num % 10 == 0:
                self._state.clear_expired_cooldowns()

            # Sleep until next poll (interruptible)
            log.info(
                "poll_cycle_sleeping",
                poll_number=poll_num,
                sleep_seconds=settings.POLL_INTERVAL_SECONDS,
            )
            # Use poll_event to allow early waking, but stop if stop_event is set
            self._poll_event.wait(timeout=settings.POLL_INTERVAL_SECONDS)
            self._poll_event.clear()

        log.info("autonomous_loop_thread_exiting")

    async def _poll_cycle(self, poll_num: int) -> None:
        """
        Execute one poll cycle.

        1. Run Telemetry Sentinel to check for anomalies
        2. If anomaly found and not in cooldown: run all 3 agents in parallel
        3. Build and store incident package

        Args:
            poll_num: Current poll cycle number.
        """
        # ─── Step 1: CDTSM anomaly check ────────────────────────────
        context = {"demo_scenario_active": getattr(self._state, "demo_scenario_active", False)}
        telemetry_finding = await self._telemetry.investigate(context)
        self._state.update_agent_heartbeat(self._telemetry.get_heartbeat())

        if not isinstance(telemetry_finding, TelemetryFinding):
            log.info("poll_no_anomaly", poll_number=poll_num, reason="non_telemetry_finding")
            return

        if not telemetry_finding.anomaly_detected:
            log.info(
                "poll_no_anomaly",
                poll_number=poll_num,
                metric=telemetry_finding.metric_name,
            )
            return

        # ─── Step 2: Check cooldown ─────────────────────────────────
        metric_name = telemetry_finding.metric_name or "unknown"
        if not self._state.can_trigger(metric_name):
            log.info(
                "poll_anomaly_in_cooldown",
                poll_number=poll_num,
                metric=metric_name,
            )
            return

        # Record the trigger
        self._state.record_trigger(metric_name)

        log.info(
            "anomaly_detected_investigating",
            poll_number=poll_num,
            metric=metric_name,
            severity=telemetry_finding.anomaly_severity,
        )

        # ─── Step 3: Parallel agent investigation ───────────────────
        investigation_context = {
            "metric_name": metric_name,
            "anomaly_severity": telemetry_finding.anomaly_severity,
            "anomaly_timestamp": telemetry_finding.anomaly_timestamp,
            "poll_number": poll_num,
        }

        # Run Threat Marshall and Platform Auditor in parallel
        # (Telemetry Sentinel already ran above)
        threat_finding, platform_finding = await asyncio.gather(
            self._threat.investigate(investigation_context),
            self._platform.investigate(investigation_context),
            return_exceptions=False,
        )

        # Update heartbeats
        self._state.update_agent_heartbeat(self._threat.get_heartbeat())
        self._state.update_agent_heartbeat(self._platform.get_heartbeat())

        log.info(
            "all_agents_complete",
            poll_number=poll_num,
            telemetry_status=telemetry_finding.status.value,
            threat_status=threat_finding.status.value,
            platform_status=platform_finding.status.value,
        )

        # ─── Step 4: Build incident package via Bedrock ─────────────
        try:
            package = await self._package_builder.build(
                telemetry_finding=telemetry_finding,
                threat_finding=threat_finding,
                platform_finding=platform_finding,
            )

            # Add to state tracker
            self._state.add_incident(package)

            await self._search.post_event(
                index="trident_incidents",
                event=package.model_dump(mode="json") if hasattr(package, 'model_dump') else package.dict(),
                sourcetype="trident:incident"
            )

            log.info(
                "incident_package_created",
                poll_number=poll_num,
                incident_id=package.incident_id,
                severity=package.severity.value,
                severity_score=package.severity_score,
                title=package.title,
            )

        except Exception as e:
            log.error(
                "incident_package_build_failed",
                poll_number=poll_num,
                error=str(e),
            )
