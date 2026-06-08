#!/usr/bin/env python3
"""
TRIDENT-AI Metrics Generator.

Generates CDTSM-compatible time-series data for demo purposes.
Creates 30 days of synthetic metric history with a recent anomaly spike.

Usage:
    python demo/generate_metrics.py
"""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_30_day_metrics(
    metric_name: str = "payments.latency_ms",
    host: str = "payments-api-02",
    base_value: float = 120.0,
    noise_stddev: float = 15.0,
    interval_minutes: int = 5,
) -> list[dict]:
    """
    Generate 30 days of realistic metric data with daily/weekly seasonality.

    Args:
        metric_name: Name of the metric.
        host: Host generating the metric.
        base_value: Average baseline value.
        noise_stddev: Standard deviation of noise.
        interval_minutes: Minutes between data points.

    Returns:
        List of metric data point dicts.
    """
    metrics = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    current = start_time

    while current <= end_time:
        # Daily seasonality (higher during business hours UTC)
        hour = current.hour
        daily_factor = 1.0 + 0.3 * math.sin((hour - 14) * math.pi / 12)

        # Weekly seasonality (lower on weekends)
        weekday = current.weekday()
        weekly_factor = 0.7 if weekday >= 5 else 1.0

        # Base value with seasonality
        value = base_value * daily_factor * weekly_factor

        # Add noise
        value += random.gauss(0, noise_stddev)

        # Clamp to reasonable range
        value = max(base_value * 0.3, value)

        metrics.append({
            "time": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metric": metric_name,
            "value": round(value, 2),
            "host": host,
            "region": "us-east-1",
        })

        current += timedelta(minutes=interval_minutes)

    return metrics


def inject_anomaly(
    metrics: list[dict],
    anomaly_start_offset_hours: float = 1.0,
    anomaly_duration_minutes: int = 30,
    spike_multiplier: float = 2.8,
) -> list[dict]:
    """
    Inject an anomaly spike into the tail end of the metric series.

    Args:
        metrics: List of metric data points.
        anomaly_start_offset_hours: Hours before the end to start anomaly.
        anomaly_duration_minutes: Duration of the anomaly in minutes.
        spike_multiplier: How much to multiply the baseline by.

    Returns:
        Modified metrics list with anomaly injected.
    """
    if not metrics:
        return metrics

    end_time = datetime.strptime(metrics[-1]["time"], "%Y-%m-%dT%H:%M:%SZ")
    anomaly_start = end_time - timedelta(hours=anomaly_start_offset_hours)
    anomaly_end = anomaly_start + timedelta(minutes=anomaly_duration_minutes)

    for m in metrics:
        t = datetime.strptime(m["time"], "%Y-%m-%dT%H:%M:%SZ")
        if anomaly_start <= t <= anomaly_end:
            progress = (t - anomaly_start).total_seconds() / (anomaly_duration_minutes * 60)
            # Exponential ramp up
            factor = 1.0 + (spike_multiplier - 1.0) * (progress ** 1.5)
            m["value"] = round(m["value"] * factor, 2)
            m["anomaly"] = True

    return metrics


def main() -> None:
    """Generate 30-day metric history with anomaly spike."""
    print()
    print("  ⚡ TRIDENT-AI Metric Generator")
    print("  ══════════════════════════════")
    print()

    output_dir = Path("./demo/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate metrics for each monitored stream
    all_metrics = []
    metric_configs = [
        ("payments.latency_ms", "payments-api-02", 120.0, 15.0),
        ("api.cpu_percent", "api-gateway-01", 35.0, 5.0),
        ("auth.request_rate", "auth-service-01", 50.0, 8.0),
        ("api.error_rate", "api-gateway-01", 0.5, 0.2),
    ]

    for name, host, base, noise in metric_configs:
        print(f"  📈 Generating {name}...")
        metrics = generate_30_day_metrics(name, host, base, noise)
        metrics = inject_anomaly(metrics)
        all_metrics.extend(metrics)
        print(f"     → {len(metrics)} data points")

    # Save
    output_file = output_dir / "metrics.json"
    with open(output_file, "w") as f:
        json.dump({"metrics": all_metrics}, f, indent=2)

    print(f"\n  ✅ Written {len(all_metrics)} total data points → {output_file}")
    print()


if __name__ == "__main__":
    main()
