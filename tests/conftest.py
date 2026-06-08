"""
TRIDENT-AI Test Configuration.

Shared fixtures, mocks, and configuration for all test modules.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def sample_metrics():
    """Load sample metric data for testing."""
    data_path = Path(__file__).parent.parent / "demo" / "sample_data" / "metrics.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {"metrics": []}


@pytest.fixture
def sample_security_logs():
    """Load sample security log data for testing."""
    data_path = Path(__file__).parent.parent / "demo" / "sample_data" / "security_logs.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {"logs": []}


@pytest.fixture
def sample_platform_data():
    """Load sample platform data for testing."""
    data_path = Path(__file__).parent.parent / "demo" / "sample_data" / "platform_data.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {"data": []}


@pytest.fixture
def mock_search_client():
    """Create a mock SearchClient for testing agents."""
    client = MagicMock()
    client.execute_search = AsyncMock(return_value=[])
    client.write_event = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_splunk_auth():
    """Create a mock SplunkAuth for testing."""
    auth = MagicMock()
    auth.get_auth_headers.return_value = {"Authorization": "Bearer test-token"}
    auth.validate_connection.return_value = True
    return auth


@pytest.fixture
def sample_incident_package():
    """Create a sample incident package dict for testing."""
    return {
        "incident_id": "TRIDENT-20260615-test0001",
        "timestamp": "2026-06-15T03:43:00Z",
        "severity": "CRITICAL",
        "severity_score": 92,
        "title": "Test incident: brute-force with latency anomaly",
        "executive_summary": "Test executive summary.",
        "technical_summary": "Test technical summary.",
        "root_cause": "Test root cause",
        "contributing_factors": ["factor1", "factor2"],
        "attack_timeline": [
            {"timestamp": "2026-06-15T03:31:00Z", "event": "Test event", "source": "telemetry"}
        ],
        "mitre_techniques": [
            {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}
        ],
        "iocs": {"ips": ["203.0.113.45"], "domains": [], "users": ["admin"]},
        "affected_services": ["payments-api", "auth-service"],
        "blast_radius": "3,240 transactions",
        "business_impact": "$180,000 / hour",
        "remediation_options": [
            {
                "priority": 1,
                "action": "Block IP 203.0.113.45",
                "rationale": "Stop the attack",
                "risk_level": "LOW",
                "estimated_recovery_minutes": 2,
                "requires_approval": True,
            }
        ],
        "confidence": 0.92,
        "agent_trace": {
            "telemetry_sentinel": {},
            "threat_marshall": {},
            "platform_auditor": {},
        },
    }
