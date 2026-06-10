import React, { useState, useEffect, useRef } from 'react';
import AgentStatusBar from './components/AgentStatusBar';
import IncidentQueue from './components/IncidentQueue';
import IncidentPackage from './components/IncidentPackage';
import RemediationPanel from './components/RemediationPanel';
import AuditTrail from './components/AuditTrail';
import { useIncidents } from './hooks/useIncidents';
import { useAgentStatus } from './hooks/useAgentStatus';

/* ─── SVG Trident Icon ───────────────────────────────────────────── */
const TridentIcon = ({ size = 30 }) => (
  <img 
    src="/trident_logo.png" 
    alt="Trident Logo" 
    style={{ 
      width: size, 
      height: size, 
      objectFit: 'contain',
      filter: 'drop-shadow(0 0 8px rgba(0, 229, 204, 0.4))'
    }} 
  />
);

/* ─── Agent Processing Stage Icon ────────────────────────────────── */
const agentIcons = {
  TelemetrySentinel: '📡',
  ThreatMarshall: '🛡️',
  PlatformAuditor: '⚙️',
};

/**
 * TRIDENT-AI Root Application.
 *
 * The processing state is REAL — it reflects the actual backend autonomous loop.
 * The UI polls /api/incidents. When the backend returns empty (agents haven't
 * finished their first poll cycle), the UI shows a genuine "agents processing" view.
 * When the backend returns real incident data, the UI transitions to show it.
 */
export default function App() {
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [resolvedIncidents, setResolvedIncidents] = useState({});
  const { incidents, loading: incidentsLoading, backendConnected } = useIncidents();
  const { agents } = useAgentStatus();
  const hasAutoSelected = useRef(false);

  // Demo sequence state
  const [demoRunning, setDemoRunning] = useState(false);
  const [showDemoSequence, setShowDemoSequence] = useState(false);
  const [demoStep, setDemoStep] = useState(0);

  const runDemo = async () => {
    setDemoRunning(true);
    setShowDemoSequence(true);
    
    // Animate sequence steps
    setDemoStep(1);
    setTimeout(() => setDemoStep(2), 1500);
    setTimeout(() => setDemoStep(3), 3500);
    setTimeout(() => setDemoStep(4), 5500);

    setTimeout(async () => {
      setShowDemoSequence(false);
      try {
        await fetch('http://localhost:8000/api/inject-demo', {method: 'POST'});
      } catch (e) {
        console.error(e);
      }
      setDemoRunning(false);
    }, 6500);
  };

  const renderDemoModal = () => {
    if (!showDemoSequence) return null;
    return (
      <div className="modal-overlay">
        <div className="modal-content" style={{maxWidth: '480px', padding: '32px'}}>
          <h2 style={{fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)', marginBottom: '24px'}}>
            {"[ EXECUTION: SCENARIO INJECTION ]"}
          </h2>
          <div className="execution-steps" style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
            <div style={{display: 'flex', gap: '12px', alignItems: 'center', opacity: demoStep >= 1 ? 1 : 0.3}}>
              <span className="status-dot" style={{background: 'var(--accent-blue)', boxShadow: '0 0 8px var(--accent-blue)'}}></span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: '0.9rem'}}>Simulating traffic anomaly on payments.latency_ms...</span>
            </div>
            <div style={{display: 'flex', gap: '12px', alignItems: 'center', opacity: demoStep >= 2 ? 1 : 0.3}}>
              <span className="status-dot" style={{background: 'var(--accent-amber)', boxShadow: '0 0 8px var(--accent-amber)'}}></span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: '0.9rem'}}>Anomalous payload detected. Triggering Agentic Swarm...</span>
            </div>
            <div style={{display: 'flex', gap: '12px', alignItems: 'center', opacity: demoStep >= 3 ? 1 : 0.3}}>
              <span className="status-dot" style={{background: 'var(--accent-teal)', boxShadow: '0 0 8px var(--accent-teal)'}}></span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: '0.9rem'}}>Agents querying Splunk Cloud & mapping MITRE techniques...</span>
            </div>
            <div style={{display: 'flex', gap: '12px', alignItems: 'center', opacity: demoStep >= 4 ? 1 : 0.3}}>
              <span className="status-dot" style={{background: 'var(--accent-red)', boxShadow: '0 0 8px var(--accent-red)'}}></span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--accent-red)'}}>Incident Package Synthesized. Awaiting Analyst Approval...</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Apply local overrides for resolved incidents
  const processedIncidents = incidents.map(incident => {
    if (resolvedIncidents[incident.incident_id]) {
      return { ...incident, status: 'MITIGATED', severity: 'RESOLVED' };
    }
    return incident;
  });

  // Determine if we're genuinely waiting for backend to produce data
  const isWaitingForAgents = backendConnected && incidents.length === 0 && !incidentsLoading;
  const isBackendDown = !backendConnected && !incidentsLoading;
  const hasIncidents = processedIncidents.length > 0;

  // Auto-select the most critical incident when data arrives
  useEffect(() => {
    if (!hasAutoSelected.current && !selectedIncidentId && hasIncidents) {
      const firstActive = processedIncidents.find(i => i.status !== 'MITIGATED') || processedIncidents[0];
      setSelectedIncidentId(firstActive.incident_id);
      hasAutoSelected.current = true;
    }
  }, [processedIncidents, selectedIncidentId, hasIncidents]);

  const selectedIncident = processedIncidents.find(i => i.incident_id === selectedIncidentId) || null;
  const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ') + ' UTC';
  const activeIncidentsCount = processedIncidents.filter(i => i.status !== 'MITIGATED').length;

  // Derive a processing message from real agent statuses
  const getProcessingMessage = () => {
    if (isBackendDown) return 'CONNECTING TO TRIDENT BACKEND...';
    if (!agents || agents.length === 0) return 'INITIALIZING AUTONOMOUS AGENTS...';
    
    const investigating = agents.find(a => a.status === 'INVESTIGATING');
    if (investigating) return `${investigating.agent_name} ANALYZING...`;
    
    const allComplete = agents.every(a => a.status === 'COMPLETE');
    if (allComplete) return 'SYNTHESIZING INCIDENT PACKAGE...';
    
    return 'AGENTS POLLING DATA STREAMS...';
  };

  return (
    <div className="app-layout">
      {/* ─── Header ──────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-logo">
          <TridentIcon size={30} />
          <h1>TRIDENT-AI</h1>
        </div>

        <div className="header-status" style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
          <button className="btn btn--outline" onClick={runDemo} disabled={demoRunning} style={{ width: 'auto', padding: '6px 12px', fontSize: '11px', borderColor: 'var(--accent-teal)', color: 'var(--accent-teal)' }}>
            {demoRunning ? 'Injecting...' : 'Run Demo Scenario'}
          </button>
          <span className={`status-badge ${backendConnected ? 'status-badge--active' : 'status-badge--inactive'}`}>
            <span className="status-dot" />
            {backendConnected ? 'Autonomous Mode: Active' : 'Connecting...'}
          </span>
          <span className="header-time">{currentTime}</span>
          {activeIncidentsCount > 0 && (
            <span className="alert-count">{activeIncidentsCount}</span>
          )}
        </div>
      </header>

      {/* ─── Body ────────────────────────────────────────────────── */}
      <div className="app-body">
        {/* Left Sidebar — Agent Status */}
        <aside className="sidebar-left">
          <AgentStatusBar agents={agents} />
        </aside>

        {/* Centre — Real-time content based on backend state */}
        <main className="main-content">
          {(!hasIncidents && (isWaitingForAgents || isBackendDown || incidentsLoading)) ? (
            /* ─── Processing View — reflects REAL backend state ─── */
            <div className="processing-screen" style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%', textAlign: 'center'
            }}>
              <div className="processing-screen__icon" style={{ marginBottom: '32px', animation: 'float 3s ease-in-out infinite' }}>
                <TridentIcon size={160} />
              </div>
              <div className="processing-screen__title" style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 600, color: 'var(--accent-teal)', letterSpacing: '0.1em', marginBottom: '8px' }}>
                {getProcessingMessage()}
              </div>
              <div className="processing-screen__subtitle" style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '40px' }}>
                {isBackendDown
                  ? 'Start backend: python3 -m uvicorn main:app --reload'
                  : 'Autonomous agents are analyzing real-time event streams...'}
              </div>

              {/* Agent status cards during processing */}
              {agents && agents.length > 0 && !isBackendDown && (
                <div className="processing-screen__agents" style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
                  {agents.map(agent => (
                    <div key={agent.agent_name} className={`processing-agent processing-agent--${agent.status?.toLowerCase() || 'idle'}`}>
                      <span className="processing-agent__icon">{agentIcons[agent.agent_name] || '🔍'}</span>
                      <span className="processing-agent__name">{agent.agent_name}</span>
                      <span className={`processing-agent__status processing-agent__status--${agent.status?.toLowerCase() || 'idle'}`}>
                        {agent.status || 'IDLE'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : selectedIncident ? (
            <IncidentPackage
              incident={selectedIncident}
              onBack={() => setSelectedIncidentId(null)}
            />
          ) : (
            <IncidentQueue
              incidents={processedIncidents}
              loading={incidentsLoading}
              selectedId={selectedIncidentId}
              onSelect={setSelectedIncidentId}
            />
          )}
        </main>

        {/* Right Sidebar — Remediation + Audit */}
        <aside className="sidebar-right">
          <RemediationPanel
            incident={hasIncidents ? selectedIncident : null}
            onRemediationComplete={(incidentId) => {
              setResolvedIncidents(prev => ({...prev, [incidentId]: true}));
            }}
          />
          <div style={{ marginTop: '16px' }}>
            <AuditTrail />
          </div>
        </aside>
      </div>
      {renderDemoModal()}
    </div>
  );
}
