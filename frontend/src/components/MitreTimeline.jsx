import React from 'react';

/**
 * MITRE ATT&CK chain horizontal timeline visualization.
 * Each node is a tactic phase. Highlighted nodes show detected techniques.
 */

const TACTIC_ORDER = [
  'Reconnaissance', 'Resource Development', 'Initial Access', 'Execution',
  'Persistence', 'Privilege Escalation', 'Defense Evasion', 'Credential Access',
  'Discovery', 'Lateral Movement', 'Collection', 'Command and Control',
  'Exfiltration', 'Impact',
];

const TACTIC_SHORT = {
  'Reconnaissance': 'RECON',
  'Resource Development': 'RES DEV',
  'Initial Access': 'INIT',
  'Execution': 'EXEC',
  'Persistence': 'PERSIST',
  'Privilege Escalation': 'PRIV ESC',
  'Defense Evasion': 'DEF EVA',
  'Credential Access': 'CRED',
  'Discovery': 'DISC',
  'Lateral Movement': 'LAT MOV',
  'Collection': 'COLLECT',
  'Command and Control': 'C2',
  'Exfiltration': 'EXFIL',
  'Impact': 'IMPACT',
};

export default function MitreTimeline({ techniques }) {
  const [activeTactic, setActiveTactic] = React.useState(null);
  // Map techniques to their tactics
  const detectedTactics = new Set();
  const tacticTechniques = {};

  (techniques || []).forEach(t => {
    const tactic = t.tactic || 'Unknown';
    detectedTactics.add(tactic);
    if (!tacticTechniques[tactic]) tacticTechniques[tactic] = [];
    tacticTechniques[tactic].push(t);
  });

  const nodeWidth = 36;
  const nodeHeight = 36;
  const gap = 12;
  const svgWidth = TACTIC_ORDER.length * (nodeWidth + gap);
  const svgHeight = 90;

  return (
    <div className="mitre-timeline-container" style={{ position: 'relative', overflow: 'visible', paddingBottom: '8px' }}>
      <svg width="100%" height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="xMidYMid meet">
        {/* Connection line */}
        <line
          x1={nodeWidth / 2}
          y1={nodeHeight / 2 + 4}
          x2={svgWidth - nodeWidth / 2}
          y2={nodeHeight / 2 + 4}
          stroke="var(--border-medium)"
          strokeWidth="1"
          strokeDasharray="4 3"
        />

        {TACTIC_ORDER.map((tactic, i) => {
          const isDetected = detectedTactics.has(tactic);
          const x = i * (nodeWidth + gap);
          const y = 4;
          const techniques = tacticTechniques[tactic] || [];

          return (
            <g 
              key={tactic} 
              onClick={() => isDetected && setActiveTactic(activeTactic === tactic ? null : tactic)}
              style={{ cursor: isDetected ? 'pointer' : 'default' }}
            >
              {/* Node background */}
              <rect
                x={x}
                y={y}
                width={nodeWidth}
                height={nodeHeight}
                rx={4}
                fill={isDetected ? 'rgba(255, 45, 85, 0.15)' : 'var(--bg-surface)'}
                stroke={isDetected ? 'var(--accent-red)' : 'var(--border-light)'}
                strokeWidth={isDetected ? 1.5 : 0.5}
                style={isDetected ? { filter: 'drop-shadow(0 0 12px #ff2d55)', animation: 'pulse-glow-red 2s ease-in-out infinite' } : {}}
              />

              {/* Tactic label */}
              <text
                x={x + nodeWidth / 2}
                y={y + nodeHeight / 2 + (isDetected && techniques.length > 0 ? -4 : 1)}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={isDetected ? 'var(--accent-red)' : 'var(--text-muted)'}
                fontSize="7"
                fontFamily="var(--font-mono)"
                fontWeight={isDetected ? '700' : '400'}
              >
                {TACTIC_SHORT[tactic] || tactic.slice(0, 8)}
              </text>

              {/* T-code in smaller text below the tactic name on the highlighted node */}
              {isDetected && techniques.length > 0 && (
                <text
                  x={x + nodeWidth / 2}
                  y={y + nodeHeight / 2 + 6}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="var(--accent-red)"
                  fontSize="5"
                  fontFamily="var(--font-mono)"
                >
                  {techniques.map(t => t.id || t).join(', ')}
                </text>
              )}

              {/* Active dot */}
              {isDetected && (
                <circle
                  cx={x + nodeWidth / 2}
                  cy={y - 2}
                  r={3}
                  fill="var(--accent-red)"
                  style={{ filter: 'drop-shadow(0 0 4px rgba(255,45,85,0.6))' }}
                />
              )}
            </g>
          );
        })}
      </svg>
      {/* Interactive Tooltip */}
      {activeTactic && (
        <div style={{
          position: 'absolute',
          top: '55px',
          left: `${(TACTIC_ORDER.indexOf(activeTactic) * (nodeWidth + gap) + nodeWidth / 2) / svgWidth * 100}%`,
          transform: 'translateX(-50%)',
          background: '#0a0e17',
          border: '1px solid var(--accent-red)',
          padding: '8px 12px',
          borderRadius: '6px',
          color: 'var(--text-primary)',
          fontSize: '0.75rem',
          zIndex: 10,
          width: 'max-content',
          maxWidth: '220px',
          boxShadow: '0 8px 24px rgba(255,45,85,0.2)',
        }}>
          <div style={{ fontWeight: 'bold', color: 'var(--accent-red)', marginBottom: '4px', borderBottom: '1px solid rgba(255,45,85,0.3)', paddingBottom: '4px' }}>
            {activeTactic}
          </div>
          <div style={{ color: '#a8b2c1', whiteSpace: 'pre-wrap' }}>
            {tacticTechniques[activeTactic]?.map(t => `${t.id} - ${t.name || 'Technique'}`).join('\n') || 'No techniques'}
          </div>
        </div>
      )}
    </div>
  );
}
