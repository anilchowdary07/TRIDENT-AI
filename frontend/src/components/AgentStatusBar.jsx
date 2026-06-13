import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';

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
  const [selectedAgent, setSelectedAgent] = useState(null);

  return (
    <div>
      <div className="section-header">
        <span className="section-header__label">Agent Status</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {agents.map((agent) => (
          <AgentCard key={agent.agent_name} agent={agent} onClick={() => setSelectedAgent(agent)} />
        ))}
      </div>

      {selectedAgent && createPortal(
        <AgentDetailsModal agent={selectedAgent} onClose={() => setSelectedAgent(null)} />,
        document.body
      )}
    </div>
  );
}

function AgentCard({ agent, onClick }) {
  const isInvestigating = agent.status === 'INVESTIGATING';
  const statusColor = STATUS_COLORS[agent.status] || 'var(--text-muted)';
  const icon = AGENT_ICONS[agent.agent_name] || '🔧';

  return (
    <div 
      className="glass-panel" 
      onClick={onClick}
      style={{
        padding: '12px',
        transition: 'all var(--transition-fast)',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.borderColor = statusColor;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.borderColor = 'var(--border-medium)';
      }}
    >
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

function AgentDetailsModal({ agent, onClose }) {
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const now = new Date();
    setCurrentTime(now.toISOString().slice(11, 19) + ' UTC');
  }, []);

  const mitigationLogs = {
    TelemetrySentinel: [
      { time: currentTime || '11:08:29 UTC', action: 'Recalibrated CDTSM quantile bands (+12%)' },
      { time: currentTime || '11:08:31 UTC', action: 'Updated baseline model parameters in ML-SPL' },
      { time: currentTime || '11:08:35 UTC', action: 'Verified traffic latency returning to nominal Q50 bounds' }
    ],
    ThreatMarshall: [
      { time: currentTime || '11:08:32 UTC', action: 'Executed MCP Command: AWS WAF IP Block (203.0.113.45)' },
      { time: currentTime || '11:08:33 UTC', action: 'Invalidated 1 active session token in identity provider' },
      { time: currentTime || '11:08:35 UTC', action: 'Forced password reset for user: admin_svc' },
      { time: currentTime || '11:08:38 UTC', action: 'Updated Splunk Security Essentials active blocklist' }
    ],
    PlatformAuditor: [
      { time: currentTime || '11:08:32 UTC', action: 'Executed MCP Command: Disabled scheduled search "Heavy_CPU_Report"' },
      { time: currentTime || '11:08:33 UTC', action: 'Flushed indexer queue (metrics_idx)' },
      { time: currentTime || '11:08:34 UTC', action: 'Restarted search peer worker thread' }
    ]
  };

  const logs = mitigationLogs[agent.agent_name] || [];

  return (
    <div 
      style={{ 
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
        background: 'rgba(2,5,10,0.85)', zIndex: 10000, 
        display: 'flex', alignItems: 'center', justifyContent: 'center', 
        backdropFilter: 'blur(8px)' 
      }} 
      onClick={onClose}
    >
      <div 
        style={{ 
          background: 'var(--bg-panel)', width: '100%', maxWidth: '600px', 
          borderRadius: '12px', border: '1px solid var(--border-medium)', 
          padding: '24px', animation: 'modal-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)' 
        }} 
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.5rem' }}>{AGENT_ICONS[agent.agent_name]}</span>
            <h3 style={{ margin: 0, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{agent.agent_name} Action Log</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.5rem' }}>&times;</button>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ color: 'var(--accent-teal)', fontSize: '0.85rem', fontWeight: 'bold', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
            RECENT MITIGATION ACTIONS (POST-APPROVAL):
          </div>
          <div style={{ background: 'var(--bg-elevated)', borderRadius: '6px', border: '1px solid var(--border-light)', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {logs.map((log, i) => (
              <div key={i} style={{ display: 'flex', gap: '16px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--accent-amber)', whiteSpace: 'nowrap' }}>[{log.time}]</span>
                <span style={{ color: 'var(--text-secondary)' }}>{log.action}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: '24px', textAlign: 'right' }}>
          <button className="btn btn--primary" onClick={onClose}>Close Log</button>
        </div>
      </div>
    </div>
  );
}
