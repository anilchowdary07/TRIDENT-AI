"""Tests for the autonomous loop coordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.coordinator.state_manager import StateManager


class TestStateManager:
    """Test the state manager cooldown and queue logic."""

    def test_can_trigger_initially(self):
        """First trigger should always be allowed."""
        state = StateManager()
        assert state.can_trigger("test.metric") is True

    def test_cooldown_blocks_retrigger(self):
        """After triggering, same metric should be blocked during cooldown."""
        state = StateManager()
        state.record_trigger("test.metric")
        assert state.can_trigger("test.metric") is False

    def test_different_metrics_independent(self):
        """Different metrics should have independent cooldowns."""
        state = StateManager()
        state.record_trigger("metric.a")
        assert state.can_trigger("metric.b") is True

    def test_queue_capacity(self):
        """Should block triggers when queue is full."""
        state = StateManager()
        # Fill the queue with mock incidents
        for i in range(100):
            mock_incident = MagicMock()
            mock_incident.incident_id = f"TRIDENT-{i:04d}"
            mock_incident.severity_score = 50
            state.add_incident(mock_incident)
        assert state.can_trigger("new.metric") is False

    def test_resolve_incident(self):
        """Should remove resolved incidents from active queue."""
        state = StateManager()
        mock_incident = MagicMock()
        mock_incident.incident_id = "TRIDENT-0001"
        mock_incident.severity_score = 80
        state.add_incident(mock_incident)
        assert len(state.get_active_incidents()) == 1
        state.resolve_incident("TRIDENT-0001")
        assert len(state.get_active_incidents()) == 0

    def test_stats(self):
        """Should return correct statistics."""
        state = StateManager()
        stats = state.get_stats()
        assert stats["poll_count"] == 0
        assert stats["active_incidents"] == 0
        state.increment_poll()
        assert state.get_stats()["poll_count"] == 1
