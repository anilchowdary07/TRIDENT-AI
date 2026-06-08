import React, { useState } from 'react';

/**
 * Agent Reasoning Trace — collapsible sections showing exact I/O from each agent.
 * This is the transparency/trust section for judges.
 */
export default function AgentTrace({ trace }) {
  if (!trace) return null;

  const agents = [
    { key: 'telemetry_sentinel', name: 'Telemetry Sentinel', icon: '📡', color: 'var(--accent-teal)' },
    { key: 'threat_marshall', name: 'Threat Marshall', icon: '🛡️', color: 'var(--accent-red)' },
    { key: 'platform_auditor', name: 'Platform Auditor', icon: '🖥️', color: 'var(--accent-amber)' },
  ];

  return (
    <div>
      {agents.map(agent => (
        <TraceSection
          key={agent.key}
          title={`${agent.icon} ${agent.name}`}
          data={trace[agent.key]}
          color={agent.color}
        />
      ))}
    </div>
  );
}

function TraceSection({ title, data, color }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!data || Object.keys(data).length === 0) return null;

  return (
    <div className="collapsible">
      <div
        className="collapsible__header"
        onClick={() => setIsOpen(!isOpen)}
        style={{ borderLeft: `3px solid ${color}` }}
      >
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
        }}>
          {title}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          transform: isOpen ? 'rotate(90deg)' : 'none',
          transition: 'transform 0.2s ease',
        }}>
          ▶
        </span>
      </div>
      {isOpen && (
        <div className="collapsible__body fade-in">
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.7rem',
            color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: '300px',
            overflow: 'auto',
            lineHeight: 1.5,
          }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
