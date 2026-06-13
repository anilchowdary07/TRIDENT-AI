# TRIDENT-AI Architecture

## System Overview

TRIDENT-AI is an autonomous incident intelligence system with three coordinating layers:

1. **Detection Layer** — ML-SPL predict (Telemetry Sentinel) continuously forecasts metrics
2. **Investigation Layer** — All 3 agents run in parallel via `asyncio.gather()`
3. **Synthesis Layer** — AWS Bedrock Claude produces structured incident packages
4. **Presentation Layer** — React dashboard + Dashboard Studio for HITL remediation

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Entry Point)                    │
│   Starts AutonomousLoop in daemon thread                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              AutonomousLoop (coordinator/)                    │
│   ├── StateManager — cooldowns, active incidents             │
│   ├── TelemetrySentinel — ML-SPL predict anomaly detection   │
│   ├── ThreatMarshall — Security log retrieval                │
│   ├── PlatformAuditor — SPL platform health queries          │
│   ├── IncidentPackageBuilder — Bedrock synthesis             │
│   └── BedrockClient — AWS API wrapper                        │
└────────────────────────┬────────────────────────────────────┘
                         │ via
┌────────────────────────▼────────────────────────────────────┐
│              Splunk Integration Layer (splunk/)              │
│   ├── SplunkAuth — token + password dual auth                │
│   ├── SearchClient — async SPL execution                     │
│   ├── MCPClient — JSON-RPC 2.0 with security validation      │
│   └── HostedModels — ML-SPL wrappers                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Data Models (models/)                           │
│   ├── IncidentPackage — complete incident report             │
│   ├── AgentFinding — typed agent outputs                     │
│   └── RemediationOption — action with MCP tool call spec     │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Poll**: AutonomousLoop wakes every 60 seconds
2. **Detect**: TelemetrySentinel checks ML-SPL predict quantile bands
3. **Gate**: StateManager checks cooldown and queue capacity
4. **Investigate**: `asyncio.gather()` runs all 3 agents in parallel
5. **Synthesize**: BedrockClient sends findings to Claude claude-sonnet-4-5
6. **Validate**: IncidentPackage pydantic model validates the response
7. **Store**: SearchClient writes to `trident_incidents` Splunk index
8. **Display**: Dashboard polls for new incidents every 30 seconds
9. **Remediate**: Analyst approves → MCPClient executes tool call

## Security Architecture

- All MCP responses validated for: path traversal, SQL injection, prompt injection
- All JSON-RPC calls logged to `trident_audit` index
- No credentials hardcoded — all from `.env` via pydantic settings
- Exponential backoff on all external API calls
- Agent crashes isolated — one failure never kills the loop
