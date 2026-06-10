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
      {/* ─── Trident AI Synthesis Highlight ─── */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        gap: '16px', 
        marginBottom: '24px', 
        padding: '20px', 
        background: 'linear-gradient(180deg, var(--bg-elevated) 0%, rgba(0, 229, 204, 0.03) 100%)', 
        borderRadius: 'var(--radius-md)', 
        border: '1px solid var(--border-medium)',
        borderBottom: '2px solid var(--accent-teal)'
      }}>
        <div style={{textAlign: 'center', flex: 1}}>
           <div style={{fontSize: '1.8rem', filter: 'drop-shadow(0 0 8px var(--accent-teal-glow))'}}>📡</div>
           <div style={{fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)', marginTop: '8px', letterSpacing: '0.1em'}}>TELEMETRY</div>
        </div>
        
        <div style={{color: 'var(--text-muted)', fontSize: '1.2rem'}}>+</div>
        
        <div style={{textAlign: 'center', flex: 1}}>
           <div style={{fontSize: '1.8rem', filter: 'drop-shadow(0 0 8px var(--accent-red-glow))'}}>🛡️</div>
           <div style={{fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-red)', marginTop: '8px', letterSpacing: '0.1em'}}>SECURITY</div>
        </div>
        
        <div style={{color: 'var(--text-muted)', fontSize: '1.2rem'}}>+</div>
        
        <div style={{textAlign: 'center', flex: 1}}>
           <div style={{fontSize: '1.8rem', filter: 'drop-shadow(0 0 8px rgba(255, 140, 0, 0.4))'}}>🖥️</div>
           <div style={{fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)', marginTop: '8px', letterSpacing: '0.1em'}}>PLATFORM</div>
        </div>
        
        <div className="pulse-ring" style={{color: 'var(--accent-teal)', margin: '0 16px', fontSize: '1.5rem'}}>→</div>
        
        <div style={{
          textAlign: 'center', 
          background: 'rgba(0, 229, 204, 0.1)', 
          padding: '12px 24px', 
          borderRadius: 'var(--radius-sm)', 
          border: '1px solid var(--accent-teal)', 
          boxShadow: '0 0 20px var(--accent-teal-glow)',
          flex: 1.5
        }}>
           <div style={{fontSize: '2rem', color: '#00E5CC', filter: 'drop-shadow(0 0 12px var(--accent-teal-glow))'}}>🔱</div>
           <div style={{fontSize: '0.75rem', fontWeight: 'bold', fontFamily: 'var(--font-mono)', color: '#00E5CC', letterSpacing: '0.1em', marginTop: '6px'}}>TRIDENT AI SYNTHESIS</div>
        </div>
      </div>

      <div style={{ marginBottom: '12px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        Raw Reasoning Trace:
      </div>

      {/* ─── Collapsible Raw Traces ─── */}
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
