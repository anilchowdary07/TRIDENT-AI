import React from 'react';

/**
 * MCP JSON-RPC audit trail — bottom stream panel.
 * Shows timestamped tool calls with security violation highlighting.
 */

const DEMO_AUDIT = [
  { timestamp: new Date().toISOString(), rpc_id: 'rpc-a1b2c3', method: 'tools/list', status: 200, security_violation: false },
  { timestamp: new Date().toISOString(), rpc_id: 'rpc-d4e5f6', method: 'tools/call', status: 200, security_violation: false },
  { timestamp: new Date().toISOString(), rpc_id: 'rpc-g7h8i9', method: 'resources/read', status: 200, security_violation: false },
  { timestamp: new Date().toISOString(), rpc_id: 'rpc-j0k1l2', method: 'tools/call', status: 400, security_violation: true },
  { timestamp: new Date().toISOString(), rpc_id: 'rpc-m3n4o5', method: 'tools/call', status: 200, security_violation: false },
];

export default function AuditTrail() {
  const entries = DEMO_AUDIT;

  return (
    <div>
      <div className="section-header">
        <span className="section-header__label">MCP Audit Trail</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {entries.map((entry, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 8px',
              borderRadius: 'var(--radius-sm)',
              background: entry.security_violation
                ? 'rgba(255,45,85,0.08)'
                : 'transparent',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
            }}
          >
            <span style={{ color: 'var(--text-muted)', width: '60px', flexShrink: 0 }}>
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span style={{
              color: entry.security_violation ? 'var(--accent-red)' : 'var(--accent-teal)',
              width: '90px',
              flexShrink: 0,
            }}>
              {entry.method}
            </span>
            <span style={{
              color: entry.status >= 400 ? 'var(--accent-red)' : 'var(--text-muted)',
              width: '30px',
              flexShrink: 0,
            }}>
              {entry.status}
            </span>
            {entry.security_violation && (
              <span style={{
                background: 'var(--accent-red-dim)',
                color: 'var(--accent-red)',
                padding: '1px 6px',
                borderRadius: '3px',
                fontSize: '0.6rem',
                fontWeight: 700,
              }}>
                ⚠ INJECTION BLOCKED
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
