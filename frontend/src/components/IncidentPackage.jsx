import React from 'react';
import MitreTimeline from './MitreTimeline';
import NetworkGraph from './NetworkGraph';
import AgentTrace from './AgentTrace';

/**
 * THE most important component — the full incident package view.
 * 7 sections: Header, Executive Summary, MITRE Chain, Timeline,
 * Affected Services, Business Impact, Agent Trace.
 */
export default function IncidentPackage({ incident, onBack }) {
  if (!incident) return null;

  const severity = (incident.severity || 'MEDIUM').toLowerCase();

  return (
    <div className="incident-package fade-in">
      {/* Back button */}
      <button
        className="btn btn--outline"
        onClick={onBack}
        style={{ marginBottom: '16px', width: 'auto', padding: '6px 12px' }}
      >
        ← Back to Queue
      </button>

      {/* ─── Section 1: Incident Header ─────────────────────────── */}
      <div className="incident-package__header">
        <div className="incident-package__severity">
          <div className={`severity-large severity-badge--${severity} ${severity === 'critical' ? 'glow-critical' : ''}`}>
            {incident.severity}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div className="incident-package__title">{incident.title}</div>
          <div className="incident-package__meta">
            {incident.incident_id} · {incident.timestamp}
          </div>
        </div>
        <ConfidenceGauge value={Math.round((incident.confidence || 0) * 100)} />
      </div>

      {/* ─── Section 2: Executive Summary ───────────────────────── */}
      <div className="package-section">
        <div className="package-section__label">Executive Summary — ready to send to leadership</div>
        <div className="package-section__content">
          {incident.executive_summary || 'No executive summary available.'}
        </div>
      </div>

      {/* ─── Section 3: MITRE ATT&CK Chain ──────────────────────── */}
      {incident.mitre_techniques && incident.mitre_techniques.length > 0 && (
        <div className="package-section">
          <div className="package-section__label">MITRE ATT&CK Chain</div>
          <MitreTimeline techniques={incident.mitre_techniques} />
        </div>
      )}

      {/* ─── Section 4: Attack Timeline ─────────────────────────── */}
      {incident.attack_timeline && incident.attack_timeline.length > 0 && (
        <div className="package-section">
          <div className="package-section__label">Attack Timeline</div>
          <div className="timeline">
            {incident.attack_timeline.slice(0, 10).map((event, i) => (
              <div key={i} className={`timeline__event timeline__event--${event.source || 'telemetry'}`}>
                <div className="timeline__event__time">{event.timestamp}</div>
                <div className="timeline__event__text">{event.event}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Section 5: Affected Services ───────────────────────── */}
      {incident.affected_services && incident.affected_services.length > 0 && (
        <div className="package-section">
          <div className="package-section__label">Service Impact Map</div>
          <NetworkGraph services={incident.affected_services} iocs={incident.iocs} />
        </div>
      )}

      {/* ─── Section 6: Business Impact ─────────────────────────── */}
      <div className="package-section">
        <div className="package-section__label">Business Impact</div>
        <div className="impact-numbers">
          <div className="impact-number">
            <div className="impact-number__value">
              {incident.business_impact || '$0 / hour'}
            </div>
            <div className="impact-number__label">Estimated loss rate</div>
          </div>
          <div className="impact-number">
            <div className="impact-number__value" style={{ color: 'var(--accent-amber)' }}>
              {incident.blast_radius || 'Unknown'}
            </div>
            <div className="impact-number__label">Blast radius</div>
          </div>
        </div>
      </div>

      {/* ─── Section 7: Technical Summary ───────────────────────── */}
      <div className="package-section">
        <div className="package-section__label">Technical Root Cause</div>
        <div className="package-section__content">
          {incident.technical_summary || incident.root_cause || 'Analysis pending.'}
        </div>
        {incident.contributing_factors && incident.contributing_factors.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Contributing factors:
            </span>
            <ul style={{ paddingLeft: '16px', marginTop: '4px' }}>
              {incident.contributing_factors.map((f, i) => (
                <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{f}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* ─── Section 8: Agent Reasoning Trace ───────────────────── */}
      <div className="package-section">
        <div className="package-section__label">Agent Reasoning Trace</div>
        <AgentTrace trace={incident.agent_trace} />
      </div>
    </div>
  );
}

/** Circular confidence gauge */
function ConfidenceGauge({ value }) {
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 70 ? 'var(--accent-red)' : value >= 40 ? 'var(--accent-amber)' : 'var(--accent-teal)';

  return (
    <div className="confidence-gauge">
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={radius} fill="none" stroke="var(--border-light)" strokeWidth="4" />
        <circle
          cx="32" cy="32" r={radius} fill="none"
          stroke={color} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 32 32)"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <span className="confidence-gauge__value" style={{ position: 'absolute', color }}>
        {value}
      </span>
    </div>
  );
}
