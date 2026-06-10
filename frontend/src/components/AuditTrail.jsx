import React from 'react';
import { useAuditTrail } from '../hooks/useAuditTrail';

/**
 * MCP JSON-RPC audit trail — bottom stream panel.
 * Shows timestamped tool calls with security violation highlighting.
 */

export default function AuditTrail() {
  const { auditLogs: entries } = useAuditTrail();

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
