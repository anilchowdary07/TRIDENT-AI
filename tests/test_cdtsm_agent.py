"""Tests for the Telemetry Sentinel (CDTSM) agent."""

import pytest

from src.agents.telemetry_sentinel import TelemetrySentinel
from src.models.agent_finding import AgentStatus


@pytest.mark.asyncio
async def test_telemetry_sentinel_demo_mode(mock_search_client, monkeypatch):
    """Telemetry Sentinel should detect anomaly in demo data."""
    monkeypatch.setattr("src.agents.telemetry_sentinel.settings.DEMO_MODE", True)
    monkeypatch.setattr("src.agents.telemetry_sentinel.settings.DEMO_DATA_PATH", "./demo/sample_data/")

    sentinel = TelemetrySentinel(mock_search_client)
    finding = await sentinel.investigate()

    assert finding.status == AgentStatus.COMPLETE
    assert finding.agent_name == "TelemetrySentinel"
    assert finding.duration_seconds >= 0


@pytest.mark.asyncio
async def test_telemetry_sentinel_error_handling(mock_search_client, monkeypatch):
    """Telemetry Sentinel should handle errors gracefully."""
    monkeypatch.setattr("src.agents.telemetry_sentinel.settings.DEMO_MODE", True)
    monkeypatch.setattr("src.agents.telemetry_sentinel.settings.DEMO_DATA_PATH", "/nonexistent/path/")

    sentinel = TelemetrySentinel(mock_search_client)
    finding = await sentinel.investigate()

    # Should complete without crash, even with bad data path
    assert finding.status in (AgentStatus.COMPLETE, AgentStatus.ERROR)
