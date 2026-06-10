import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useApproval } from '../hooks/useApproval';

/**
 * Remediation action panel — shows 3 options with approve/reject buttons.
 * Confirmation step before execution via MCP Server.
 */
export default function RemediationPanel({ incident, onRemediationComplete }) {
  const { approveRemediation, rejectRemediation, approvalStatus } = useApproval();
  const [confirmingId, setConfirmingId] = useState(null);
  const [simulationStep, setSimulationStep] = useState(0);

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

  const handleConfirm = async (optionKey, actionIndex) => {
    setConfirmingId(null);
    setSimulationStep(1);
    
    // Orchestrate fake delay for video narration
    setTimeout(() => setSimulationStep(2), 1500);
    setTimeout(() => setSimulationStep(3), 3000);
    setTimeout(() => setSimulationStep(4), 4500);

    const success = await approveRemediation(optionKey, incident.incident_id, actionIndex);
    
    setTimeout(() => {
      setSimulationStep(0);
      if (success && onRemediationComplete) {
        onRemediationComplete(incident.incident_id);
      }
    }, 5500);
  };

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
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '4px', textDecoration: status === 'rejected' ? 'line-through' : 'none', opacity: status === 'rejected' ? 0.5 : 1 }}>
                    {option.action}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: status === 'rejected' ? 0.5 : 1 }}>
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
                  <span className="spin" style={{ display: 'inline-block', marginRight: '6px' }}>⟳</span>
                  Executing via MCP Server...
                </div>
              ) : status === 'completed' ? (
                <div style={{
                  padding: '8px',
                  background: 'rgba(0, 229, 204, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: '#00E5CC',
                  fontWeight: 'bold'
                }}>
                  ✓ Mitigation Applied
                </div>
              ) : status === 'rejected' ? (
                <div style={{
                  padding: '8px',
                  background: 'rgba(255, 45, 85, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  textAlign: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--accent-red)',
                }}>
                  ✗ Rejected by Analyst
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
                      onClick={() => handleConfirm(optionKey, index)}
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
                    disabled={incident.status === 'MITIGATED'}
                    style={{ opacity: incident.status === 'MITIGATED' ? 0.5 : 1 }}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn--outline"
                    onClick={() => rejectRemediation(optionKey)}
                    style={{ width: 'auto', flex: '0 0 auto', opacity: incident.status === 'MITIGATED' ? 0.5 : 1 }}
                    disabled={incident.status === 'MITIGATED'}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Remediation Execution Simulator Modal */}
      {simulationStep > 0 && createPortal(
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(2,5,10,0.85)', zIndex: 10000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)'
        }}>
          <div style={{
            background: 'var(--bg-panel)', width: '100%', maxWidth: '600px',
            borderRadius: '12px', border: '1px solid var(--border-medium)',
            display: 'flex', flexDirection: 'column', boxShadow: '0 0 50px rgba(0,229,204,0.1)',
            overflow: 'hidden', animation: 'modal-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
          }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', background: 'var(--bg-elevated)' }}>
              <span className="spin" style={{ color: 'var(--accent-teal)', marginRight: '12px', fontSize: '1.2rem' }}>⟳</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 600 }}>Agent Execution Terminal via MCP</span>
            </div>
            <div style={{ padding: '32px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.95rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ opacity: simulationStep >= 1 ? 1 : 0.3, transition: 'opacity 0.3s' }}>
                <span style={{ color: 'var(--accent-amber)' }}>[SYSTEM]</span> Connecting to Splunk MCP Server... {simulationStep > 1 && <span style={{ color: 'var(--accent-teal)' }}>[OK]</span>}
              </div>
              <div style={{ opacity: simulationStep >= 2 ? 1 : 0.3, transition: 'opacity 0.3s' }}>
                <span style={{ color: 'var(--accent-amber)' }}>[AGENT]</span> Executing autonomous resolution runbook... {simulationStep > 2 && <span style={{ color: 'var(--accent-teal)' }}>[OK]</span>}
              </div>
              <div style={{ opacity: simulationStep >= 3 ? 1 : 0.3, transition: 'opacity 0.3s' }}>
                <span style={{ color: 'var(--accent-amber)' }}>[AGENT]</span> Validating telemetry stabilization... {simulationStep > 3 && <span style={{ color: 'var(--accent-teal)' }}>[OK]</span>}
              </div>
              {simulationStep >= 4 && (
                <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(0, 229, 204, 0.1)', border: '1px solid var(--accent-teal)', borderRadius: '6px', color: 'var(--accent-teal)', textAlign: 'center', fontWeight: 'bold', fontSize: '1.1rem' }}>
                  ✓ MITIGATION SUCCESSFUL
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
