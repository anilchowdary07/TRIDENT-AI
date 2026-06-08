import React from 'react';
import IncidentCard from './IncidentCard';

/**
 * Incident Queue — the main incident list.
 * New incidents slide in from top. Sorted by severity. Empty state with trident logo.
 */
export default function IncidentQueue({ incidents, loading, selectedId, onSelect }) {
  if (loading) {
    return (
      <div>
        <div className="section-header">
          <span className="section-header__label">Incident Queue</span>
        </div>
        <div className="stagger-children">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
      </div>
    );
  }

  if (!incidents || incidents.length === 0) {
    return (
      <div>
        <div className="section-header">
          <span className="section-header__label">Incident Queue</span>
        </div>
        <div className="empty-state">
          <svg className="empty-state__icon" width="64" height="64" viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.5">
            <line x1="16" y1="4" x2="16" y2="28" />
            <line x1="16" y1="4" x2="8" y2="12" />
            <line x1="16" y1="4" x2="24" y2="12" />
            <line x1="8" y1="12" x2="8" y2="16" />
            <line x1="24" y1="12" x2="24" y2="16" />
          </svg>
          <p className="empty-state__text">Agents watching. All systems nominal.</p>
        </div>
      </div>
    );
  }

  // Sort by severity score descending
  const sorted = [...incidents].sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0));

  return (
    <div>
      <div className="incident-queue__header">
        <div className="section-header" style={{ marginBottom: 0, paddingBottom: 0, borderBottom: 'none' }}>
          <span className="section-header__label">Incident Queue</span>
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
        }}>
          {incidents.length} active
        </span>
      </div>
      <div className="incident-queue stagger-children">
        {sorted.map((incident) => (
          <IncidentCard
            key={incident.incident_id}
            incident={incident}
            isSelected={incident.incident_id === selectedId}
            onClick={() => onSelect(incident.incident_id)}
          />
        ))}
      </div>
    </div>
  );
}
