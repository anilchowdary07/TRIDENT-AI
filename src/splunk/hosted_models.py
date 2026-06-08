"""
TRIDENT-AI Splunk Hosted Models Wrapper.

Provides Python wrappers for Splunk-hosted AI models:
  - CDTSM (Cisco Deep Time Series Model) — zero-shot metric forecasting
  - Foundation AI Security Model — autonomous threat classification

Both models are accessed via SPL `| apply` commands through the Splunk AI Toolkit.

Usage:
    from src.splunk.hosted_models import CDTSMClient, FoundationAIClient
    cdtsm = CDTSMClient(search_client)
    forecast = await cdtsm.forecast_metric("payments.latency_ms")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.splunk.search_client import SearchClient
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class CDTSMForecast:
    """Result from a CDTSM forecast."""
    metric_name: str
    forecast_values: list[float]
    lower_band: list[float]  # Q20 quantile values
    upper_band: list[float]  # Q80 quantile values
    actual_values: list[float]
    anomaly_detected: bool
    anomaly_severity: float  # How far outside the band
    anomaly_timestamp: Optional[str] = None
    raw_results: Optional[list[dict]] = None


@dataclass
class FoundationAIResult:
    """Result from Foundation AI Security Model analysis."""
    threat_type: str
    confidence_score: float
    attack_timeline: list[dict[str, str]]
    ioc_list: list[str]
    mitre_techniques: list[str]
    affected_users: list[str]
    narrative: str
    raw_results: Optional[list[dict]] = None


class CDTSMClient:
    """
    Wraps the Cisco Deep Time Series Model (CDTSM) for zero-shot metric forecasting.

    CDTSM is accessed via the Splunk AI Toolkit's `| apply` SPL command.
    Hard limit: holdback + forecast_k <= 384 (enforced by config validation).
    """

    def __init__(self, search_client: SearchClient) -> None:
        """
        Initialize CDTSM client.

        Args:
            search_client: SearchClient instance for executing SPL queries.
        """
        self._search = search_client
        # Enforce hard limit at init time
        total = settings.CDTSM_HOLDBACK + settings.CDTSM_FORECAST_K
        assert total <= 384, (
            f"CDTSM hard limit violated: holdback({settings.CDTSM_HOLDBACK}) + "
            f"forecast_k({settings.CDTSM_FORECAST_K}) = {total} > 384"
        )
        log.info(
            "cdtsm_client_init",
            model=settings.CDTSM_MODEL_NAME,
            holdback=settings.CDTSM_HOLDBACK,
            forecast_k=settings.CDTSM_FORECAST_K,
        )

    def _build_forecast_spl(self, metric_name: str) -> str:
        """
        Build the SPL query for CDTSM forecasting.

        Args:
            metric_name: The metric stream name to forecast (e.g., "payments.latency_ms").

        Returns:
            Complete SPL query string for CDTSM apply.
        """
        spl = (
            f'| inputlookup {metric_name}\n'
            f'| apply {settings.CDTSM_MODEL_NAME}\n'
            f'  holdback={settings.CDTSM_HOLDBACK}\n'
            f'  forecast_k={settings.CDTSM_FORECAST_K}\n'
            f'  quantiles=[{settings.CDTSM_QUANTILE_LOWER}, 0.5, {settings.CDTSM_QUANTILE_UPPER}]'
        )
        return spl

    def _build_metric_query_spl(self, metric_name: str, timespan: str = "5m") -> str:
        """
        Build SPL query to fetch raw metric data for CDTSM analysis.

        Args:
            metric_name: The metric to query.
            timespan: Time bucket span for aggregation.

        Returns:
            SPL query string.
        """
        spl = (
            f'index={settings.CDTSM_METRICS_INDEX} '
            f'sourcetype={settings.CDTSM_METRICS_SOURCETYPE} '
            f'metric_name="{metric_name}"\n'
            f'| timechart span={timespan} avg(metric_value) as value\n'
            f'| apply {settings.CDTSM_MODEL_NAME}\n'
            f'  holdback={settings.CDTSM_HOLDBACK}\n'
            f'  forecast_k={settings.CDTSM_FORECAST_K}\n'
            f'  quantiles=[{settings.CDTSM_QUANTILE_LOWER}, 0.5, {settings.CDTSM_QUANTILE_UPPER}]'
        )
        return spl

    async def forecast_metric(
        self,
        metric_name: str,
        use_lookup: bool = True,
    ) -> CDTSMForecast:
        """
        Run CDTSM zero-shot forecasting on a metric stream.

        Args:
            metric_name: The metric to forecast.
            use_lookup: If True, use inputlookup (pre-loaded data).
                        If False, query live metric index.

        Returns:
            CDTSMForecast with predictions, quantile bands, and anomaly detection.
        """
        log.info("cdtsm_forecast_start", metric=metric_name)

        if use_lookup:
            spl = self._build_forecast_spl(metric_name)
        else:
            spl = self._build_metric_query_spl(metric_name)

        results = await self._search.execute_search(
            spl,
            earliest_time="-4h",
            latest_time="now",
        )

        return self._parse_forecast(metric_name, results)

    def _parse_forecast(
        self,
        metric_name: str,
        results: list[dict[str, Any]],
    ) -> CDTSMForecast:
        """
        Parse CDTSM forecast results into a structured object.

        Extracts quantile bands and detects anomalies where actual values
        breach the [Q20, Q80] band by more than ANOMALY_DEVIATION_THRESHOLD.

        Args:
            metric_name: The metric name for context.
            results: Raw search results from CDTSM apply.

        Returns:
            CDTSMForecast object.
        """
        forecast_values = []
        lower_band = []
        upper_band = []
        actual_values = []
        anomaly_detected = False
        anomaly_severity = 0.0
        anomaly_timestamp = None

        for row in results:
            # Extract CDTSM output columns
            actual = self._safe_float(row.get("value") or row.get("actual"))
            predicted = self._safe_float(row.get("predicted"))
            lower = self._safe_float(
                row.get(f"lower{settings.CDTSM_QUANTILE_LOWER}")
                or row.get("lower")
                or row.get(f"quantile_{settings.CDTSM_QUANTILE_LOWER}")
            )
            upper = self._safe_float(
                row.get(f"upper{settings.CDTSM_QUANTILE_UPPER}")
                or row.get("upper")
                or row.get(f"quantile_{settings.CDTSM_QUANTILE_UPPER}")
            )

            if predicted is not None:
                forecast_values.append(predicted)
            if lower is not None:
                lower_band.append(lower)
            if upper is not None:
                upper_band.append(upper)
            if actual is not None:
                actual_values.append(actual)

            # Anomaly detection: actual outside [Q20, Q80] band
            if actual is not None and lower is not None and upper is not None:
                band_width = upper - lower if upper > lower else 1.0
                if actual > upper:
                    deviation = (actual - upper) / band_width
                    if deviation > settings.ANOMALY_DEVIATION_THRESHOLD:
                        anomaly_detected = True
                        if deviation > anomaly_severity:
                            anomaly_severity = deviation
                            anomaly_timestamp = row.get("_time")
                elif actual < lower:
                    deviation = (lower - actual) / band_width
                    if deviation > settings.ANOMALY_DEVIATION_THRESHOLD:
                        anomaly_detected = True
                        if deviation > anomaly_severity:
                            anomaly_severity = deviation
                            anomaly_timestamp = row.get("_time")

        log.info(
            "cdtsm_forecast_complete",
            metric=metric_name,
            anomaly_detected=anomaly_detected,
            anomaly_severity=round(anomaly_severity, 3),
            data_points=len(results),
        )

        return CDTSMForecast(
            metric_name=metric_name,
            forecast_values=forecast_values,
            lower_band=lower_band,
            upper_band=upper_band,
            actual_values=actual_values,
            anomaly_detected=anomaly_detected,
            anomaly_severity=round(anomaly_severity, 3),
            anomaly_timestamp=anomaly_timestamp,
            raw_results=results,
        )

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert a value to float, returning None on failure."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class FoundationAIClient:
    """
    Wraps the Foundation AI Security Model (foundation-sec-1.1-8b-instruct).

    Accessed via Splunk AI Toolkit. Performs autonomous threat classification,
    MITRE ATT&CK mapping, and IoC extraction from security logs.
    """

    def __init__(self, search_client: SearchClient) -> None:
        """
        Initialize Foundation AI client.

        Args:
            search_client: SearchClient instance for executing SPL queries.
        """
        self._search = search_client
        log.info(
            "foundation_ai_init",
            model=settings.FOUNDATION_AI_MODEL,
            security_index=settings.SECURITY_LOGS_INDEX,
        )

    def _build_analysis_spl(
        self,
        earliest: str = "-15m",
        additional_filter: str = "",
    ) -> str:
        """
        Build SPL query for Foundation AI threat analysis.

        Args:
            earliest: How far back to search for security logs.
            additional_filter: Extra SPL filter conditions.

        Returns:
            Complete SPL query string.
        """
        filter_clause = f" {additional_filter}" if additional_filter else ""
        spl = (
            f'search index={settings.SECURITY_LOGS_INDEX} '
            f'sourcetype={settings.SECURITY_SOURCETYPE}'
            f'{filter_clause}\n'
            f'earliest={earliest}\n'
            f'| eval log_text = _raw\n'
            f'| apply {settings.FOUNDATION_AI_MODEL}\n'
            f'  field=log_text\n'
            f'  task="threat_classification"'
        )
        return spl

    async def analyze_threats(
        self,
        earliest: str = "-15m",
        additional_filter: str = "",
    ) -> FoundationAIResult:
        """
        Run Foundation AI threat analysis on recent security logs.

        Args:
            earliest: How far back to look for threats.
            additional_filter: Additional SPL filter conditions.

        Returns:
            FoundationAIResult with threat classification, MITRE mapping, IoCs.
        """
        log.info("foundation_ai_analysis_start", earliest=earliest)

        spl = self._build_analysis_spl(earliest, additional_filter)
        results = await self._search.execute_search(spl, earliest_time=earliest)

        return self._parse_results(results)

    def _parse_results(self, results: list[dict[str, Any]]) -> FoundationAIResult:
        """
        Parse Foundation AI model output into structured result.

        Args:
            results: Raw search results from Foundation AI apply.

        Returns:
            FoundationAIResult with enriched threat intelligence.
        """
        # Aggregate findings across all result rows
        threat_types: dict[str, int] = {}
        confidence_scores: list[float] = []
        timeline: list[dict[str, str]] = []
        iocs: set[str] = set()
        mitre_ids: set[str] = set()
        users: set[str] = set()
        narratives: list[str] = []

        for row in results:
            # Extract Foundation AI model outputs
            threat = row.get("threat_type") or row.get("predicted_threat_type", "None")
            confidence = CDTSMClient._safe_float(
                row.get("confidence_score") or row.get("confidence", 0)
            ) or 0.0

            if threat and threat != "None":
                threat_types[threat] = threat_types.get(threat, 0) + 1
                confidence_scores.append(confidence)

            # IoCs
            for ioc_field in ("src_ip", "src", "clientip", "dest_ip", "dest"):
                if row.get(ioc_field):
                    iocs.add(row[ioc_field])

            # MITRE techniques
            techniques = row.get("mitre_techniques", "")
            if isinstance(techniques, str) and techniques:
                for t in techniques.replace("[", "").replace("]", "").replace('"', "").split(","):
                    t = t.strip()
                    if t.startswith("T"):
                        mitre_ids.add(t)

            # Users
            for user_field in ("user", "username", "src_user", "dest_user"):
                if row.get(user_field):
                    users.add(row[user_field])

            # Timeline events
            if row.get("_time"):
                timeline.append({
                    "timestamp": row["_time"],
                    "event": row.get("action", row.get("_raw", "")[:200]),
                    "source": "security",
                })

            if row.get("narrative"):
                narratives.append(row["narrative"])

        # Determine dominant threat type
        dominant_threat = max(threat_types, key=threat_types.get) if threat_types else "None"
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )
        narrative = " ".join(narratives[:3]) if narratives else (
            f"Foundation AI analyzed {len(results)} security log entries. "
            f"Dominant threat type: {dominant_threat} with "
            f"average confidence {avg_confidence:.2f}."
        )

        log.info(
            "foundation_ai_analysis_complete",
            threat_type=dominant_threat,
            confidence=round(avg_confidence, 3),
            ioc_count=len(iocs),
            mitre_count=len(mitre_ids),
        )

        return FoundationAIResult(
            threat_type=dominant_threat,
            confidence_score=round(avg_confidence, 3),
            attack_timeline=sorted(timeline, key=lambda x: x.get("timestamp", "")),
            ioc_list=sorted(iocs),
            mitre_techniques=sorted(mitre_ids),
            affected_users=sorted(users),
            narrative=narrative,
            raw_results=results,
        )
