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
  // Map techniques to their tactics
  const detectedTactics = new Set();
  const tacticTechniques = {};

  (techniques || []).forEach(t => {
    const tactic = t.tactic || 'Unknown';
    detectedTactics.add(tactic);
    if (!tacticTechniques[tactic]) tacticTechniques[tactic] = [];
    tacticTechniques[tactic].push(t);
  });

  const nodeWidth = 72;
  const nodeHeight = 36;
  const gap = 4;
  const svgWidth = TACTIC_ORDER.length * (nodeWidth + gap);
  const svgHeight = 90;

  return (
    <div style={{ overflowX: 'auto', paddingBottom: '8px' }}>
      <svg width={svgWidth} height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
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
            <g key={tactic}>
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
              />

              {/* Tactic label */}
              <text
                x={x + nodeWidth / 2}
                y={y + nodeHeight / 2 + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={isDetected ? 'var(--accent-red)' : 'var(--text-muted)'}
                fontSize="7"
                fontFamily="var(--font-mono)"
                fontWeight={isDetected ? '700' : '400'}
              >
                {TACTIC_SHORT[tactic] || tactic.slice(0, 8)}
              </text>

              {/* Technique labels below */}
              {techniques.map((t, j) => (
                <text
                  key={j}
                  x={x + nodeWidth / 2}
                  y={y + nodeHeight + 12 + (j * 12)}
                  textAnchor="middle"
                  fill="var(--accent-blue)"
                  fontSize="6.5"
                  fontFamily="var(--font-mono)"
                >
                  {t.id || t}
                </text>
              ))}

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
    </div>
  );
}
