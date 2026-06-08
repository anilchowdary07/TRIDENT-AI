"""
TRIDENT-AI Telemetry Sentinel Agent.

Uses the Cisco Deep Time Series Model (CDTSM) for zero-shot metric forecasting.
When actual metric values breach the [Q20, Q80] quantile band by more than
ANOMALY_DEVIATION_THRESHOLD, the agent triggers an investigation.

CDTSM API via Splunk AI Toolkit:
    | inputlookup <metric_series>
    | apply cdtsm holdback=<N> forecast_k=<K> quantiles=[0.2, 0.5, 0.8]

CRITICAL CONSTRAINT: holdback + forecast_k <= 384 (hard limit)

Usage:
    from src.agents.telemetry_sentinel import TelemetrySentinel
    sentinel = TelemetrySentinel(search_client)
    finding = await sentinel.investigate()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models.agent_finding import AgentStatus, TelemetryFinding
from src.splunk.hosted_models import CDTSMClient, CDTSMForecast
from src.splunk.search_client import SearchClient
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# ─── Default metrics to monitor ─────────────────────────────────────────
DEFAULT_METRICS = [
    "payments.latency_ms",
    "auth.request_rate",
    "api.cpu_percent",
    "api.error_rate",
]


class TelemetrySentinel(BaseAgent):
    """
    CDTSM-powered telemetry monitoring agent.

    Continuously forecasts metric streams and detects anomalies
    when actual values breach the quantile confidence bands.
    """

    def __init__(
        self,
        search_client: SearchClient,
        metrics: list[str] | None = None,
    ) -> None:
        """
        Initialize the Telemetry Sentinel.

        Args:
            search_client: SearchClient for SPL execution.
            metrics: List of metric names to monitor. Defaults to DEFAULT_METRICS.
        """
        super().__init__("TelemetrySentinel")
        self._search = search_client
        self._cdtsm = CDTSMClient(search_client)
        self._metrics = metrics or DEFAULT_METRICS

    async def _investigate(self, context: dict[str, Any]) -> TelemetryFinding:
        """
        Run CDTSM forecasting on all configured metric streams.

        In demo mode, loads data from local sample files instead of live Splunk.

        Args:
            context: Optional context. If "metric_name" is set, only checks that metric.

        Returns:
            TelemetryFinding with the most severe anomaly detected (if any).
        """
        log.info(
            "telemetry_sentinel_starting",
            metrics=self._metrics,
            demo_mode=settings.DEMO_MODE,
        )

        if settings.DEMO_MODE:
            return await self._investigate_demo(context)

        # Check specific metric or all configured metrics
        target_metrics = (
            [context["metric_name"]] if "metric_name" in context else self._metrics
        )

        worst_finding: TelemetryFinding | None = None
        worst_severity = 0.0

        for metric in target_metrics:
            try:
                forecast = await self._cdtsm.forecast_metric(metric)
                finding = self._forecast_to_finding(forecast)

                if finding.anomaly_detected and finding.anomaly_severity > worst_severity:
                    worst_finding = finding
                    worst_severity = finding.anomaly_severity

            except Exception as e:
                log.warning(
                    "telemetry_metric_error",
                    metric=metric,
                    error=str(e),
                )

        if worst_finding:
            return worst_finding

        # No anomalies found
        return TelemetryFinding(
            status=AgentStatus.COMPLETE,
            anomaly_detected=False,
            anomaly_severity=0.0,
        )

    async def _investigate_demo(self, context: dict[str, Any]) -> TelemetryFinding:
        """
        Run investigation using local demo data instead of live Splunk.

        Loads metrics from demo/sample_data/metrics.json and simulates
        CDTSM output.

        Args:
            context: Investigation context.

        Returns:
            TelemetryFinding from demo data.
        """
        demo_path = Path(settings.DEMO_DATA_PATH) / "metrics.json"
        log.info("telemetry_demo_mode", path=str(demo_path))

        try:
            with open(demo_path) as f:
                demo_data = json.load(f)
        except FileNotFoundError:
            log.warning("telemetry_demo_data_not_found", path=str(demo_path))
            return TelemetryFinding(
                status=AgentStatus.COMPLETE,
                anomaly_detected=False,
            )

        # Parse demo data to simulate CDTSM output
        metrics = demo_data if isinstance(demo_data, list) else demo_data.get("metrics", [])

        actual_values = [m.get("value", 0) for m in metrics]
        # Simulate quantile bands
        if actual_values:
            import statistics
            mean = statistics.mean(actual_values[:-24])  # Use all but last 24 as baseline
            stdev = statistics.stdev(actual_values[:-24]) if len(actual_values) > 25 else mean * 0.1
            lower_band = [mean - 1.2 * stdev] * len(actual_values)
            upper_band = [mean + 1.2 * stdev] * len(actual_values)
        else:
            lower_band = []
            upper_band = []

        # Detect anomalies
        anomaly_detected = False
        anomaly_severity = 0.0
        anomaly_timestamp = None

        for i, val in enumerate(actual_values):
            if i < len(upper_band) and upper_band[i] > lower_band[i]:
                band_width = upper_band[i] - lower_band[i]
                if val > upper_band[i]:
                    deviation = (val - upper_band[i]) / band_width
                    if deviation > settings.ANOMALY_DEVIATION_THRESHOLD:
                        anomaly_detected = True
                        if deviation > anomaly_severity:
                            anomaly_severity = deviation
                            anomaly_timestamp = metrics[i].get("time", "")

        finding = TelemetryFinding(
            status=AgentStatus.COMPLETE,
            metric_name=metrics[0].get("metric", "demo.metric") if metrics else "demo.metric",
            anomaly_detected=anomaly_detected,
            anomaly_severity=round(anomaly_severity, 3),
            anomaly_timestamp=anomaly_timestamp,
            forecast_band={"lower": lower_band[-48:], "upper": upper_band[-48:]},
            actual_vs_forecast={
                "actual": actual_values[-48:],
                "forecast": [statistics.mean(actual_values[:-24])] * 48 if actual_values else [],
            },
            forecast_k=settings.CDTSM_FORECAST_K,
            holdback=settings.CDTSM_HOLDBACK,
        )

        log.info(
            "telemetry_demo_complete",
            anomaly_detected=anomaly_detected,
            severity=round(anomaly_severity, 3),
        )

        return finding

    def _forecast_to_finding(self, forecast: CDTSMForecast) -> TelemetryFinding:
        """
        Convert a CDTSMForecast into a TelemetryFinding.

        Args:
            forecast: CDTSM forecast result.

        Returns:
            TelemetryFinding with mapped fields.
        """
        return TelemetryFinding(
            status=AgentStatus.COMPLETE,
            metric_name=forecast.metric_name,
            anomaly_detected=forecast.anomaly_detected,
            anomaly_severity=forecast.anomaly_severity,
            anomaly_timestamp=forecast.anomaly_timestamp,
            forecast_band={
                "lower": forecast.lower_band,
                "upper": forecast.upper_band,
            },
            actual_vs_forecast={
                "actual": forecast.actual_values,
                "forecast": forecast.forecast_values,
            },
            forecast_k=settings.CDTSM_FORECAST_K,
            holdback=settings.CDTSM_HOLDBACK,
            raw_data={"raw_result_count": len(forecast.raw_results or [])},
        )
