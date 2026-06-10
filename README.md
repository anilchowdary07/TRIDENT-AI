<div align="center">
  <img src="./trident_logo.png" alt="TRIDENT-AI Logo" width="150">
  <h1>TRIDENT-AI</h1>
  <p><b>Autonomous Incident Intelligence & Remediation Swarm</b></p>
  <p><i>Splunk Hackathon 2026 Submission</i></p>
</div>

---

## 🏆 Hackathon Tracks: Observability, Security, & Platform DevEx
TRIDENT-AI is a unified, agentic swarm that spans all three Splunk Hackathon tracks:
1. **Observability:** Uses Splunk's CDTSM (Cisco Deep Time Series Model) to autonomously forecast and detect zero-shot metric anomalies in real-time.
2. **Security:** Autonomously correlates telemetry anomalies with security events, mapping active threats to the MITRE ATT&CK framework.
3. **Platform & DevEx:** Continuously audits Splunk's internal health (indexer queues, expensive scheduled searches) to ensure platform stability during a crisis, while leveraging the Model Context Protocol (MCP) to execute zero-touch remediations.

## 🚨 The Problem
SOC Analysts and Site Reliability Engineers (SREs) are drowning in alerts. When a P1 incident strikes at 3:00 AM, human operators waste the first 45 minutes manually cross-referencing dashboards, firewall logs, and infrastructure metrics just to figure out what is happening.

**The Business Impact:** A 45-minute delay during a peak traffic event can cost an enterprise upwards of **$180,000 per hour** in lost revenue and SLA penalties.

## 💡 Our Solution
**TRIDENT-AI** is an autonomous agentic swarm that investigates and resolves incidents before a human even wakes up. 

When a metric deviates from its predicted baseline, TRIDENT-AI awakens three distinct AI agents:
* **TelemetrySentinel:** Analyzes time-series data using CDTSM to quantify the exact severity of the anomaly.
* **ThreatMarshall:** Scours security indexes for concurrent IOCs and maps them to MITRE techniques.
* **PlatformAuditor:** Checks Splunk's internal health to ensure resource-hogging searches aren't exacerbating the outage.

The agents synthesize their findings via AWS Bedrock (Claude 3.5 Sonnet) into a pristine **Incident Package**, complete with a 1-click remediation runbook powered by the **Model Context Protocol (MCP)**. 

**Result:** A 45-minute manual investigation is reduced to a 3-minute, one-click autonomous resolution.

---

## 🛡️ Guardrails on MCP Remediations
Platform stability and safety are critical. TRIDENT-AI operates with strict execution guardrails:
* **Zero-Trust MCP Execution:** The Splunk MCP Server operates on a heavily restricted, read/write permission-scoped service account. 
* **Blast Radius Containment:** This strict scoping ensures that while `PlatformAuditor` can dynamically kill a runaway scheduled search, the agent can *never* accidentally drop an index, modify core network firewalls, or mutate critical security policies without explicit multi-factor analyst verification.

---

## 🏗️ Architecture & Component Breakdown

### 🤖 The Agent Swarm (Orchestrated via AWS Bedrock)
*   **TelemetrySentinel:** Executes periodic background queries using the Splunk Python SDK to pull high-cardinality metric streams. It passes these arrays into the **Cisco Deep Time Series Model (CDTSM)** to predict expected baselines and flag zero-shot anomalies ($>3\sigma$ deviations).
*   **ThreatMarshall:** When an anomaly is detected, this agent targets security indexes (e.g., `index=security` or `sourcetype=pan:traffic`), extracting concurrent Indicators of Compromise (IOCs) like spikes in 403 errors or unusual egress destinations, mapping them directly to **MITRE ATT&CK Matrix v14** techniques.
*   **PlatformAuditor:** Queries Splunk’s REST API (`| rest /services/search/jobs`) to evaluate ongoing indexing latency and locate expensive, unoptimized scheduled searches that might be compounding system instability during the crisis.

### 🔌 The Splunk MCP Server Integration
TRIDENT-AI implements an **MCP (Model Context Protocol)** server acting as a secure gateway between Claude 3.5 Sonnet and your infrastructure. The server exposes a restricted set of read/write schema tools to the LLM:
*   `get_search_results(query)`: Secure read-only access to specific Splunk indexes.
*   `terminate_splunk_job(sid)`: Allows `PlatformAuditor` to kill runaway searches.
*   `deploy_containment_rule(ip_address)`: Drafts a perimeter block rule for the engineer's 1-click approval.

---

## 🚀 Setup and Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Splunk Enterprise / Cloud (with Splunk AI Toolkit v5.7.3+)
- AWS Account (with `anthropic.claude-3-5-sonnet-v1:0` model access enabled in IAM)

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your_secure_password

AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

MCP_SERVER_PORT=5001
```

### 2. Running the Sandbox / Demo Mode (No Live Splunk Required)

If you do not have a live Splunk instance configured with CDTSM locally, you can test the entire agentic loop using our simulated event injector:

```bash
# Terminal 1: Start backend in Mock/Simulation Mode
python3 main.py --mode simulation

# Terminal 2: Start the React UI
cd frontend
npm run dev
```

*This bypasses live API calls and feeds `demo/sample_data/metrics.json` into the agent pipeline, allowing you to visualize the full multi-agent triage and MCP runbook generation on the frontend.*

Visit `http://localhost:3000`. Click **"Run Demo Scenario"** to inject a simulated multi-vector breach and watch the autonomous agents go to work!

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
# TRIDENT-AI
