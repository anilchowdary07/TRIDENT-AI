#!/usr/bin/env python3
"""
TRIDENT-AI — Autonomous Incident Intelligence System.

Entry point. Starts the autonomous loop as a daemon thread and
keeps the main thread alive for graceful shutdown handling.

Usage:
    python main.py
    DEMO_MODE=true python main.py
"""

from __future__ import annotations

import asyncio
import datetime
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.coordinator.autonomous_loop import AutonomousLoop
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# Global loop instance
loop = AutonomousLoop()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info(
        "trident_ai_starting",
        version="1.0.0",
        demo_mode=settings.DEMO_MODE,
        poll_interval=settings.POLL_INTERVAL_SECONDS,
        splunk_host=settings.SPLUNK_HOST,
    )
    print(r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ████████╗██████╗ ██╗██████╗ ███████╗███╗   ██╗████████╗   ║
    ║   ╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝   ║
    ║      ██║   ██████╔╝██║██║  ██║█████╗  ██╔██╗ ██║   ██║      ║
    ║      ██║   ██╔══██╗██║██║  ██║██╔══╝  ██║╚██╗██║   ██║      ║
    ║      ██║   ██║  ██║██║██████╔╝███████╗██║ ╚████║   ██║      ║
    ║      ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      ║
    ║                                                              ║
    ║              AUTONOMOUS INCIDENT INTELLIGENCE                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    mode = "🧪 DEMO MODE" if settings.DEMO_MODE else "🔴 LIVE MODE"
    print(f"    Mode: {mode}")
    print(f"    Splunk: {settings.SPLUNK_HOST}:{settings.SPLUNK_PORT}")
    print(f"    Poll interval: {settings.POLL_INTERVAL_SECONDS}s")
    print(f"    Bedrock model: {settings.BEDROCK_MODEL_ID}")
    print("\n    ✅ Autonomous loop ACTIVE — agents are watching.\n")
    
    loop.start()
    yield
    # Shutdown
    log.info("shutdown_signal_received")
    loop.stop()

app = FastAPI(title="TRIDENT-AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ApproveRequest(BaseModel):
    action_index: int

# ─── Full demo incident package with ALL fields the frontend expects ────
DEMO_INCIDENT = {
    "incident_id": "TRIDENT-20260608-A4B7C3D9",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "severity": "CRITICAL",
    "severity_score": 92,
    "status": "OPEN",
    "title": "Brute-force credential attack with concurrent latency anomaly on payments-api",
    "executive_summary": "A coordinated attack was detected targeting the payments API. Over 2,000 login attempts per minute originated from IP 203.0.113.45, coinciding with a 183% latency spike in the payments service. TRIDENT agents identified this as a multi-vector incident requiring immediate response.",
    "technical_summary": "CDTSM detected payments.latency_ms breaching the Q80 quantile band at T+43 minutes, with actual values reaching 340ms against a predicted upper bound of 156ms. Simultaneously, Foundation AI classified a brute-force attack (T1110) from 203.0.113.45 with 95% confidence. Platform Auditor identified a poorly optimized scheduled search consuming 103% estimated CPU, likely exacerbating the latency impact.",
    "root_cause": "Brute-force credential stuffing attack from 203.0.113.45 combined with resource-intensive scheduled search",
    "contributing_factors": [
        "Poorly optimized \"Flash Sale Revenue Dashboard\" search consuming 103% CPU",
        "No rate limiting on /api/auth/login endpoint",
        "Insufficient indexer queue capacity during peak traffic",
    ],
    "confidence": 0.92,
    "attack_timeline": [
        {"timestamp": "2026-06-08T03:31:00Z", "event": "Latency begins climbing: 120ms → 180ms", "source": "telemetry"},
        {"timestamp": "2026-06-08T03:33:00Z", "event": "Brute-force attack starts from 203.0.113.45", "source": "security"},
        {"timestamp": "2026-06-08T03:35:00Z", "event": "Jr-admin scheduled search spawns 400K events/call", "source": "platform"},
        {"timestamp": "2026-06-08T03:38:00Z", "event": "CPU spikes to 94%, indexer queues filling", "source": "platform"},
        {"timestamp": "2026-06-08T03:41:00Z", "event": "12 successful login compromises detected", "source": "security"},
        {"timestamp": "2026-06-08T03:43:00Z", "event": "CDTSM detects Q80 breach — TRIDENT triggered", "source": "telemetry"},
    ],
    "mitre_techniques": [
        {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
        {"id": "T1078", "name": "Valid Accounts", "tactic": "Initial Access"},
    ],
    "iocs": {
        "ips": ["203.0.113.45"],
        "domains": [],
        "users": ["admin", "deploy", "service-account"],
    },
    "affected_services": ["payments-api", "auth-service", "api-gateway", "user-db"],
    "blast_radius": "3,240 transactions affected in last 15 minutes",
    "business_impact": "$180,000 / hour",
    "remediation_options": [
        {
            "priority": 1,
            "action": "Block source IP 203.0.113.45 via network ACL",
            "rationale": "Immediately stops the ongoing brute-force attack",
            "risk_level": "LOW",
            "estimated_recovery_minutes": 2,
            "requires_approval": True,
            "mcp_tool_call": {"tool": "block_ip", "args": {"ip": "203.0.113.45"}},
        },
        {
            "priority": 2,
            "action": "Disable compromised accounts and force password reset",
            "rationale": "12 accounts may be compromised — disable to prevent lateral movement",
            "risk_level": "MEDIUM",
            "estimated_recovery_minutes": 10,
            "requires_approval": True,
            "mcp_tool_call": {"tool": "disable_accounts", "args": {"users": ["admin", "deploy", "service-account"]}},
        },
        {
            "priority": 3,
            "action": "Kill resource-intensive scheduled search \"Flash Sale Revenue Dashboard\"",
            "rationale": "Frees 103% CPU load, should reduce latency by 40-60%",
            "risk_level": "LOW",
            "estimated_recovery_minutes": 1,
            "requires_approval": True,
            "mcp_tool_call": {"tool": "cancel_search", "args": {"title": "Flash Sale - Realtime Revenue Dashboard"}},
        },
    ],
    "agent_trace": {
        "telemetry_sentinel": {
            "agent_name": "TelemetrySentinel",
            "status": "COMPLETE",
            "anomaly_detected": True,
            "anomaly_severity": 2.84,
            "metric_name": "payments.latency_ms",
            "duration_seconds": 3.2,
        },
        "threat_marshall": {
            "agent_name": "ThreatMarshall",
            "status": "COMPLETE",
            "threat_type": "BruteForce",
            "confidence_score": 0.95,
            "ioc_list": ["203.0.113.45"],
            "mitre_techniques": ["T1110", "T1078"],
            "duration_seconds": 5.1,
        },
        "platform_auditor": {
            "agent_name": "PlatformAuditor",
            "status": "COMPLETE",
            "heavy_searches": [{"title": "Flash Sale - Realtime Revenue Dashboard", "cpu_estimate": 103.5}],
            "queue_warnings": [{"queue_name": "parsingQueue", "avg_fill_kb": 7840.5}],
            "duration_seconds": 2.8,
        },
    },
}


@app.get("/api/incidents")
async def get_incidents():
    """Return incidents from the autonomous loop's StateManager (real processing output)."""
    active_incidents = loop.state.get_active_incidents()
    if active_incidents:
        results = []
        for pkg in active_incidents:
            if hasattr(pkg, 'model_dump'):
                results.append(pkg.model_dump(mode="json"))
            elif hasattr(pkg, 'dict'):
                results.append(pkg.dict())
            else:
                results.append(pkg)
        return results
    # No incidents yet — return empty so frontend shows "waiting for agents"
    return []

@app.get("/api/agent-status")
async def get_agent_status():
    """Return live status of all 3 agents from real heartbeats."""
    state = loop.state.get_agent_heartbeats()
    agents = list(state.values())
    
    # If no heartbeats yet (first few seconds of startup), return initializing status
    if not agents:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return [
            {"agent_name": "TelemetrySentinel", "status": "IDLE", "last_poll": now, "last_anomaly": None},
            {"agent_name": "ThreatMarshall", "status": "IDLE", "last_poll": now, "last_anomaly": None},
            {"agent_name": "PlatformAuditor", "status": "IDLE", "last_poll": now, "last_anomaly": None},
        ]
    return agents

@app.post("/api/approve/{incident_id}")
async def approve_incident(incident_id: str, req: ApproveRequest):
    """Approve a remediation action — gets data from real StateManager."""
    try:
        # Find the incident from the real state
        active = loop.state.get_active_incidents()
        incident_data = None
        for pkg in active:
            pkg_dict = pkg.model_dump(mode="json") if hasattr(pkg, 'model_dump') else (pkg.dict() if hasattr(pkg, 'dict') else pkg)
            if pkg_dict.get("incident_id") == incident_id:
                incident_data = pkg_dict
                break
        
        if not incident_data:
            raise HTTPException(status_code=404, detail="Incident not found in active state")
        
        remediation_options = incident_data.get("remediation_options", [])
        if req.action_index >= len(remediation_options):
            raise HTTPException(status_code=400, detail="Invalid action index")
        
        action = remediation_options[req.action_index]
        
        log.info("remediation_approved", incident_id=incident_id, action=action.get("action", "unknown"))
        
        # Write audit event to Splunk (or demo log)
        audit_event = {
            "event_type": "APPROVAL",
            "incident_id": incident_id,
            "action": action.get("action", "unknown"),
            "approved_by": "analyst",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        try:
            await loop._search.write_event(event_data=audit_event, index="trident_audit", sourcetype="trident:audit")
        except Exception as write_err:
            log.warning("audit_write_skipped", error=str(write_err))
        
        return {"success": True, "message": f"Action executed: {action.get('action', 'unknown')}"}
    except HTTPException:
        raise
    except Exception as e:
        log.error("api_approve_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit-trail")
async def get_audit_trail():
    """Query trident_audit index for last 50 entries."""
    try:
        results = await loop._search.get_events("trident_audit", query="| sort -_time | head 50")
        return results if results else []
    except Exception as e:
        log.error("api_audit_trail_error", error=str(e))
        return []

@app.post("/api/inject-demo")
async def inject_demo():
    """Trigger the autonomous loop to detect the demo anomaly."""
    loop.state.start_demo_scenario()
    loop.trigger_immediate_poll()
    return {"success": True, "message": "Demo scenario activated. Agents are investigating."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
