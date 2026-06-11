import React from 'react';
import MitreTimeline from './MitreTimeline';
import NetworkGraph from './NetworkGraph';
import AgentTrace from './AgentTrace';
import TelemetryChart from './TelemetryChart';

/**
 * THE most important component — the full incident package view.
 * 7 sections: Header, Executive Summary, MITRE Chain, Timeline,
 * Affected Services, Business Impact, Agent Trace.
 */
export default function IncidentPackage({ incident, onBack }) {
  const [showRawLogs, setShowRawLogs] = React.useState(false);

  if (!incident) return null;

  const isMitigated = incident.status === 'MITIGATED';
  const severity = isMitigated ? 'low' : (incident.severity || 'MEDIUM').toLowerCase();

  return (
    <div className={`incident-package fade-in ${isMitigated ? 'package-mitigated' : ''}`} style={{
      position: 'relative',
      borderRadius: '8px',
      transition: 'all 0.5s ease',
      ...(isMitigated ? {
        boxShadow: '0 0 40px rgba(0, 229, 204, 0.1)',
        border: '1px solid rgba(0, 229, 204, 0.3)'
      } : {})
    }}>
      {/* Mitigated Overlay Effect */}
      {isMitigated && (
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'linear-gradient(180deg, rgba(0, 229, 204, 0.05) 0%, transparent 100%)',
          pointerEvents: 'none',
          borderRadius: '8px',
          zIndex: 1
        }} />
      )}

      {/* Back button */}
      <button
        className="btn btn--outline"
        onClick={onBack}
        style={{ marginBottom: '16px', width: 'auto', padding: '6px 12px', position: 'relative', zIndex: 2 }}
      >
        ← Back to Queue
      </button>

      {/* ─── Section 1: Incident Header ─────────────────────────── */}
      <div className="incident-package__header" style={{ position: 'relative', zIndex: 2 }}>
        <div className="incident-package__severity">
          {isMitigated ? (
            <div className="severity-large" style={{
              background: 'rgba(0, 229, 204, 0.2)',
              color: '#00E5CC',
              border: '1px solid rgba(0, 229, 204, 0.5)',
              boxShadow: '0 0 16px rgba(0, 229, 204, 0.3)'
            }}>
              MITIGATED
            </div>
          ) : (
            <div className={`severity-large severity-badge--${severity} ${severity === 'critical' ? 'glow-critical' : ''}`}>
              {incident.severity}
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          <div className="incident-package__title" style={{
            color: isMitigated ? '#E8ECF4' : undefined,
            textDecoration: isMitigated ? 'line-through' : 'none',
            opacity: isMitigated ? 0.7 : 1
          }}>{incident.title}</div>
          <div className="incident-package__meta">
            {incident.incident_id} · {incident.timestamp}
          </div>
        </div>
        <div style={{ opacity: isMitigated ? 0.5 : 1, transition: 'opacity 0.5s' }}>
          <ConfidenceGauge value={Math.round((incident.confidence || 0) * 100)} />
        </div>
      </div>

      <div style={{ position: 'relative', zIndex: 2 }}>
        {/* ─── Section 2: Executive Summary ───────────────────────── */}
        <div className="package-section">
          <div className="package-section__label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Executive Summary — ready to send to leadership</span>
            <button className="btn btn--outline" onClick={() => setShowRawLogs(true)} style={{ fontSize: '10px', padding: '4px 8px', borderColor: 'var(--accent-teal)', color: 'var(--accent-teal)' }}>
              View Raw Logs
            </button>
          </div>
          <div className="package-section__content">
            {incident.executive_summary || 'No executive summary available.'}
          </div>
        </div>

        {/* ─── Section 3: Telemetry Forecast ────────────────────── */}
        <div className="package-section">
          <div className="package-section__label">TELEMETRY FORECAST — CDTSM QUANTILE BAND</div>
          <TelemetryChart 
            telemetryData={incident.agent_trace?.telemetry_sentinel} 
            timeline={incident.attack_timeline}
          />
        </div>

        {/* ─── Section 4: MITRE ATT&CK Chain ──────────────────────── */}
        {incident.mitre_techniques && incident.mitre_techniques.length > 0 && (
          <div className="package-section">
            <div className="package-section__label">MITRE ATT&CK Chain</div>
            <MitreTimeline techniques={incident.mitre_techniques} />
          </div>
        )}

        {/* ─── Section 5: Attack Timeline ─────────────────────────── */}
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

        {/* ─── Section 6: Affected Services ───────────────────────── */}
        {incident.affected_services && incident.affected_services.length > 0 && (
          <div className="package-section">
            <div className="package-section__label">Service Impact Map</div>
            <NetworkGraph services={incident.affected_services} iocs={incident.iocs} />
          </div>
        )}

        {/* ─── Section 7: Business Impact ─────────────────────────── */}
        <div className="package-section">
          <div className="package-section__label">Business Impact</div>
          <div className="impact-numbers">
            <div className="impact-number">
              <div className="impact-number__value" style={{ color: isMitigated ? '#00E5CC' : undefined }}>
                {isMitigated ? '$0 / hour (RESOLVED)' : (incident.business_impact || '$0 / hour')}
              </div>
              <div className="impact-number__label">Estimated loss rate</div>
            </div>
            <div className="impact-number">
              <div className="impact-number__value" style={{ color: isMitigated ? '#00E5CC' : 'var(--accent-amber)' }}>
                {incident.blast_radius || 'Unknown'}
              </div>
              <div className="impact-number__label">Blast radius</div>
            </div>
          </div>
        </div>

        {/* ─── Section 8: Technical Summary ───────────────────────── */}
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

        {/* ─── Section 9: Agent Reasoning Trace ───────────────────── */}
        <div className="package-section">
          <div className="package-section__label">Agent Reasoning Trace</div>
          <AgentTrace trace={incident.agent_trace} />
        </div>
      </div>

      {/* Raw Log Inspector Modal */}
      {showRawLogs && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            background: 'var(--bg-panel)', width: '80%', height: '80%',
            borderRadius: '12px', border: '1px solid var(--border-medium)',
            display: 'flex', flexDirection: 'column', boxShadow: '0 20px 40px rgba(0,0,0,0.5)'
          }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)' }}>Raw Evidence Inspector</span>
              <button className="btn btn--outline" onClick={() => setShowRawLogs(false)} style={{ padding: '4px 12px' }}>Close</button>
            </div>
            <div style={{ flex: 1, overflow: 'auto', padding: '16px', backgroundColor: 'var(--bg-deep)' }}>
              <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#a8b2c1', margin: 0 }}>
                {JSON.stringify(incident.agent_trace || { status: 'No raw data available' }, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Circular confidence gauge */
function ConfidenceGauge({ value }) {
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 75 ? 'var(--accent-teal)' : value >= 50 ? 'var(--accent-amber)' : 'var(--accent-red)';

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
      <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span className="confidence-gauge__value" style={{ color, lineHeight: 1 }}>
          {value}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>CONFIDENCE</span>
      </div>
    </div>
  );
}
