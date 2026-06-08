# TRIDENT-AI ⚡
### Zero-Touch Autonomous Incident Intelligence for the Modern Enterprise

> *"By the time your engineer opens their laptop, TRIDENT has already investigated
> the incident, mapped the attack chain, and queued the remediation — waiting for
> one click."*

---

## 🏆 Built for Splunk Agentic Ops Hackathon 2026

TRIDENT-AI is a production-grade autonomous incident intelligence system that detects, investigates, and packages complete incident reports — without any human trigger. Three autonomous agents form a unified strike force that continuously monitors your infrastructure, correlates threats across telemetry, security, and platform domains, and delivers analyst-ready incident packages in under 60 seconds.

---

## The Problem

Enterprise incidents cost businesses **$600 billion annually** in downtime. SOC teams face:
- **Alert fatigue**: 11,000+ alerts/day, 74% ignored
- **Fragmented telemetry**: metrics, security logs, and platform health in separate silos
- **Slow investigation**: 287 days average to identify and contain a breach (IBM 2025)
- **Manual correlation**: analysts manually connecting dots across 5+ tools

The result? Incidents are detected late, investigated slowly, and remediated inconsistently.

## The Solution

TRIDENT-AI eliminates the detection-to-remediation gap with **three autonomous agents** running continuously — no human trigger, no manual start:

```
┌─────────────────────────────────────────────────────────┐
│              AUTONOMOUS COORDINATOR (Python)             │
│   Background thread polls every 60s — NO HUMAN NEEDED   │
└──────────────┬──────────────────────────────────────────┘
               │  All agent calls via MCP Server
               ▼
┌──────────────┐ ┌──────────────┐ ┌─────────────┐
│  Telemetry   │ │   Threat     │ │  Platform   │
│  Sentinel    │ │  Marshall    │ │  Auditor    │
│  CDTSM       │ │ Foundation AI│ │  SPL-only   │
│  zero-shot   │ │ 8B security  │ │  lightweight│
└──────────────┘ └──────────────┘ └─────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│         AWS BEDROCK (Claude claude-sonnet-4-5)          │
│    Synthesizes all agent findings into complete          │
│    incident package with remediation options             │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│    TRIDENT DASHBOARD — Dark Ops Command Centre           │
│    One-click approve / modify / reject remediation       │
└─────────────────────────────────────────────────────────┘
```

## Three-Prong Architecture

### 🔱 Prong 1: Telemetry Sentinel (CDTSM)
Uses the **Cisco Deep Time Series Model** for zero-shot metric forecasting. Detects when actual values breach the [Q20, Q80] quantile band — no training data needed. Monitors latency, CPU, error rates, and request volumes across all services.

### 🔱 Prong 2: Threat Marshall (Foundation AI Security Model)
Uses the **Foundation AI Security Model (foundation-sec-1.1-8b-instruct)** for autonomous threat investigation. When triggered by a telemetry anomaly, analyses security logs to classify threats, extract IoCs, and map to MITRE ATT&CK techniques with confidence scoring.

### 🔱 Prong 3: Platform Auditor (SPL-native)
Lightweight SPL-only agent — no AI model required. Runs 3 parallel queries to detect CPU-hungry searches, configuration changes, and indexer queue congestion. Identifies when platform issues are contributing to the incident.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend coordinator | Python 3.11+, asyncio, threading |
| Splunk SDK | splunk-sdk (Python) |
| MCP Protocol | JSON-RPC 2.0 over HTTP/SSE |
| Time-series AI | Cisco Deep Time Series Model (CDTSM) via Splunk AI Toolkit |
| Security AI | Foundation AI Security Model (foundation-sec-1.1-8b-instruct) |
| Incident synthesis | AWS Bedrock — anthropic.claude-sonnet-4-5 |
| AWS SDK | boto3 |
| Frontend | React 18 + D3.js |
| Dashboard | Dashboard Studio 10.4 JSON |
| Data validation | pydantic v2 |
| Logging | structlog (JSON) |
| Testing | pytest, pytest-asyncio |

## Splunk Technologies Used

- **Splunk MCP Server** (App ID 7931, v1.2.0) — agent coordination backbone, JSON-RPC 2.0
- **Cisco Deep Time Series Model (CDTSM)** — zero-shot metric forecasting via AI Toolkit
- **Foundation AI Security Model** (foundation-sec-1.1-8b-instruct) — autonomous threat analysis
- **Splunk AI Toolkit** v5.7.3 — model inference layer for both CDTSM and Foundation AI
- **Dashboard Studio** 10.4 — HITL command console with token-driven panels
- **Splunk Python SDK** — backend coordinator for search execution and event writing
- **Splunk Technology Add-On for MCP** v0.1.2 — security audit layer for JSON-RPC validation

## AWS Bedrock Integration

Bedrock serves as the **incident synthesis layer only** — it does not replace Splunk's hosted models. After all 3 agents complete their investigations, their raw findings are sent to Claude claude-sonnet-4-5 via Bedrock to produce:
- Executive summary (non-technical, VP/CTO ready)
- Technical root cause analysis
- MITRE ATT&CK chain reconstruction
- Business impact estimation
- 3 prioritised remediation options with risk badges

## Human-in-the-Loop Design

TRIDENT agents **never act autonomously on irreversible actions**. The workflow:
1. Agents detect and investigate autonomously
2. Bedrock synthesises the incident package
3. Package appears in the dashboard queue
4. Analyst reviews and approves remediation with **one click**
5. Approved action executes via MCP Server tool call
6. Full audit trail logged for compliance

## Security Governance

Every MCP JSON-RPC call is:
- **Logged** with full request/response payloads for audit
- **Validated** for path traversal patterns (`../`)
- **Validated** for SQL injection patterns (`UNION SELECT`)
- **Validated** for prompt injection markers (`<|endoftext|>`)
- Any violation triggers a `CRITICAL` alert and blocks the response

## Demo Scenario

**Flash Sale at a Retail Company:**
1. Normal baseline: 120ms latency, 35% CPU, 50 req/sec
2. T+31min: Latency starts climbing, brute-force attack begins from `203.0.113.45`
3. T+35min: Jr-admin runs bad search consuming 103% CPU
4. T+43min: CDTSM detects Q80 breach → TRIDENT triggers all 3 agents
5. T+44min: Bedrock synthesises complete incident package
6. Dashboard shows: CRITICAL incident with 3 remediation options
7. Analyst clicks "Approve" → IP blocked via MCP in 2 seconds

## Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/anilchowdary07/TRIDENT-AI.git
cd TRIDENT-AI

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Splunk Cloud and AWS Bedrock credentials

# 4. Generate demo data
python demo/simulate_incident.py

# 5. Run in demo mode
DEMO_MODE=true python main.py

# 6. Install frontend
cd frontend && npm install && npm run dev
```

### Prerequisites
- Python 3.11+
- Node.js 18+
- Splunk Cloud trial with Developer License
- MCP Server (App ID 7931) installed from Splunkbase
- AWS account with Bedrock access (Claude claude-sonnet-4-5)

## Team

**TRIDENT-AI Team** — Built for the Splunk Agentic Ops Hackathon 2026

---

*TRIDENT-AI: Your incident is investigated, mapped, and solved before your engineer opens their laptop.* ⚡
