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
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="section-header__label">Incident Queue</span>
        </div>
        <div className="empty-state">
          <img src="/trident_logo.png" alt="Trident Logo" className="empty-state__icon" style={{ width: 64, height: 64, opacity: 0.5, objectFit: 'contain' }} />
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
        <div className="section-header" style={{ marginBottom: 0, paddingBottom: 0, borderBottom: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
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
