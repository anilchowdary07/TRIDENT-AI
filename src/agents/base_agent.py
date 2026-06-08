"""
TRIDENT-AI Base Agent — Abstract Base Class.

All three TRIDENT agents inherit from this class. It provides:
  - Standardised logging and timing
  - Error handling that never crashes the caller
  - Consistent AgentFinding output format
  - Status lifecycle management

Usage:
    class MyAgent(BaseAgent):
        async def _investigate(self, context: dict) -> AgentFinding:
            ...
"""

from __future__ import annotations

import abc
import time
from typing import Any

from src.models.agent_finding import AgentFinding, AgentStatus
from src.utils.logger import get_logger

log = get_logger(__name__)


class BaseAgent(abc.ABC):
    """
    Abstract base class for all TRIDENT autonomous agents.

    Provides the investigate() public method which wraps the subclass
    _investigate() implementation with timing, logging, and error handling.
    A crash in one agent must NEVER kill the autonomous loop.
    """

    def __init__(self, agent_name: str) -> None:
        """
        Initialize the base agent.

        Args:
            agent_name: Human-readable name for logging (e.g., "TelemetrySentinel").
        """
        self.agent_name = agent_name
        self._status = AgentStatus.IDLE
        self._last_poll_time: float | None = None
        self._last_anomaly_time: float | None = None
        log.info("agent_initialized", agent=self.agent_name)

    @property
    def status(self) -> AgentStatus:
        """Current agent status."""
        return self._status

    @status.setter
    def status(self, value: AgentStatus) -> None:
        """Update agent status with logging."""
        old = self._status
        self._status = value
        log.info(
            "agent_status_change",
            agent=self.agent_name,
            old_status=old.value,
            new_status=value.value,
        )

    async def investigate(self, context: dict[str, Any] | None = None) -> AgentFinding:
        """
        Run the agent's investigation with full error handling.

        This is the public entry point. It wraps _investigate() with:
        - Status lifecycle management
        - Timing measurement
        - Exception handling (errors produce ERROR findings, never crash)
        - Structured logging at every step

        Args:
            context: Optional dict of contextual data for the investigation.

        Returns:
            AgentFinding (or subclass) with investigation results.
            On error, returns a finding with status=ERROR and error_message set.
        """
        start_time = time.time()
        self.status = AgentStatus.INVESTIGATING
        self._last_poll_time = start_time

        log.info(
            "agent_investigation_start",
            agent=self.agent_name,
            context_keys=list((context or {}).keys()),
        )

        try:
            finding = await self._investigate(context or {})
            elapsed = time.time() - start_time
            finding.duration_seconds = round(elapsed, 3)

            if finding.status == AgentStatus.ERROR:
                self.status = AgentStatus.ERROR
            else:
                self.status = AgentStatus.COMPLETE
                # Track last anomaly time for status display
                if hasattr(finding, "anomaly_detected") and finding.anomaly_detected:
                    self._last_anomaly_time = time.time()

            log.info(
                "agent_investigation_complete",
                agent=self.agent_name,
                status=finding.status.value,
                duration=finding.duration_seconds,
            )
            return finding

        except Exception as e:
            elapsed = time.time() - start_time
            self.status = AgentStatus.ERROR

            log.error(
                "agent_investigation_error",
                agent=self.agent_name,
                error=str(e),
                error_type=type(e).__name__,
                duration=round(elapsed, 3),
            )

            return AgentFinding(
                agent_name=self.agent_name,
                status=AgentStatus.ERROR,
                duration_seconds=round(elapsed, 3),
                error_message=f"{type(e).__name__}: {str(e)}",
            )

    @abc.abstractmethod
    async def _investigate(self, context: dict[str, Any]) -> AgentFinding:
        """
        Perform the actual investigation logic. Subclasses implement this.

        Args:
            context: Dict of contextual data (e.g., anomaly details from CDTSM).

        Returns:
            A typed AgentFinding subclass with investigation results.
        """
        ...

    def get_heartbeat(self) -> dict[str, Any]:
        """
        Get a heartbeat dict for the agent status dashboard.

        Returns:
            Dict with agent name, status, and timing information.
        """
        return {
            "agent_name": self.agent_name,
            "status": self._status.value,
            "last_poll_time": self._last_poll_time,
            "last_anomaly_time": self._last_anomaly_time,
        }
