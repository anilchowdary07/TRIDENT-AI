# TRIDENT-AI — Judging Criteria Mapping

## How TRIDENT-AI maps to every judging criterion

---

### 🏆  Criteria

| Criterion | TRIDENT-AI Implementation |
|-----------|---------------------------|
| **Innovation** | Three autonomous agents with zero-shot CDTSM forecasting — no training data, no human trigger |
| **Technical Complexity** | asyncio.gather() parallel agents, MCP JSON-RPC, Bedrock synthesis, D3 network graphs |
| **Practical Value** | Reduces MTTR from hours to seconds. $600B enterprise downtime problem |
| **Completeness** | Full pipeline: detection → investigation → synthesis → remediation → audit |
| **Polish** | Dark Ops Command Centre UI, comprehensive docs, demo simulation 

---

### 🛡️  Security

| Criterion | TRIDENT-AI Implementation |
|-----------|---------------------------|
| **Foundation AI Usage** | Threat Marshall uses `foundation-sec-1.1-8b-instruct` for autonomous threat classification |
| **MITRE ATT&CK Mapping** | Automatic T-code extraction and kill chain visualization |
| **IoC Extraction** | IPs, domains, user agents extracted from security logs |
| **Security Validation** | MCP response validation for path traversal, SQLi, prompt injection |
| **Audit Trail** | Every JSON-RPC call logged with full request/response payloads |

---

### 🔌  MCP Server

| Criterion | TRIDENT-AI Implementation |
|-----------|---------------------------|
| **MCP Integration** | JSON-RPC 2.0 client with `list_tools()`, `call_tool()`, `list_resources()`, `read_resource()` |
| **Agent Coordination** | All agent searches and actions flow through MCP Server |
| **Security** | 3-layer response validation (path traversal, SQLi, prompt injection) |
| **Audit** | Complete JSON-RPC audit trail in `trident_audit` index |
| **Remediation** | One-click approve triggers MCP tool call execution |

---

### 🤖  Hosted Models

| Criterion | TRIDENT-AI Implementation |
|-----------|---------------------------|
| **CDTSM** | Zero-shot metric forecasting with quantile bands, no training data required |
| **Foundation AI** | Autonomous threat classification, confidence scoring, narrative generation |
| **Correct Usage** | Both models accessed via Splunk AI Toolkit `\| apply` command |
| **Hard Limits** | CDTSM holdback + forecast_k ≤ 384 enforced in code with assertion |
| **Integration** | Models feed into Bedrock synthesis for cross-domain correlation |

---

### Splunk Technology Versions Used

| Technology | Version | Usage |
|-----------|---------|-------|
| Splunk MCP Server | App ID 7931, v1.2.0 | Agent coordination, JSON-RPC 2.0 |
| CDTSM | via AI Toolkit | Zero-shot metric forecasting |
| Foundation AI | foundation-sec-1.1-8b-instruct | Threat classification |
| Splunk AI Toolkit | v5.7.3 | Model inference layer |
| Dashboard Studio | 10.4 | HITL command console |
| Splunk Python SDK | ≥2.0.1 | Backend coordinator |
| Splunk TA for MCP | v0.1.2 | Security audit layer |

---

