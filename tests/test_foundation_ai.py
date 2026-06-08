"""Tests for the Threat Marshall (Foundation AI) agent."""

import pytest

from src.agents.threat_marshall import ThreatMarshall
from src.models.agent_finding import AgentStatus, ThreatType


@pytest.mark.asyncio
async def test_threat_marshall_demo_mode(mock_search_client, monkeypatch):
    """Threat Marshall should detect brute-force in demo data."""
    monkeypatch.setattr("src.agents.threat_marshall.settings.DEMO_MODE", True)
    monkeypatch.setattr("src.agents.threat_marshall.settings.DEMO_DATA_PATH", "./demo/sample_data/")

    marshall = ThreatMarshall(mock_search_client)
    finding = await marshall.investigate()

    assert finding.status == AgentStatus.COMPLETE
    assert finding.agent_name == "ThreatMarshall"
    # Should detect brute force in demo data
    assert finding.threat_type == ThreatType.BRUTE_FORCE
    assert finding.confidence_score > 0.4
    assert len(finding.ioc_list) > 0


@pytest.mark.asyncio
async def test_threat_marshall_no_demo_data(mock_search_client, monkeypatch):
    """Threat Marshall should handle missing demo data."""
    monkeypatch.setattr("src.agents.threat_marshall.settings.DEMO_MODE", True)
    monkeypatch.setattr("src.agents.threat_marshall.settings.DEMO_DATA_PATH", "/nonexistent/path/")

    marshall = ThreatMarshall(mock_search_client)
    finding = await marshall.investigate()

    assert finding.status == AgentStatus.COMPLETE
    assert finding.threat_type == ThreatType.NONE
