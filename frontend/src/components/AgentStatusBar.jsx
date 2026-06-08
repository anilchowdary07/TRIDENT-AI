import React from 'react';

const STATUS_COLORS = {
  POLLING: 'var(--accent-teal)',
  TRIGGERED: 'var(--accent-amber)',
  INVESTIGATING: 'var(--accent-amber)',
  COMPLETE: 'var(--accent-teal)',
  ERROR: 'var(--accent-red)',
  IDLE: 'var(--text-muted)',
};

const AGENT_ICONS = {
  TelemetrySentinel: '📡',
  ThreatMarshall: '🛡️',
  PlatformAuditor: '🖥️',
};

/**
 * Agent Status Sidebar — shows live heartbeat of all 3 agents.
 * Pulsing ring animation when status is INVESTIGATING.
 */
export default function AgentStatusBar({ agents }) {
  return (
    <div>
      <div className="section-header">
        <span className="section-header__label">Agent Status</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {agents.map((agent) => (
          <AgentCard key={agent.agent_name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function AgentCard({ agent }) {
  const isInvestigating = agent.status === 'INVESTIGATING';
  const statusColor = STATUS_COLORS[agent.status] || 'var(--text-muted)';
  const icon = AGENT_ICONS[agent.agent_name] || '🔧';

  return (
    <div className="glass-panel" style={{
      padding: '12px',
      transition: 'all var(--transition-fast)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '1.2rem' }}>{icon}</span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
        }}>
          {agent.agent_name}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
        <div
          className={isInvestigating ? 'pulse-ring' : ''}
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: statusColor,
            boxShadow: `0 0 6px ${statusColor}`,
          }}
        />
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.65rem',
          fontWeight: 600,
          color: statusColor,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}>
          {agent.status}
        </span>
      </div>

      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '0.6rem',
        color: 'var(--text-muted)',
      }}>
        <div>Last poll: {agent.last_poll || '—'}</div>
        <div>Last anomaly: {agent.last_anomaly || '—'}</div>
      </div>

      {/* Mini sparkline placeholder */}
      <div style={{
        marginTop: '8px',
        height: '20px',
        display: 'flex',
        alignItems: 'flex-end',
        gap: '2px',
      }}>
        {(agent.confidence_history || [0.3, 0.5, 0.4, 0.6, 0.3, 0.8, 0.4, 0.5, 0.7, 0.9]).map((v, i) => (
          <div key={i} style={{
            flex: 1,
            height: `${v * 100}%`,
            background: v > 0.7 ? 'var(--accent-red)' : 'var(--accent-teal)',
            borderRadius: '1px',
            opacity: 0.6,
            transition: 'height 0.3s ease',
          }} />
        ))}
      </div>
    </div>
  );
}
