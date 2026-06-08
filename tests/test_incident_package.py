"""Tests for the incident package builder and pydantic models."""

import pytest

from src.models.incident import IncidentPackage, Severity, generate_incident_id


class TestIncidentPackage:
    """Test the IncidentPackage pydantic model."""

    def test_create_from_dict(self, sample_incident_package):
        """Should create a valid IncidentPackage from a dict."""
        package = IncidentPackage.model_validate(sample_incident_package)
        assert package.incident_id == "TRIDENT-20260615-test0001"
        assert package.severity == Severity.CRITICAL
        assert package.severity_score == 92
        assert package.confidence == 0.92

    def test_incident_id_format(self):
        """Generated incident IDs should follow TRIDENT format."""
        iid = generate_incident_id()
        assert iid.startswith("TRIDENT-")
        parts = iid.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 8  # UUID[:8]

    def test_severity_score_validation(self):
        """Severity score should be clamped to 0-100."""
        package = IncidentPackage(severity_score=50)
        assert 0 <= package.severity_score <= 100

    def test_to_splunk_event(self, sample_incident_package):
        """Should convert to a Splunk-ingestible dict."""
        package = IncidentPackage.model_validate(sample_incident_package)
        event = package.to_splunk_event()
        assert isinstance(event, dict)
        assert "incident_id" in event
        assert "severity" in event

    def test_default_values(self):
        """Should have sensible defaults for all fields."""
        package = IncidentPackage()
        assert package.incident_id.startswith("TRIDENT-")
        assert package.severity == Severity.MEDIUM
        assert package.severity_score == 50
        assert package.status.value == "OPEN"
