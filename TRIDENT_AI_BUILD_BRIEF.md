# TRIDENT-AI — Complete Build Brief for Claude Opus 4.6
> You are a senior full-stack engineer, Splunk architect, and AI systems designer.
> Your single objective: build TRIDENT-AI — a production-grade, autonomous incident
> intelligence system that wins the $7,000 Grand Prize at the Splunk Agentic Ops
> Hackathon 2026. Mediocre output is failure. Every file you write must be
> production-quality. Every UI component must be stunning. Every agent must be
> truly autonomous. Build as if $10,000 depends on every commit — because it does.

---

## 1. PROJECT IDENTITY

**Name:** TRIDENT-AI
**Tagline:** *"Your incident is investigated, mapped, and solved before your engineer opens their laptop."*
**GitHub:** https://github.com/anilchowdary07/TRIDENT-AI
**Competition:** Splunk Agentic Ops Hackathon 2026 (deadline June 15, 2026)
**Prize target:** Grand Prize ($7,000) + Best of Security ($3,000) + Best Use of MCP Server ($1,000) + Best Use of Hosted Models ($1,000) = $12,000 from one project

**What TRIDENT means:**
Three autonomous agents forming a unified strike force — like a trident's three prongs:
- **Prong 1 — Telemetry Sentinel:** Uses Cisco Deep Time Series Model (CDTSM) for zero-shot metric forecasting
- **Prong 2 — Threat Marshall:** Uses Foundation AI Security Model for autonomous threat investigation and MITRE ATT&CK mapping
- **Prong 3 — Platform Auditor:** Uses SPL to detect resource-hogging searches and deployment anomalies

**Core value:** The three agents run continuously with no human trigger. When they detect an incident, they autonomously investigate it, synthesize a complete incident package using AWS Bedrock, and push it to the analyst — who only needs to approve the final remediation with one click.

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│              AUTONOMOUS COORDINATOR (Mac/Python)         │
│   Background thread polls every 60s — NO HUMAN NEEDED   │
│   coordinator/autonomous_loop.py                        │
└──────────────┬─────────────────────────────────────────┘
               │  All agent calls via MCP Server
               ▼
┌─────────────────────────────────────────────────────────┐
│              SPLUNK CLOUD PLATFORM (browser-based)       │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         Splunk MCP Server (App ID 7931)          │    │
│  │  /services/mcp · JSON-RPC 2.0 · Token auth      │    │
│  └────────────┬────────────┬──────────────────┐    │    │
│               ▼            ▼                   ▼   │    │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │   │
│  │  Telemetry   │ │   Threat     │ │  Platform   │ │   │
│  │  Sentinel    │ │  Marshall    │ │  Auditor    │ │   │
│  │  CDTSM       │ │ Foundation AI│ │  SPL-only   │ │   │
│  │  zero-shot   │ │ 8B security  │ │  lightweight│ │   │
│  └──────────────┘ └──────────────┘ └─────────────┘ │   │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│         AWS BEDROCK (Claude claude-sonnet-4-5)          │
│    Synthesizes all agent findings into:                  │
│    · Executive summary · Root cause                      │
│    · MITRE ATT&CK chain · Business impact estimate       │
│    · 3 prioritised remediation options with risk badges  │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│    TRIDENT DASHBOARD (Splunk React App + Dashboard Studio)│
│    · Incident queue (agent-populated, human reads)       │
│    · Full incident package view                          │
│    · One-click approve / modify / reject                 │
│    · Agent reasoning trace panel                         │
│    · MCP audit trail (security validation)               │
└─────────────────────────────────────────────────────────┘
```

---

## 3. TECH STACK

| Layer | Technology |
|-------|-----------|
| Backend coordinator | Python 3.11+, asyncio, threading |
| Splunk SDK | splunk-sdk (Python) |
| MCP Protocol | JSON-RPC 2.0 over HTTP/SSE |
| Time-series AI | Cisco Deep Time Series Model (CDTSM) via Splunk AI Toolkit |
| Security AI | Foundation AI Security Model (foundation-sec-1.1-8b-instruct) via Splunk Hosted Models |
| Incident synthesis | AWS Bedrock — anthropic.claude-sonnet-4-5 |
| AWS SDK | boto3 |
| Frontend | Splunk React App (Splunk UI Toolkit + @splunk/react-ui components) |
| Visualisations | Dashboard Studio 10.4 JSON + Custom D3 network graph |
| Env management | python-dotenv |
| HTTP client | httpx (async) |
| Data validation | pydantic v2 |
| Logging | structlog |
| Testing | pytest, pytest-asyncio |

---

## 4. COMPLETE FILE STRUCTURE

Create every file listed below. Do not skip any.

```
TRIDENT-AI/
│
├── .env.example                   ← template (committed)
├── .env                           ← real credentials (gitignored)
├── .gitignore
├── README.md                      ← Devpost-quality README
├── requirements.txt
├── setup.cfg
├── pyproject.toml
├── Makefile                       ← dev shortcuts
│
├── src/
│   ├── __init__.py
│   │
│   ├── coordinator/
│   │   ├── __init__.py
│   │   ├── autonomous_loop.py     ← THE CORE — background polling thread
│   │   ├── incident_package.py   ← builds the complete incident report
│   │   ├── bedrock_client.py     ← AWS Bedrock integration
│   │   └── state_manager.py      ← tracks active incidents, cooldowns
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py         ← abstract base class
│   │   ├── telemetry_sentinel.py ← CDTSM forecasting agent
│   │   ├── threat_marshall.py    ← Foundation AI security agent
│   │   └── platform_auditor.py   ← SPL-based platform health agent
│   │
│   ├── splunk/
│   │   ├── __init__.py
│   │   ├── mcp_client.py         ← MCP Server JSON-RPC client
│   │   ├── search_client.py      ← SPL search execution
│   │   ├── hosted_models.py      ← CDTSM + Foundation AI wrappers
│   │   └── token_auth.py         ← Splunk token authentication
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── incident.py           ← Incident pydantic model
│   │   ├── agent_finding.py      ← Agent output pydantic models
│   │   └── remediation.py        ← Remediation option model
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py             ← loads .env variables
│       ├── logger.py             ← structured logging setup
│       └── mitre.py              ← MITRE ATT&CK technique lookup
│
├── splunk_app/                   ← the actual Splunk app package
│   ├── app.conf
│   ├── default/
│   │   ├── data/
│   │   │   └── ui/
│   │   │       ├── views/
│   │   │       │   ├── trident_dashboard.xml
│   │   │       │   └── audit_trail.xml
│   │   │       └── nav/
│   │   │           └── default.xml
│   │   ├── indexes.conf
│   │   ├── inputs.conf
│   │   ├── props.conf
│   │   ├── transforms.conf
│   │   └── savedsearches.conf
│   └── metadata/
│       └── default.meta
│
├── frontend/                     ← React Splunk app frontend
│   ├── package.json
│   ├── webpack.config.js
│   ├── src/
│   │   ├── index.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── IncidentQueue.jsx     ← the main incident list
│   │   │   ├── IncidentCard.jsx      ← individual incident card
│   │   │   ├── IncidentPackage.jsx   ← full detailed view
│   │   │   ├── AgentStatusBar.jsx    ← live agent health strip
│   │   │   ├── MitreTimeline.jsx     ← attack chain visualisation
│   │   │   ├── NetworkGraph.jsx      ← D3 force-directed graph
│   │   │   ├── RemediationPanel.jsx  ← approve/reject UI
│   │   │   ├── AuditTrail.jsx        ← MCP JSON-RPC audit log
│   │   │   └── AgentTrace.jsx        ← shows agent reasoning steps
│   │   ├── hooks/
│   │   │   ├── useIncidents.js       ← polls Splunk search for new incidents
│   │   │   ├── useAgentStatus.js     ← polls agent heartbeat
│   │   │   └── useApproval.js        ← handles approve/reject + MCP call
│   │   └── styles/
│   │       ├── global.css
│   │       ├── incident-queue.css
│   │       └── animations.css
│   └── public/
│       └── index.html
│
├── dashboards/                   ← Dashboard Studio JSON definitions
│   ├── trident_main.json
│   └── audit_security.json
│
├── demo/
│   ├── simulate_incident.py      ← injects realistic fake incident data
│   ├── generate_metrics.py       ← generates CDTSM-compatible time series
│   └── sample_data/
│       ├── metrics.json          ← 30-day metric history with anomaly spike
│       ├── security_logs.json    ← realistic brute-force attack logs
│       └── platform_data.json    ← Splunk internal performance data
│
├── tests/
│   ├── conftest.py
│   ├── test_autonomous_loop.py
│   ├── test_cdtsm_agent.py
│   ├── test_foundation_ai.py
│   ├── test_mcp_client.py
│   ├── test_incident_package.py
│   └── test_bedrock_synthesis.py
│
└── docs/
    ├── architecture.md
    ├── setup.md
    ├── demo_script.md             ← narrated demo script for video
    └── judging_criteria.md       ← maps every feature to a judging criterion
```

---

## 5. ENVIRONMENT VARIABLES (.env)

Create `.env.example` with exactly these keys (no values — user fills them):

```bash
# ─── SPLUNK CLOUD ──────────────────────────────────────
SPLUNK_HOST=your-instance.splunkcloud.com
SPLUNK_PORT=8089
SPLUNK_TOKEN=your-splunk-api-token-here
SPLUNK_INDEX=main
SPLUNK_APP=trident_ai
SPLUNK_VERIFY_SSL=true

# ─── SPLUNK MCP SERVER ─────────────────────────────────
# App ID 7931 — install from Splunkbase before running
MCP_BASE_URL=https://your-instance.splunkcloud.com:8089/services/mcp
MCP_PROTOCOL=sse

# ─── SPLUNK HOSTED MODELS ──────────────────────────────
# CDTSM — Cisco Deep Time Series Model (via Splunk AI Toolkit)
CDTSM_MODEL_NAME=cisco_ai_assistant
CDTSM_FORECAST_K=24
CDTSM_HOLDBACK=12
# NOTE: holdback + forecast_k MUST be <= 384 (hard limit)
CDTSM_QUANTILE_LOWER=0.20
CDTSM_QUANTILE_UPPER=0.80
CDTSM_MAX_DATAPOINTS=30000
CDTSM_METRICS_INDEX=metrics
CDTSM_METRICS_SOURCETYPE=aws:cloudwatch

# Foundation AI Security Model
FOUNDATION_AI_MODEL=foundation-sec-1.1-8b-instruct
SECURITY_LOGS_INDEX=main
SECURITY_SOURCETYPE=access_combined

# ─── AWS BEDROCK ────────────────────────────────────────
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5
BEDROCK_MAX_TOKENS=4096

# ─── AUTONOMOUS LOOP ────────────────────────────────────
POLL_INTERVAL_SECONDS=60
ANOMALY_COOLDOWN_SECONDS=300
# How far below the Q20 or above Q80 to trigger
ANOMALY_DEVIATION_THRESHOLD=1.5
MAX_INCIDENTS_IN_QUEUE=100

# ─── DEMO MODE ──────────────────────────────────────────
# Set DEMO_MODE=true to use local sample_data/ instead of live Splunk
DEMO_MODE=false
DEMO_DATA_PATH=./demo/sample_data/

# ─── LOGGING ────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Load ALL variables using `python-dotenv` in `src/utils/config.py`.
Never hardcode any credential anywhere in any file.
Any file that uses a credential must import from `config.py` only.

---

## 6. GIT INITIALISATION

After creating all files, run these exact git commands in the project root:

```bash
echo "# TRIDENT-AI" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/anilchowdary07/TRIDENT-AI.git
git push -u origin main
```

Then immediately create and commit a proper .gitignore that includes:
```
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
node_modules/
dist/
build/
*.egg-info/
.pytest_cache/
.venv/
venv/
*.log
*.sqlite
.coverage
htmlcov/
```

---

## 7. BACKEND: AUTONOMOUS COORDINATOR (DETAILED SPEC)

### 7.1 `src/coordinator/autonomous_loop.py`

This is the most important file in the project. It must:

```python
"""
AutonomousLoop — runs forever as a background daemon thread.
No human trigger. No manual start. It wakes, polls, decides, acts.

Every POLL_INTERVAL_SECONDS (default: 60) it:
1. Calls CDTSM via MCP Server for all configured metric streams
2. If any metric breaches [Q20, Q80] quantile band by ANOMALY_DEVIATION_THRESHOLD:
   a. Prevents re-triggering for ANOMALY_COOLDOWN_SECONDS
   b. Spawns concurrent investigation tasks for all 3 agents (asyncio.gather)
   c. Passes all agent findings to BedrockClient.synthesize_incident_package()
   d. Writes the complete IncidentPackage to Splunk index via search_client
   e. Logs the full agent trace for the audit trail
3. If no anomaly: logs heartbeat and sleeps
"""
```

**Key requirements for this file:**
- Use `threading.Thread(daemon=True)` for the outer loop
- Use `asyncio.run()` inside the thread for async agent calls
- Use `asyncio.gather()` to run all 3 agents in parallel (not sequential)
- Implement exponential backoff for failed Splunk API calls
- Implement a cooldown tracker so one anomaly doesn't flood the incident queue
- Emit structured logs at every decision point (what was detected, what triggered, what was skipped)
- Handle ALL exceptions gracefully — a crash in one agent must never kill the loop

### 7.2 `src/agents/telemetry_sentinel.py`

Implements the CDTSM zero-shot forecasting. Key logic:

```python
"""
Uses the Cisco Deep Time Series Model to forecast metric streams.

CDTSM API call via Splunk AI Toolkit:
    | inputlookup <metric_series>
    | apply cdtsm 
      holdback=<CDTSM_HOLDBACK>
      forecast_k=<CDTSM_FORECAST_K>
      quantiles=[0.2, 0.5, 0.8]

CRITICAL CONSTRAINT: holdback + forecast_k <= 384 (enforced in code with assertion)

Returns:
    - forecast_band: {lower: Q20 values, upper: Q80 values}
    - anomaly_detected: bool
    - anomaly_severity: float (how far outside the band)
    - anomaly_timestamp: datetime
    - metric_name: str
    - actual_vs_forecast: dict
"""
```

Build the SPL query programmatically. Use the Splunk Python SDK to execute it.
Parse the result rows and extract the quantile columns.
Return a typed `AgentFinding` pydantic model.

### 7.3 `src/agents/threat_marshall.py`

Implements Foundation AI Security Model integration:

```python
"""
When triggered by TelemetrySentinel anomaly, queries security logs
and sends them to Foundation AI Security Model for analysis.

Foundation AI model: foundation-sec-1.1-8b-instruct
Accessed via: Splunk AI Toolkit's | apply command or REST API

SPL workflow:
    index=<SECURITY_LOGS_INDEX> sourcetype=<SECURITY_SOURCETYPE>
    earliest=-15m
    | eval log_text = _raw
    | apply foundation-sec-1.1-8b-instruct
      field=log_text
      task="threat_classification"

Expected outputs from Foundation AI:
    - threat_type: (BruteForce | Exfiltration | Injection | Reconnaissance | PrivilegeEscalation | None)
    - confidence_score: float 0.0-1.0
    - attack_timeline: list of timestamped events
    - ioc_list: [IP addresses, domains, user agents flagged as malicious]
    - mitre_techniques: list of T-codes (e.g. ["T1110", "T1078"])
    - affected_users: list of usernames targeted
    - narrative: str — 2-paragraph human-readable investigation summary

If confidence_score < 0.4: return NO_THREAT finding
If confidence_score >= 0.7: return HIGH_CONFIDENCE_THREAT finding
"""
```

### 7.4 `src/agents/platform_auditor.py`

Lightweight SPL-only agent, no AI model required:

```python
"""
Runs 3 SPL queries in parallel:

Query 1 — CPU-hungry scheduled searches:
    | rest /services/search/jobs
    | where dispatchState="RUNNING" AND runDuration > 300
    | eval cpu_estimate = (scanCount / 1000000) * 2.3
    | where cpu_estimate > 80
    | table title, owner, runDuration, cpu_estimate

Query 2 — Deployment changes in last 60 minutes:
    index=_internal sourcetype=splunkd
    earliest=-60m
    (props.conf OR transforms.conf OR inputs.conf OR outputs.conf)
    | stats count by host, file, action, user
    | where count > 0

Query 3 — Indexer queue fill rate warning:
    index=_internal sourcetype=metrics group=queue
    earliest=-5m
    | stats avg(current_size_kb) as avg_fill by name
    | where avg_fill > 5000

Returns PlatformFinding with: heavy_searches, config_changes, queue_warnings
"""
```

### 7.5 `src/coordinator/incident_package.py`

The crown jewel. Builds the complete incident report:

```python
"""
Takes findings from all 3 agents and synthesises them via AWS Bedrock.

The Bedrock prompt must request a structured JSON response containing:
{
  "incident_id": "TRIDENT-<YYYYMMDD>-<UUID4[:8]>",
  "timestamp": "ISO8601",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "severity_score": 0-100,
  "title": "one-sentence incident title",
  "executive_summary": "2-3 sentences, non-technical, suitable for VP/CTO",
  "technical_summary": "detailed technical root cause paragraph",
  "root_cause": "single most likely root cause",
  "contributing_factors": ["factor1", "factor2"],
  "attack_timeline": [
    {"timestamp": "...", "event": "...", "source": "telemetry|security|platform"}
  ],
  "mitre_techniques": [
    {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}
  ],
  "iocs": {"ips": [], "domains": [], "users": []},
  "affected_services": ["payments-api", "auth-service"],
  "blast_radius": "estimated number of affected users/transactions",
  "business_impact": "$ estimate of loss per hour at current rate",
  "remediation_options": [
    {
      "priority": 1,
      "action": "Block source IP 203.0.113.45 via Cisco ISE",
      "rationale": "...",
      "risk_level": "LOW",
      "estimated_recovery_minutes": 2,
      "requires_approval": true,
      "mcp_tool_call": {"tool": "block_ip", "args": {"ip": "203.0.113.45"}}
    }
  ],
  "confidence": 0.0-1.0,
  "agent_trace": {
    "telemetry_sentinel": { ... raw finding ... },
    "threat_marshall": { ... raw finding ... },
    "platform_auditor": { ... raw finding ... }
  }
}

After synthesis, write this JSON to Splunk index 'trident_incidents'
using a one-shot HTTP POST to /services/receivers/simple.
"""
```

### 7.6 `src/coordinator/bedrock_client.py`

```python
"""
Wraps AWS Bedrock API calls.

Model: anthropic.claude-sonnet-4-5 (via Bedrock)
Client: boto3.client('bedrock-runtime', region_name=AWS_REGION)

Critical: always include in the system prompt:
  "You are a security incident analyst. Respond ONLY with valid JSON.
   No preamble, no explanation, no markdown code blocks. Raw JSON only."

Use invoke_model() not converse() for reliability.
Parse response['body'].read() → json.loads() → validate with IncidentPackage pydantic model.
On JSON parse error: retry once with a more explicit prompt.
On Bedrock throttling: exponential backoff, max 3 retries.
"""
```

### 7.7 `src/splunk/mcp_client.py`

```python
"""
JSON-RPC 2.0 client for Splunk MCP Server.

Base URL: MCP_BASE_URL from config (e.g. https://host:8089/services/mcp)
Auth: Authorization: Bearer <SPLUNK_TOKEN>
Content-Type: application/json

Implement these methods:
- list_tools() → dict of available MCP tools
- call_tool(tool_name: str, arguments: dict) → tool result
- list_resources() → dict of available resources
- read_resource(uri: str) → resource content

All calls use httpx.AsyncClient with timeout=30s.
All calls log the full JSON-RPC request AND response to structlog.
This logging is what feeds the MCP Security Audit Trail.

Implement security validation on every response:
- Check for path traversal patterns (../ or ..\)
- Check for SQL injection patterns (union select, drop table, etc.)
- Check for prompt injection markers (<|endoftext|>, <|system|>, etc.)
- If any pattern found: raise SecurityViolationError and log CRITICAL alert
"""
```

---

## 8. FRONTEND: PREMIUM SPLUNK REACT APP (DETAILED SPEC)

This is where you win the demo. The UI must be extraordinary.

### 8.1 Design Direction

**Aesthetic:** "Dark Ops Command Centre" — the look of a real enterprise SOC war room.
- Deep black backgrounds (`#080B0F`) with cool graphite panels (`#0E1318`)
- Primary accent: Electric teal (`#00E5CC`) for active/healthy states
- Alert accent: Burning amber (`#FF8C00`) for warnings
- Critical accent: Plasma red (`#FF2D55`) for critical incidents
- Typography: `IBM Plex Mono` for data/metrics, `Inter` for UI text
- All data panels use subtle glass-morphism: `backdrop-filter: blur(8px)` with `rgba(255,255,255,0.03)` borders
- Micro-animations on every state change — not decorative, functional (they signal that data just updated)
- Animated pulse rings on agent status indicators
- Smooth horizontal slide-in for new incidents entering the queue
- No rounded corners over 6px — this is precision tooling, not a consumer app

### 8.2 `frontend/src/App.jsx`

The root layout. Three columns:
- **Left column (240px):** Agent status sidebar — shows live heartbeat of all 3 agents
- **Centre column (flex-grow):** Incident queue and selected incident package
- **Right column (320px):** Remediation action panel and MCP audit stream

Header: `TRIDENT-AI` logo (stylised trident icon in SVG), `AUTONOMOUS MODE: ACTIVE` badge with pulsing green dot, current time in UTC, alert count badge.

### 8.3 `frontend/src/components/AgentStatusBar.jsx`

Shows real-time status of each of the 3 agents. For each agent:
- Name + icon (use lucide-react or custom SVG)
- Status badge: `POLLING` / `TRIGGERED` / `INVESTIGATING` / `COMPLETE` / `ERROR`
- Last poll timestamp
- Pulsing ring animation when status is `INVESTIGATING`
- Last anomaly detected time
- A mini sparkline of the last 10 CDTSM confidence scores

### 8.4 `frontend/src/components/IncidentQueue.jsx`

The main incident list. Requirements:
- Each incident renders as a `IncidentCard` component
- New incidents slide in from the top with smooth CSS animation (`transform: translateY(-20px)` → `0` with `opacity 0` → `1`)
- Sorted by severity score descending
- Severity colour coded: CRITICAL=red, HIGH=amber, MEDIUM=teal, LOW=grey
- Each card shows: incident ID, title, severity badge, time ago, top 2 MITRE techniques
- Unacknowledged incidents have a pulsing left border
- Clicking a card sets it as the selected incident and renders `IncidentPackage`
- Empty state: animated trident logo with text "Agents watching. All systems nominal."

### 8.5 `frontend/src/components/IncidentPackage.jsx`

THE most important component. This is what judges will screenshot. Render the complete incident package in a scrollable right panel:

**Section 1: Incident Header**
- Large severity badge (CRITICAL / HIGH etc) with glow effect
- Incident title in large `IBM Plex Mono`
- Timestamp + incident ID
- Confidence score as a circular gauge (0-100)

**Section 2: Executive Summary**
- Clean sans-serif text box
- Labelled "EXECUTIVE SUMMARY — ready to send to leadership"

**Section 3: MITRE ATT&CK Chain**
- Render `MitreTimeline.jsx` — a horizontal attack chain diagram
- Each node is a MITRE tactic phase (Reconnaissance → Initial Access → Execution → Persistence → etc)
- Highlighted nodes show which tactics were detected
- Each highlighted node shows the T-code and technique name on hover
- This is a custom SVG/D3 component — make it visually impressive

**Section 4: Attack Timeline**
- Vertical timeline with timestamps
- Each event colour-coded by source (teal=observability, red=security, amber=platform)
- Icons for each event type

**Section 5: Affected Services**
- Render `NetworkGraph.jsx` — a D3 force-directed graph
- Nodes: microservices, database, external IPs, users
- Node colour = health status (green → red)
- Edge width = traffic volume / impact severity
- Clicking a node shows its current metric values in a tooltip

**Section 6: Business Impact**
- Big number: "Estimated loss rate: $180,000 / hour"
- Blast radius: "3,240 transactions affected in last 15 minutes"

**Section 7: Agent Reasoning Trace**
- Collapsible sections for each agent
- Shows exact inputs and outputs from each agent call
- Shows the MCP tool calls that were made
- This is the transparency / trust section

### 8.6 `frontend/src/components/RemediationPanel.jsx`

Right-side panel. Shows 3 remediation options from the incident package.

For each option:
- Priority number (1, 2, 3) in large bold
- Action description
- Risk level badge: LOW (green) / MEDIUM (amber) / HIGH (red)
- Estimated recovery time
- `Approve` button: teal, full width, with confirmation step ("Are you sure? This will execute via MCP Server")
- `Reject` button: outlined, smaller
- Approved items get a checkmark + "Executing..." → "Completed" state

On approval:
1. Call the backend `POST /api/approve-remediation` endpoint
2. Backend calls the appropriate MCP tool
3. Update incident status to `REMEDIATING` → `RESOLVED`
4. Show a live activity log of the MCP execution

### 8.7 `frontend/src/components/AuditTrail.jsx`

Bottom strip or collapsible panel. Shows real-time stream of MCP JSON-RPC calls:
- Each call shows: timestamp, tool name, arguments (truncated), result status (200/400/etc)
- Security violations highlighted in red with `⚠ INJECTION BLOCKED` badge
- This proves to judges that every agent action is logged and validated

---

## 9. DASHBOARD STUDIO JSON — `dashboards/trident_main.json`

Build a complete Dashboard Studio 10.4 JSON definition with these panels:

**Panel 1: CDTSM Forecasting Chart**
- Line chart with `acceleratedRender: true`
- Three lines: actual metric, Q20 lower band (shaded area fill), Q80 upper band
- The shaded area between Q20 and Q80 is the "breathing zone"
- When actual line goes outside the band: change colour to red, add annotation marker
- Time range: last 4 hours
- Token: `$selected_metric$` controls which metric is shown

**Panel 2: Network Topology Graph**
- Custom visualisation using D3.js within Dashboard Studio sandbox
- Force-directed layout
- Nodes: each microservice, database cluster, external connections
- Node colour changes dynamically based on `$health_state$` token
- Edge width scales with `$traffic_volume$` token
- Clicking node sets `$selected_service$` token, updating other panels

**Panel 3: Incident Queue Table**
- Table visualisation
- SPL: `index=trident_incidents | sort -severity_score | head 20`
- Colour-coded severity column
- Clicking a row sets `$selected_incident_id$` token

**Panel 4: Incident Detail (token-driven)**
- Only visible when `$selected_incident_id$` is set:
  `"visibility": "$selected_incident_id$"`
- Shows executive_summary, title, timestamp from the selected incident JSON
- Uses `spath` SPL command to extract nested JSON fields

**Panel 5: Remediation Action Panel**
- Only visible when `$selected_incident_id$` is set
- Shows 3 remediation buttons with confirmation dialog
- Each button sets `$pending_action$` token
- Confirmation dialog checks `$pending_action$` is not empty before showing

**Panel 6: MCP Audit View**
- Shows last 50 MCP JSON-RPC calls from the audit index
- Highlights any rows where `security_violation=true`
- Uses the Splunk Technology Add-On for MCP (version 0.1.2) fields

---

## 10. DEMO SIMULATION — `demo/simulate_incident.py`

Build a script that injects a realistic multi-domain incident into Splunk:

**The scenario:** Flash sale at a retail company.

**Phase 1 — Normal (first 30 minutes of data):**
- Steady transaction latency: ~120ms average
- Normal login activity: ~50 req/sec
- CPU at 35% average

**Phase 2 — Incident begins (T+31 minutes):**
- Latency starts climbing: 120ms → 180ms → 340ms over 12 minutes
- A brute-force attack starts from IP `203.0.113.45` with 2,000 login attempts/minute
- A junior admin runs a poorly written scheduled search that spawns 400,000 events/call
- CPU spikes to 94%

**Phase 3 — CDTSM detects breach:**
- At T+43 minutes, actual latency crosses Q80 band
- TelemetrySentinel triggers investigation
- All 3 agents run in parallel

**Phase 4 — Incident package generated:**
- Bedrock synthesises findings in under 30 seconds
- Package written to `trident_incidents` index
- Dashboard queue populates automatically

**Data format for injected metrics (feed to CDTSM):**
```json
{
  "time": "2026-06-15T03:47:23Z",
  "metric": "payments.latency_ms",
  "value": 340.5,
  "host": "payments-api-02",
  "region": "us-east-1"
}
```

**Security logs (for Foundation AI):**
```
203.0.113.45 - - [15/Jun/2026:03:48:01 +0000] "POST /api/auth/login HTTP/1.1" 401 127 "-" "python-requests/2.28.0"
203.0.113.45 - - [15/Jun/2026:03:48:02 +0000] "POST /api/auth/login HTTP/1.1" 401 127 "-" "python-requests/2.28.0"
[repeat 2000 times over 1 minute, with 12 successful 200 responses scattered in]
```

The simulate_incident.py script must:
1. Generate 30 days of normal baseline metric data (for CDTSM context)
2. Generate the incident spike
3. Generate realistic security logs
4. POST all of it to Splunk via HTTP Event Collector (HEC)
5. Print progress and confirmation

---

## 11. SPLUNK APP CONFIGURATION — `splunk_app/`

### `app.conf`
```ini
[launcher]
author=TRIDENT-AI Team
description=Autonomous AI-powered incident intelligence using CDTSM, Foundation AI Security Model, and Splunk MCP Server
version=1.0.0

[ui]
is_visible=1
label=TRIDENT-AI

[package]
id=trident_ai
```

### `default/indexes.conf`
```ini
[trident_incidents]
homePath = $SPLUNK_DB/trident_incidents/db
coldPath = $SPLUNK_DB/trident_incidents/colddb
thawedPath = $SPLUNK_DB/trident_incidents/thaweddb
maxDataSize = 5000

[trident_audit]
homePath = $SPLUNK_DB/trident_audit/db
coldPath = $SPLUNK_DB/trident_audit/colddb
thawedPath = $SPLUNK_DB/trident_audit/thaweddb
maxDataSize = 1000
```

### `default/savedsearches.conf`
Include these saved searches:
1. `TRIDENT - Active Incidents Alert` — real-time alert when new incident in queue
2. `TRIDENT - CDTSM Anomaly Detection` — scheduled every 1 min
3. `TRIDENT - MCP Security Audit` — real-time monitoring of JSON-RPC validation
4. `TRIDENT - Platform Health Baseline` — hourly platform metrics

---

## 12. DEVPOST README — `README.md`

Write a full Devpost-quality README. Include ALL of these sections:

### README Structure:

```markdown
# TRIDENT-AI ⚡
### Zero-Touch Autonomous Incident Intelligence for the Modern Enterprise

> *"By the time your engineer opens their laptop, TRIDENT has already investigated 
> the incident, mapped the attack chain, and queued the remediation — waiting for 
> one click."*

## 🏆 Built for Splunk Agentic Ops Hackathon 2026

## The Problem
[Explain the $600B enterprise downtime problem, alert fatigue, fragmented telemetry]

## The Solution
[Explain the three-prong autonomous approach]

## How It Works
[Architecture diagram — ASCII art or embedded image]

## Three-Prong Architecture
### Prong 1: Telemetry Sentinel (CDTSM)
### Prong 2: Threat Marshall (Foundation AI Security Model)  
### Prong 3: Platform Auditor (SPL-native)

## Tech Stack
[Full table]

## Splunk Technologies Used
- Splunk MCP Server (App ID 7931, v1.2.0) — agent coordination backbone
- Cisco Deep Time Series Model (CDTSM) — zero-shot metric forecasting
- Foundation AI Security Model (foundation-sec-1.1-8b-instruct) — autonomous threat analysis
- Splunk AI Toolkit v5.7.3 — model inference layer
- Dashboard Studio 10.4 — HITL command console
- Splunk Python SDK — backend coordinator
- Splunk Technology Add-On for MCP v0.1.2 — security audit layer

## AWS Bedrock Integration
[Explain role as incident synthesis layer only — not replacing Splunk models]

## Human-in-the-Loop Design
[Explain the approve/reject workflow and why agents never act autonomously on irreversible actions]

## Security Governance
[Explain MCP JSON-RPC validation, injection detection, audit trail]

## Demo Scenario
[Describe the flash sale incident simulation]

## Setup Instructions
[Step-by-step: Splunk Cloud trial → Developer License → MCP Server install → .env setup → run coordinator]

## Team
[Author info]
```

---

## 13. QUALITY STANDARDS — NON-NEGOTIABLE

Every single one of these must be true before the project is considered "done":

**Code quality:**
- Zero hardcoded credentials anywhere
- Every function has a docstring explaining what it does, inputs, and outputs
- All async functions use proper `async/await` patterns
- All HTTP calls have timeouts set
- All external API calls have retry logic with exponential backoff
- `pydantic` models validate all data at boundaries
- `structlog` structured logging at every significant action

**UI quality:**
- The dashboard must look like a commercial product, not a hackathon prototype
- Every interactive element has hover and active states
- Loading states for all async operations (skeleton screens, not spinners)
- Empty states designed (not just blank panels)
- Error states designed (not just console errors)
- Responsive to different screen widths (minimum 1280px to 2560px)
- All text is readable — minimum 13px, WCAG AA contrast ratios

**Demo quality:**
- The demo MUST show the autonomous loop catching an incident WITHOUT the user touching anything
- The incident package MUST look like a professional analyst wrote it
- The remediation approval MUST be one click with confirmation
- The MCP audit trail MUST show real JSON-RPC entries

**Documentation quality:**
- `docs/setup.md` must be so clear that a stranger can set this up from scratch
- `docs/demo_script.md` must be a narrated, timestamped script for the 5-minute demo video
- Every Splunk technology used must be named by exact version number

---

## 14. EXECUTION ORDER

Build in this exact order to avoid blocking dependencies:

1. `src/utils/config.py` — loads .env, must work before anything else
2. `src/utils/logger.py` — structured logging, needed by all modules
3. `src/splunk/token_auth.py` — auth layer
4. `src/splunk/search_client.py` — SPL execution
5. `src/splunk/mcp_client.py` — MCP JSON-RPC client
6. `src/splunk/hosted_models.py` — CDTSM + Foundation AI wrappers
7. `src/models/` — all pydantic models
8. `src/agents/base_agent.py` — abstract base
9. `src/agents/platform_auditor.py` — simplest agent, validate the full pipeline
10. `src/agents/telemetry_sentinel.py` — CDTSM integration
11. `src/agents/threat_marshall.py` — Foundation AI integration
12. `src/coordinator/bedrock_client.py` — Bedrock synthesis
13. `src/coordinator/incident_package.py` — builds the report
14. `src/coordinator/state_manager.py` — tracks cooldowns
15. `src/coordinator/autonomous_loop.py` — the main loop
16. `demo/simulate_incident.py` — test data injection
17. `splunk_app/` — all Splunk app config files
18. `dashboards/trident_main.json` — Dashboard Studio configuration
19. `frontend/` — React app (build last, when backend is confirmed working)
20. `tests/` — test files for each module
21. `docs/` — all documentation
22. Git initialisation and first commit

---

## 15. FINAL CHECKLIST BEFORE SUBMISSION

- [ ] `python main.py` starts the autonomous loop without errors
- [ ] `demo/simulate_incident.py` successfully injects data to Splunk
- [ ] Loop detects the anomaly within 2 poll cycles (max 2 minutes)
- [ ] All 3 agents run and return findings
- [ ] Bedrock synthesises a complete incident package
- [ ] Package appears in Dashboard Studio incident queue
- [ ] Remediation approval executes the MCP tool call
- [ ] MCP audit trail shows all JSON-RPC entries
- [ ] Security validation catches a simulated injection attempt
- [ ] React frontend renders correctly in Chrome
- [ ] Demo video is exactly 4-5 minutes
- [ ] README is complete on Devpost
- [ ] GitHub repo has clean commit history
- [ ] App is submitted on Devpost before June 15, 2026 midnight

---

## WHAT WINNING LOOKS LIKE

When a judge reviews TRIDENT-AI, they must feel this in this exact order:

1. **Surprise** — "The agents detected this before anyone opened a laptop?"
2. **Respect** — "This is using CDTSM and Foundation AI exactly as intended"
3. **Delight** — "This dashboard looks like an actual product"
4. **Trust** — "The MCP audit trail proves every action was logged and validated"
5. **Desire** — "I wish I had this at my company right now"

If your output produces these five feelings in a Splunk engineer judge, TRIDENT-AI wins.

Build accordingly.
