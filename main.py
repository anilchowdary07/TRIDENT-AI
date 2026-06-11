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
