# TRIDENT-AI Demo Script

## Video Duration: 4-5 minutes

---

### [0:00 - 0:20] Opening Hook

**Script:**
> "What if your incident was investigated, mapped, and solved before your engineer even opens their laptop? This is TRIDENT-AI — autonomous incident intelligence for the modern enterprise."

**Visual:** Show the TRIDENT-AI dashboard in "All systems nominal" state — the trident icon floating, agents showing "POLLING" status with green dots.

---

### [0:20 - 0:50] The Problem

**Script:**
> "Enterprise SOC teams face 11,000 alerts per day. 74% are ignored. The average breach takes 287 days to identify. TRIDENT-AI eliminates this gap with three autonomous agents that detect, investigate, and package incidents — with zero human trigger."

**Visual:** Show a simplified architecture diagram highlighting the three prongs.

---

### [0:50 - 1:30] Architecture Walkthrough

**Script:**
> "TRIDENT uses three autonomous agents:
> - Prong 1: The Telemetry Sentinel uses Cisco's Deep Time Series Model for zero-shot metric forecasting. No training data needed.
> - Prong 2: The Threat Marshall uses Foundation AI's 8-billion parameter security model for autonomous threat classification and MITRE ATT&CK mapping.
> - Prong 3: The Platform Auditor runs lightweight SPL queries to detect resource issues.
>
> These agents run in parallel via asyncio.gather — not sequentially. When CDTSM detects an anomaly, all three investigate simultaneously."

**Visual:** Show the agent status sidebar with all 3 agents. Highlight the MCP Server as the coordination backbone.

---

### [1:30 - 2:30] Live Demo — Incident Detection

**Script:**
> "Let's watch TRIDENT detect a real incident. We've simulated a flash sale scenario: normal traffic for 30 minutes, then a brute-force attack begins from IP 203.0.113.45 — 2,000 login attempts per minute — while a junior admin runs a poorly written search consuming 103% CPU."

**Visual:**
1. Show the terminal: `python main.py` running with structured log output
2. Point to "poll_cycle_start" logs showing the 60-second polling
3. Watch for "anomaly_detected_investigating" log entry
4. Show "all_agents_complete" — all 3 finished in parallel

> "The CDTSM model detected the latency breach at T+43 minutes. All three agents investigated in parallel — total investigation time: 5.1 seconds. Bedrock synthesised the incident package in under 30 seconds."

---

### [2:30 - 3:30] Dashboard Walkthrough

**Script:**
> "Here's what the analyst sees — no setup, no query writing, no manual investigation."

**Visual:** Walk through the incident package view:
1. **Severity badge**: "CRITICAL" with glow effect
2. **Executive Summary**: "Ready to send to leadership"
3. **MITRE ATT&CK Chain**: Highlight T1110 (Brute Force) and T1078 (Valid Accounts) in the horizontal timeline
4. **Attack Timeline**: Show the 6 events colour-coded by source
5. **Network Graph**: Show the D3 force-directed graph with affected services
6. **Business Impact**: "$180,000 / hour" in large text
7. **Agent Trace**: Open one collapsible to show raw agent output

---

### [3:30 - 4:10] One-Click Remediation

**Script:**
> "The analyst has three remediation options, prioritised by AI:
> 1. Block the attack IP — LOW risk, 2 minutes to recover
> 2. Disable compromised accounts — MEDIUM risk
> 3. Kill the resource-intensive search — LOW risk
>
> One click. Confirmation step. MCP Server executes the tool call."

**Visual:**
1. Click "Approve" on option 1
2. Show confirmation dialog: "Are you sure? This will execute via MCP Server"
3. Click "Confirm Execution"
4. Show "Executing..." → "Completed" state transition

---

### [4:10 - 4:40] Security & Audit Trail

**Script:**
> "Every MCP tool call is logged in the audit trail — timestamp, method, arguments, result status. And every response is validated for path traversal, SQL injection, and prompt injection. Watch what happens when we simulate an injection attempt."

**Visual:** Show the audit trail panel with green "CLEAN" entries and one red "⚠ INJECTION BLOCKED" entry.

---

### [4:40 - 5:00] Closing

**Script:**
> "TRIDENT-AI: three autonomous agents, zero human trigger, complete incident packages in under 60 seconds. The incident is investigated, mapped, and solved — before your engineer opens their laptop."

**Visual:** Return to the dashboard showing all systems nominal with the pulsing green "AUTONOMOUS MODE: ACTIVE" badge.

---

## Key Talking Points

- **Autonomous**: No human trigger — the loop runs continuously
- **Parallel**: All 3 agents run via `asyncio.gather()`, not sequentially
- **CDTSM**: Zero-shot forecasting — no training data needed
- **Foundation AI**: 8B parameter security model for real threat analysis
- **MCP Server**: Every agent action audited via JSON-RPC
- **One-click**: Human-in-the-loop for irreversible actions only
- **Production-grade**: Pydantic validation, structlog, exponential backoff, crash isolation
