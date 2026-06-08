"""
TRIDENT-AI State Manager.

Tracks active incidents, anomaly cooldowns, and agent states.
Prevents the autonomous loop from flooding the incident queue
when the same anomaly is detected repeatedly.

Usage:
    from src.coordinator.state_manager import StateManager
    state = StateManager()
    if state.can_trigger("payments.latency_ms"):
        state.record_trigger("payments.latency_ms")
"""

from __future__ import annotations

import time
from typing import Any

from src.models.incident import IncidentPackage
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class StateManager:
    """
    Manages the autonomous loop's operational state.

    Responsibilities:
    - Cooldown tracking: prevents re-triggering on the same anomaly
    - Incident queue management: tracks active incidents
    - Agent heartbeat tracking: monitors agent health
    - Deduplication: prevents duplicate incidents for the same root cause
    """

    def __init__(self) -> None:
        """Initialize state manager with empty state."""
        # Cooldown tracker: metric_name → last_trigger_timestamp
        self._cooldowns: dict[str, float] = {}

        # Active incidents: incident_id → IncidentPackage
        self._active_incidents: dict[str, IncidentPackage] = {}

        # Agent heartbeats: agent_name → heartbeat dict
        self._agent_heartbeats: dict[str, dict[str, Any]] = {}

        # Poll counter
        self._poll_count: int = 0
        self._start_time: float = time.time()

        log.info(
            "state_manager_init",
            cooldown_seconds=settings.ANOMALY_COOLDOWN_SECONDS,
            max_incidents=settings.MAX_INCIDENTS_IN_QUEUE,
        )

    def can_trigger(self, metric_name: str) -> bool:
        """
        Check if a metric anomaly is allowed to trigger an investigation.

        Returns False if:
        - The metric is still in cooldown period
        - The incident queue is full

        Args:
            metric_name: The metric that detected an anomaly.

        Returns:
            True if investigation should proceed, False if in cooldown.
        """
        # Check queue capacity
        if len(self._active_incidents) >= settings.MAX_INCIDENTS_IN_QUEUE:
            log.warning(
                "trigger_blocked_queue_full",
                metric=metric_name,
                active_count=len(self._active_incidents),
                max=settings.MAX_INCIDENTS_IN_QUEUE,
            )
            return False

        # Check cooldown
        last_trigger = self._cooldowns.get(metric_name, 0)
        elapsed = time.time() - last_trigger

        if elapsed < settings.ANOMALY_COOLDOWN_SECONDS:
            remaining = settings.ANOMALY_COOLDOWN_SECONDS - elapsed
            log.info(
                "trigger_blocked_cooldown",
                metric=metric_name,
                remaining_seconds=round(remaining, 1),
            )
            return False

        return True

    def record_trigger(self, metric_name: str) -> None:
        """
        Record that an anomaly triggered an investigation.

        Starts the cooldown timer for this metric.

        Args:
            metric_name: The metric that triggered.
        """
        self._cooldowns[metric_name] = time.time()
        log.info(
            "trigger_recorded",
            metric=metric_name,
            cooldown_seconds=settings.ANOMALY_COOLDOWN_SECONDS,
        )

    def add_incident(self, package: IncidentPackage) -> None:
        """
        Add a new incident to the active queue.

        Args:
            package: The incident package to track.
        """
        self._active_incidents[package.incident_id] = package
        log.info(
            "incident_added",
            incident_id=package.incident_id,
            severity=package.severity.value,
            active_count=len(self._active_incidents),
        )

    def resolve_incident(self, incident_id: str) -> bool:
        """
        Mark an incident as resolved and remove from active queue.

        Args:
            incident_id: The incident ID to resolve.

        Returns:
            True if incident was found and resolved, False otherwise.
        """
        if incident_id in self._active_incidents:
            del self._active_incidents[incident_id]
            log.info(
                "incident_resolved",
                incident_id=incident_id,
                active_count=len(self._active_incidents),
            )
            return True
        return False

    def get_active_incidents(self) -> list[IncidentPackage]:
        """
        Get all active incidents, sorted by severity score descending.

        Returns:
            List of active IncidentPackage objects.
        """
        return sorted(
            self._active_incidents.values(),
            key=lambda x: x.severity_score,
            reverse=True,
        )

    def update_agent_heartbeat(self, heartbeat: dict[str, Any]) -> None:
        """
        Update the heartbeat for an agent.

        Args:
            heartbeat: Dict with agent_name, status, last_poll_time.
        """
        agent_name = heartbeat.get("agent_name", "unknown")
        self._agent_heartbeats[agent_name] = {
            **heartbeat,
            "updated_at": time.time(),
        }

    def get_agent_heartbeats(self) -> dict[str, dict[str, Any]]:
        """Get all agent heartbeats."""
        return dict(self._agent_heartbeats)

    def increment_poll(self) -> int:
        """
        Increment and return the poll counter.

        Returns:
            Current poll count.
        """
        self._poll_count += 1
        return self._poll_count

    def get_stats(self) -> dict[str, Any]:
        """
        Get overall state statistics for dashboard display.

        Returns:
            Dict with uptime, poll count, active incidents, etc.
        """
        uptime = time.time() - self._start_time
        return {
            "uptime_seconds": round(uptime, 1),
            "poll_count": self._poll_count,
            "active_incidents": len(self._active_incidents),
            "active_cooldowns": len([
                m for m, t in self._cooldowns.items()
                if time.time() - t < settings.ANOMALY_COOLDOWN_SECONDS
            ]),
            "agents_tracked": len(self._agent_heartbeats),
        }

    def clear_expired_cooldowns(self) -> int:
        """
        Remove expired cooldowns to free memory.

        Returns:
            Number of expired cooldowns cleared.
        """
        now = time.time()
        expired = [
            m for m, t in self._cooldowns.items()
            if now - t >= settings.ANOMALY_COOLDOWN_SECONDS * 2
        ]
        for m in expired:
            del self._cooldowns[m]

        if expired:
            log.debug("cooldowns_cleared", count=len(expired))

        return len(expired)
