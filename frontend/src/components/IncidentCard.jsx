import React from 'react';

/**
 * Individual incident card in the queue.
 * Severity colour-coded. Pulsing border for unacknowledged. MITRE badges.
 */
export default function IncidentCard({ incident, isSelected, onClick }) {
  const severity = (incident.severity || 'MEDIUM').toLowerCase();
  const isUnacknowledged = incident.status === 'OPEN';
  const timeAgo = getTimeAgo(incident.timestamp);
  const mitreTechniques = (incident.mitre_techniques || []).slice(0, 2);

  const cardClass = [
    'incident-card',
    `incident-card--${severity}`,
    isSelected ? 'incident-card--selected' : '',
    isUnacknowledged ? 'incident-card--unacknowledged' : '',
    'slide-in',
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClass} onClick={onClick} id={`incident-${incident.incident_id}`}>
      <div className="incident-card__top">
        <span className="incident-card__id">{incident.incident_id}</span>
        <span className={`severity-badge severity-badge--${severity}`}>
          {incident.severity}
        </span>
      </div>

      <div className="incident-card__title">{incident.title}</div>

      <div className="incident-card__meta">
        <span className="incident-card__time">{timeAgo}</span>
        {mitreTechniques.length > 0 && (
          <div className="incident-card__mitre">
            {mitreTechniques.map((t, i) => (
              <span key={i} className="mitre-badge">
                {typeof t === 'string' ? t : t.id}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function getTimeAgo(timestamp) {
  if (!timestamp) return '';
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return `${Math.floor(diffHrs / 24)}d ago`;
  } catch {
    return '';
  }
}
