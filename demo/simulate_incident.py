#!/usr/bin/env python3
"""
TRIDENT-AI Demo Incident Simulator.

Injects a realistic multi-domain incident into Splunk (or local files).
Simulates a flash sale retail scenario with:

Phase 1 — Normal (first 30 minutes): steady latency, normal logins, low CPU
Phase 2 — Incident begins (T+31 min): latency spike, brute-force, bad search
Phase 3 — CDTSM detects breach (T+43 min): actual crosses Q80 band
Phase 4 — Incident package generated: Bedrock synthesises in <30 seconds

Usage:
    python demo/simulate_incident.py
    python demo/simulate_incident.py --demo-mode  # Write to local files only
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_baseline_metrics(
    start_time: datetime,
    duration_minutes: int = 30,
    interval_seconds: int = 60,
) -> list[dict]:
    """
    Generate 30 days of normal baseline metric data for CDTSM context.

    Args:
        start_time: Start time for the baseline period.
        duration_minutes: Duration in minutes for the baseline.
        interval_seconds: Interval between data points.

    Returns:
        List of metric data points as dicts.
    """
    metrics = []
    current = start_time
    end = start_time + timedelta(minutes=duration_minutes)

    while current < end:
        # Normal steady state
        latency = random.gauss(120, 15)  # ~120ms average, 15ms stddev
        cpu = random.gauss(35, 5)  # ~35% average
        request_rate = random.gauss(50, 8)  # ~50 req/sec
        error_rate = random.gauss(0.5, 0.2)  # ~0.5% error rate

        for metric_name, value, host in [
            ("payments.latency_ms", max(10, latency), "payments-api-02"),
            ("api.cpu_percent", max(1, min(100, cpu)), "api-gateway-01"),
            ("auth.request_rate", max(0, request_rate), "auth-service-01"),
            ("api.error_rate", max(0, min(100, error_rate)), "api-gateway-01"),
        ]:
            metrics.append({
                "time": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "metric": metric_name,
                "value": round(value, 2),
                "host": host,
                "region": "us-east-1",
            })

        current += timedelta(seconds=interval_seconds)

    return metrics


def generate_incident_spike(
    start_time: datetime,
    duration_minutes: int = 15,
    interval_seconds: int = 60,
) -> list[dict]:
    """
    Generate the incident spike data (Phase 2 — latency climbing, CPU spiking).

    Args:
        start_time: When the incident begins.
        duration_minutes: Duration of the incident in minutes.
        interval_seconds: Data point interval.

    Returns:
        List of anomalous metric data points.
    """
    metrics = []
    current = start_time
    end = start_time + timedelta(minutes=duration_minutes)
    elapsed_minutes = 0

    while current < end:
        # Progressive degradation
        progress = elapsed_minutes / duration_minutes

        # Latency: 120ms → 340ms exponential climb
        latency = 120 + (220 * (progress ** 1.5)) + random.gauss(0, 10)

        # CPU: 35% → 94% spike
        cpu = 35 + (59 * progress) + random.gauss(0, 3)

        # Error rate: 0.5% → 12%
        error_rate = 0.5 + (11.5 * progress) + random.gauss(0, 0.5)

        # Request rate stays elevated during attack
        request_rate = 50 + (2000 * progress) + random.gauss(0, 20)

        for metric_name, value, host in [
            ("payments.latency_ms", max(10, latency), "payments-api-02"),
            ("api.cpu_percent", max(1, min(100, cpu)), "api-gateway-01"),
            ("auth.request_rate", max(0, request_rate), "auth-service-01"),
            ("api.error_rate", max(0, min(100, error_rate)), "api-gateway-01"),
        ]:
            metrics.append({
                "time": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "metric": metric_name,
                "value": round(value, 2),
                "host": host,
                "region": "us-east-1",
            })

        current += timedelta(seconds=interval_seconds)
        elapsed_minutes += interval_seconds / 60

    return metrics


def generate_security_logs(
    start_time: datetime,
    duration_minutes: int = 5,
    attack_ip: str = "203.0.113.45",
) -> list[dict]:
    """
    Generate realistic brute-force attack security logs.

    Simulates 2,000 login attempts/minute from the attack IP,
    with 12 successful (200) responses scattered among 401s.

    Args:
        start_time: When the attack begins.
        duration_minutes: Duration of the attack.
        attack_ip: Source IP of the attacker.

    Returns:
        List of security log entries.
    """
    logs = []
    current = start_time
    end = start_time + timedelta(minutes=duration_minutes)

    # Target usernames for the attack
    target_users = [
        "admin", "root", "administrator", "user1", "test",
        "deploy", "service-account", "jenkins", "gitlab-runner",
        "backup-admin", "db-admin", "api-user",
    ]

    # Success indices (12 successful 200s scattered through the attack)
    total_attempts = duration_minutes * 2000
    success_indices = set(random.sample(range(total_attempts), 12))

    attempt = 0
    while current < end:
        # Generate ~33 attempts per second (2000/min)
        for _ in range(33):
            status = 200 if attempt in success_indices else 401
            user = random.choice(target_users)

            # Apache combined log format
            raw_log = (
                f'{attack_ip} - {user} [{current.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
                f'"POST /api/auth/login HTTP/1.1" {status} 127 "-" '
                f'"python-requests/2.28.0"'
            )

            logs.append({
                "time": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "timestamp": current.strftime("%d/%b/%Y:%H:%M:%S +0000"),
                "src_ip": attack_ip,
                "user": user,
                "action": "login_attempt",
                "status_code": status,
                "method": "POST",
                "uri": "/api/auth/login",
                "user_agent": "python-requests/2.28.0",
                "bytes": 127,
                "raw": raw_log,
            })

            attempt += 1
            current += timedelta(milliseconds=30)  # ~33 per second

    return logs


def generate_platform_data(start_time: datetime) -> list[dict]:
    """
    Generate Splunk internal performance data.

    Simulates a poorly written scheduled search consuming excessive resources.

    Args:
        start_time: Timestamp for the platform data.

    Returns:
        List of platform health data points.
    """
    return [
        {
            "type": "heavy_search",
            "title": "Flash Sale - Realtime Revenue Dashboard",
            "owner": "jr-admin",
            "runDuration": 482,
            "scanCount": 45000000,
            "cpu_estimate": 103.5,
            "dispatchState": "RUNNING",
            "time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        {
            "type": "config_change",
            "host": "idx-cluster-01",
            "file": "inputs.conf",
            "action": "modified",
            "user": "jr-admin",
            "count": 3,
            "time": (start_time - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        {
            "type": "queue_warning",
            "name": "parsingQueue",
            "avg_fill_kb": 7840.5,
            "time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        {
            "type": "queue_warning",
            "name": "indexQueue",
            "avg_fill_kb": 6120.3,
            "time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    ]


def save_demo_data(
    metrics: list[dict],
    security_logs: list[dict],
    platform_data: list[dict],
    output_dir: Path,
) -> None:
    """
    Save generated demo data to JSON files.

    Args:
        metrics: All metric data points (baseline + incident).
        security_logs: Security log entries.
        platform_data: Platform health data.
        output_dir: Directory to write files to.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "metrics.json", "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)
    print(f"  ✅ Written {len(metrics)} metric points → metrics.json")

    with open(output_dir / "security_logs.json", "w") as f:
        json.dump({"logs": security_logs}, f, indent=2)
    print(f"  ✅ Written {len(security_logs)} security logs → security_logs.json")

    with open(output_dir / "platform_data.json", "w") as f:
        json.dump({"data": platform_data}, f, indent=2)
    print(f"  ✅ Written {len(platform_data)} platform records → platform_data.json")


def main() -> None:
    """Generate and save demo incident simulation data."""
    parser = argparse.ArgumentParser(description="TRIDENT-AI Demo Incident Simulator")
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        default=True,
        help="Write to local files only (default: True)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./demo/sample_data",
        help="Output directory for demo data files",
    )
    args = parser.parse_args()

    print()
    print("  ⚡ TRIDENT-AI Demo Incident Simulator")
    print("  ═════════════════════════════════════")
    print()

    # Timeline
    now = datetime.utcnow()
    baseline_start = now - timedelta(minutes=45)
    incident_start = baseline_start + timedelta(minutes=31)
    attack_start = incident_start + timedelta(minutes=2)

    print("  📊 Generating baseline metrics (30 minutes of normal)...")
    baseline = generate_baseline_metrics(baseline_start, duration_minutes=30)

    print("  🔥 Generating incident spike (15 minutes of degradation)...")
    spike = generate_incident_spike(incident_start, duration_minutes=15)

    print("  🔐 Generating brute-force attack logs (2000 attempts/min)...")
    security = generate_security_logs(attack_start, duration_minutes=5)

    print("  🖥️  Generating platform health data...")
    platform = generate_platform_data(incident_start + timedelta(minutes=5))

    all_metrics = baseline + spike
    print(f"\n  📦 Total data generated:")
    print(f"     • {len(all_metrics)} metric data points")
    print(f"     • {len(security)} security log entries")
    print(f"     • {len(platform)} platform records")

    output_dir = Path(args.output_dir)
    print(f"\n  💾 Saving to {output_dir}/...")
    save_demo_data(all_metrics, security, platform, output_dir)

    print(f"\n  ✅ Demo data ready! Run 'DEMO_MODE=true python main.py' to test.")
    print()


if __name__ == "__main__":
    main()
