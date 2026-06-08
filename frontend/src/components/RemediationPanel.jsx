import React, { useState } from 'react';
import { useApproval } from '../hooks/useApproval';

/**
 * Remediation action panel — shows 3 options with approve/reject buttons.
 * Confirmation step before execution via MCP Server.
 */
export default function RemediationPanel({ incident }) {
  const { approveRemediation, approvalStatus } = useApproval();
  const [confirmingId, setConfirmingId] = useState(null);

  if (!incident) {
    return (
      <div>
        <div className="section-header">
          <span className="section-header__label">Remediation</span>
        </div>
        <div style={{
          padding: '20px',
          textAlign: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
        }}>
          Select an incident to view remediation options
        </div>
      </div>
    );
  }

  const options = incident.remediation_options || [];

  return (
    <div>
      <div className="section-header">
        <span className="section-header__label">Remediation Options</span>
      </div>

      {options.length === 0 && (
        <div style={{
          padding: '12px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
        }}>
          No remediation options available.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {options.map((option, index) => {
          const optionKey = `${incident.incident_id}-${option.priority || index}`;
          const status = approvalStatus[optionKey];
          const isConfirming = confirmingId === optionKey;
          const riskLevel = (option.risk_level || 'MEDIUM').toLowerCase();

          return (
            <div key={optionKey} className="glass-panel" style={{ padding: '12px' }}>
              {/* Priority number */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                marginBottom: '8px',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '1.3rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  lineHeight: 1,
                }}>
                  {option.priority || index + 1}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {option.action}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`risk-badge risk-badge--${riskLevel}`}>
                      {option.risk_level || 'MEDIUM'}
                    </span>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.65rem',
                      color: 'var(--text-muted)',
                    }}>
                      ~{option.estimated_recovery_minutes || '?'}min recovery
                    </span>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              {status === 'approved' ? (
                <div style={{
                  padding: '8px',
                  background: 'var(--accent-teal-dim)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--accent-teal)',
                }}>
                  ✓ Approved — Executing via MCP Server...
                </div>
              ) : status === 'completed' ? (
                <div style={{
                  padding: '8px',
                  background: 'var(--accent-teal-dim)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--accent-teal)',
                }}>
                  ✓ Completed
                </div>
              ) : isConfirming ? (
                <div>
                  <p style={{
                    fontSize: '0.75rem',
                    color: 'var(--accent-amber)',
                    marginBottom: '8px',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    ⚠ Are you sure? This will execute via MCP Server.
                  </p>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      className="btn btn--primary"
                      onClick={() => {
                        approveRemediation(optionKey, option);
                        setConfirmingId(null);
                      }}
                    >
                      Confirm Execution
                    </button>
                    <button
                      className="btn btn--outline"
                      onClick={() => setConfirmingId(null)}
                      style={{ width: 'auto' }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    className="btn btn--primary"
                    onClick={() => setConfirmingId(optionKey)}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn--outline"
                    style={{ width: 'auto', flex: '0 0 auto' }}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
