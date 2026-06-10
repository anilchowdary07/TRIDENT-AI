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

function generateBezierPath(data, width, height) {
  if (!data || data.length === 0) return '';
  const xStep = width / Math.max(1, data.length - 1);
  const pts = data.map((v, i) => ({
    x: i * xStep,
    y: height - (v * height)
  }));
  
  let path = `M ${pts[0].x},${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const cp1x = p0.x + xStep / 2;
    const cp1y = p0.y;
    const cp2x = p1.x - xStep / 2;
    const cp2y = p1.y;
    path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p1.x},${p1.y}`;
  }
  return path;
}

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

      {/* Mini sparkline */}
      <div style={{
        marginTop: '8px',
        height: '24px',
        width: '100%',
      }}>
        <svg width="100%" height="100%" viewBox="0 0 100 24" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`sparkline-grad-${agent.agent_name}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={statusColor} stopOpacity="0.4" />
              <stop offset="100%" stopColor={statusColor} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d={generateBezierPath(agent.confidence_history || [0.3, 0.5, 0.4, 0.6, 0.3, 0.8, 0.4, 0.5, 0.7, 0.9], 100, 24) + ` L 100,24 L 0,24 Z`}
            fill={`url(#sparkline-grad-${agent.agent_name})`}
            stroke="none"
          />
          <path
            d={generateBezierPath(agent.confidence_history || [0.3, 0.5, 0.4, 0.6, 0.3, 0.8, 0.4, 0.5, 0.7, 0.9], 100, 24)}
            fill="none"
            stroke={statusColor}
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
}
