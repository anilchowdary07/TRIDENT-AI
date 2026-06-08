import { useState, useEffect } from 'react';

/**
 * Hook: polls for new incidents from the backend.
 * In demo mode, uses hardcoded demo data to showcase the UI.
 */

const DEMO_INCIDENTS = [
  {
    incident_id: 'TRIDENT-20260615-a1b2c3d4',
    timestamp: new Date().toISOString(),
    severity: 'CRITICAL',
    severity_score: 92,
    status: 'OPEN',
    title: 'Brute-force credential attack with concurrent latency anomaly on payments-api',
    executive_summary: 'A coordinated attack was detected targeting the payments API. Over 2,000 login attempts per minute originated from IP 203.0.113.45, coinciding with a 183% latency spike in the payments service. TRIDENT agents identified this as a multi-vector incident requiring immediate response.',
    technical_summary: 'CDTSM detected payments.latency_ms breaching the Q80 quantile band at T+43 minutes, with actual values reaching 340ms against a predicted upper bound of 156ms. Simultaneously, Foundation AI classified a brute-force attack (T1110) from 203.0.113.45 with 95% confidence. Platform Auditor identified a poorly optimized scheduled search consuming 103% estimated CPU, likely exacerbating the latency impact.',
    root_cause: 'Brute-force credential stuffing attack from 203.0.113.45 combined with resource-intensive scheduled search',
    contributing_factors: [
      'Poorly optimized "Flash Sale Revenue Dashboard" search consuming 103% CPU',
      'No rate limiting on /api/auth/login endpoint',
      'Insufficient indexer queue capacity during peak traffic',
    ],
    confidence: 0.92,
    attack_timeline: [
      { timestamp: '2026-06-15T03:31:00Z', event: 'Latency begins climbing: 120ms → 180ms', source: 'telemetry' },
      { timestamp: '2026-06-15T03:33:00Z', event: 'Brute-force attack starts from 203.0.113.45', source: 'security' },
      { timestamp: '2026-06-15T03:35:00Z', event: 'Jr-admin scheduled search spawns 400K events/call', source: 'platform' },
      { timestamp: '2026-06-15T03:38:00Z', event: 'CPU spikes to 94%, indexer queues filling', source: 'platform' },
      { timestamp: '2026-06-15T03:41:00Z', event: '12 successful login compromises detected', source: 'security' },
      { timestamp: '2026-06-15T03:43:00Z', event: 'CDTSM detects Q80 breach — TRIDENT triggered', source: 'telemetry' },
    ],
    mitre_techniques: [
      { id: 'T1110', name: 'Brute Force', tactic: 'Credential Access' },
      { id: 'T1078', name: 'Valid Accounts', tactic: 'Initial Access' },
    ],
    iocs: {
      ips: ['203.0.113.45'],
      domains: [],
      users: ['admin', 'deploy', 'service-account'],
    },
    affected_services: ['payments-api', 'auth-service', 'api-gateway', 'user-db'],
    blast_radius: '3,240 transactions affected in last 15 minutes',
    business_impact: '$180,000 / hour',
    remediation_options: [
      {
        priority: 1,
        action: 'Block source IP 203.0.113.45 via network ACL',
        rationale: 'Immediately stops the ongoing brute-force attack',
        risk_level: 'LOW',
        estimated_recovery_minutes: 2,
        requires_approval: true,
        mcp_tool_call: { tool: 'block_ip', args: { ip: '203.0.113.45' } },
      },
      {
        priority: 2,
        action: 'Disable compromised accounts and force password reset',
        rationale: '12 accounts may be compromised — disable to prevent lateral movement',
        risk_level: 'MEDIUM',
        estimated_recovery_minutes: 10,
        requires_approval: true,
        mcp_tool_call: { tool: 'disable_accounts', args: { users: ['admin', 'deploy', 'service-account'] } },
      },
      {
        priority: 3,
        action: 'Kill resource-intensive scheduled search "Flash Sale Revenue Dashboard"',
        rationale: 'Frees 103% CPU load, should reduce latency by 40-60%',
        risk_level: 'LOW',
        estimated_recovery_minutes: 1,
        requires_approval: true,
        mcp_tool_call: { tool: 'cancel_search', args: { title: 'Flash Sale - Realtime Revenue Dashboard' } },
      },
    ],
    agent_trace: {
      telemetry_sentinel: {
        agent_name: 'TelemetrySentinel',
        status: 'COMPLETE',
        anomaly_detected: true,
        anomaly_severity: 2.84,
        metric_name: 'payments.latency_ms',
        duration_seconds: 3.2,
      },
      threat_marshall: {
        agent_name: 'ThreatMarshall',
        status: 'COMPLETE',
        threat_type: 'BruteForce',
        confidence_score: 0.95,
        ioc_list: ['203.0.113.45'],
        mitre_techniques: ['T1110', 'T1078'],
        duration_seconds: 5.1,
      },
      platform_auditor: {
        agent_name: 'PlatformAuditor',
        status: 'COMPLETE',
        heavy_searches: [{ title: 'Flash Sale - Realtime Revenue Dashboard', cpu_estimate: 103.5 }],
        queue_warnings: [{ queue_name: 'parsingQueue', avg_fill_kb: 7840.5 }],
        duration_seconds: 2.8,
      },
    },
  },
  {
    incident_id: 'TRIDENT-20260615-e5f6g7h8',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    severity: 'HIGH',
    severity_score: 78,
    status: 'OPEN',
    title: 'Unusual data exfiltration pattern detected from internal database cluster',
    executive_summary: 'Anomalous outbound data transfer detected from the user-db cluster. Transfer volume exceeded normal baseline by 340%, suggesting potential data exfiltration.',
    technical_summary: 'Foundation AI detected outbound data patterns matching T1041 (Exfiltration Over C2 Channel).',
    root_cause: 'Unauthorized bulk data export via compromised service account',
    contributing_factors: ['Excessive service account permissions', 'No DLP controls on database egress'],
    confidence: 0.78,
    attack_timeline: [
      { timestamp: '2026-06-15T02:15:00Z', event: 'Unusual query volume on user-db', source: 'telemetry' },
      { timestamp: '2026-06-15T02:22:00Z', event: 'Large outbound data transfer detected', source: 'security' },
    ],
    mitre_techniques: [
      { id: 'T1041', name: 'Exfiltration Over C2 Channel', tactic: 'Exfiltration' },
      { id: 'T1005', name: 'Data from Local System', tactic: 'Collection' },
    ],
    iocs: { ips: ['198.51.100.23'], domains: ['suspicious-cdn.example.com'], users: ['db-backup-svc'] },
    affected_services: ['user-db', 'data-pipeline'],
    blast_radius: '~50,000 user records potentially exposed',
    business_impact: '$2.1M estimated if breach confirmed',
    remediation_options: [
      {
        priority: 1,
        action: 'Isolate user-db from external network',
        rationale: 'Stops ongoing data transfer immediately',
        risk_level: 'MEDIUM',
        estimated_recovery_minutes: 5,
        requires_approval: true,
      },
    ],
    agent_trace: {
      telemetry_sentinel: { status: 'COMPLETE', anomaly_detected: true },
      threat_marshall: { status: 'COMPLETE', threat_type: 'Exfiltration', confidence_score: 0.78 },
      platform_auditor: { status: 'COMPLETE', platform_healthy: true },
    },
  },
  {
    incident_id: 'TRIDENT-20260614-i9j0k1l2',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    severity: 'MEDIUM',
    severity_score: 55,
    status: 'OPEN',
    title: 'API error rate anomaly — checkout service returning elevated 500 errors',
    executive_summary: 'The checkout service error rate increased from 0.5% to 8.2% over the last 30 minutes. No security threat detected — likely a deployment issue.',
    technical_summary: 'CDTSM flagged api.error_rate breaching Q80 band. Platform Auditor detected a recent configuration change to outputs.conf.',
    root_cause: 'Recent configuration change causing misconfigured outputs',
    contributing_factors: [],
    confidence: 0.55,
    attack_timeline: [],
    mitre_techniques: [],
    iocs: { ips: [], domains: [], users: [] },
    affected_services: ['checkout-service'],
    blast_radius: '~120 failed checkouts in last 30 minutes',
    business_impact: '$12,000 / hour in lost revenue',
    remediation_options: [
      {
        priority: 1,
        action: 'Revert outputs.conf to previous version',
        rationale: 'Configuration change correlates with error spike',
        risk_level: 'LOW',
        estimated_recovery_minutes: 3,
        requires_approval: true,
      },
    ],
    agent_trace: {
      telemetry_sentinel: { status: 'COMPLETE', anomaly_detected: true },
      threat_marshall: { status: 'COMPLETE', threat_type: 'None' },
      platform_auditor: { status: 'COMPLETE', config_changes: [{ file: 'outputs.conf' }] },
    },
  },
];

export function useIncidents(pollInterval = 30000) {
  const [incidents, setIncidents] = useState(DEMO_INCIDENTS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // In a real deployment, this would poll the Splunk search endpoint
    // For now, use demo data
    setLoading(false);
  }, []);

  return { incidents, loading };
}
