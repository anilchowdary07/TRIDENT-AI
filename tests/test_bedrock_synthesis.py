"""Tests for the Bedrock client synthesis."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.coordinator.bedrock_client import BedrockClient


class TestBedrockResponseParsing:
    """Test response parsing and JSON extraction."""

    def test_parse_clean_json(self):
        """Should parse clean JSON responses."""
        client = BedrockClient.__new__(BedrockClient)
        response = '{"severity": "HIGH", "title": "Test incident"}'
        result = client._parse_response(response)
        assert result["severity"] == "HIGH"

    def test_parse_json_with_markdown(self):
        """Should strip markdown code blocks from response."""
        client = BedrockClient.__new__(BedrockClient)
        response = '```json\n{"severity": "CRITICAL"}\n```'
        result = client._parse_response(response)
        assert result["severity"] == "CRITICAL"

    def test_parse_json_with_whitespace(self):
        """Should handle leading/trailing whitespace."""
        client = BedrockClient.__new__(BedrockClient)
        response = '\n  {"title": "test"}  \n'
        result = client._parse_response(response)
        assert result["title"] == "test"

    def test_parse_invalid_json_raises(self):
        """Should raise JSONDecodeError on invalid JSON."""
        client = BedrockClient.__new__(BedrockClient)
        with pytest.raises(json.JSONDecodeError):
            client._parse_response("this is not json at all")

    def test_build_user_prompt(self):
        """Should include all agent findings in the prompt."""
        client = BedrockClient.__new__(BedrockClient)
        findings = {
            "telemetry_sentinel": {"anomaly_detected": True},
            "threat_marshall": {"threat_type": "BruteForce"},
            "platform_auditor": {"platform_healthy": False},
        }
        prompt = client._build_user_prompt(findings)
        assert "TELEMETRY SENTINEL" in prompt
        assert "THREAT MARSHALL" in prompt
        assert "PLATFORM AUDITOR" in prompt
        assert "BruteForce" in prompt
