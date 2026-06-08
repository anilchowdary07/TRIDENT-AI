import React, { useState } from 'react';
import AgentStatusBar from './components/AgentStatusBar';
import IncidentQueue from './components/IncidentQueue';
import IncidentPackage from './components/IncidentPackage';
import RemediationPanel from './components/RemediationPanel';
import AuditTrail from './components/AuditTrail';
import { useIncidents } from './hooks/useIncidents';
import { useAgentStatus } from './hooks/useAgentStatus';

/* ─── SVG Trident Icon ───────────────────────────────────────────── */
const TridentIcon = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="16" y1="4" x2="16" y2="28" />
    <line x1="16" y1="4" x2="8" y2="12" />
    <line x1="16" y1="4" x2="24" y2="12" />
    <line x1="8" y1="12" x2="8" y2="16" />
    <line x1="24" y1="12" x2="24" y2="16" />
    <circle cx="16" cy="4" r="1.5" fill="currentColor" />
    <circle cx="8" cy="16" r="1.5" fill="currentColor" />
    <circle cx="24" cy="16" r="1.5" fill="currentColor" />
  </svg>
);

/**
 * TRIDENT-AI Root Application.
 *
 * Three-column layout:
 * - Left (240px): Agent status sidebar
 * - Centre (flex): Incident queue + selected incident package
 * - Right (320px): Remediation panel + MCP audit trail
 */
export default function App() {
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const { incidents, loading: incidentsLoading } = useIncidents();
  const { agents } = useAgentStatus();

  const selectedIncident = incidents.find(i => i.incident_id === selectedIncidentId) || null;
  const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ') + ' UTC';

  return (
    <div className="app-layout">
      {/* ─── Header ──────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-logo">
          <TridentIcon />
          <h1>TRIDENT-AI</h1>
        </div>

        <div className="header-status">
          <span className="status-badge status-badge--active">
            <span className="status-dot" />
            Autonomous Mode: Active
          </span>
          <span className="header-time">{currentTime}</span>
          {incidents.length > 0 && (
            <span className="alert-count">{incidents.length}</span>
          )}
        </div>
      </header>

      {/* ─── Body ────────────────────────────────────────────────── */}
      <div className="app-body">
        {/* Left Sidebar — Agent Status */}
        <aside className="sidebar-left">
          <AgentStatusBar agents={agents} />
        </aside>

        {/* Centre — Incident Queue + Package */}
        <main className="main-content">
          {selectedIncident ? (
            <IncidentPackage
              incident={selectedIncident}
              onBack={() => setSelectedIncidentId(null)}
            />
          ) : (
            <IncidentQueue
              incidents={incidents}
              loading={incidentsLoading}
              selectedId={selectedIncidentId}
              onSelect={setSelectedIncidentId}
            />
          )}
        </main>

        {/* Right Sidebar — Remediation + Audit */}
        <aside className="sidebar-right">
          <RemediationPanel
            incident={selectedIncident}
          />
          <div style={{ marginTop: '16px' }}>
            <AuditTrail />
          </div>
        </aside>
      </div>
    </div>
  );
}
