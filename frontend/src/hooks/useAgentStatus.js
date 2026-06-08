import { useState, useEffect } from 'react';

/**
 * Hook: monitors agent heartbeats.
 * In demo mode, simulates live agent status cycling.
 */
const INITIAL_AGENTS = [
  {
    agent_name: 'TelemetrySentinel',
    status: 'COMPLETE',
    last_poll: 'just now',
    last_anomaly: '2m ago',
    confidence_history: [0.3, 0.4, 0.5, 0.4, 0.6, 0.5, 0.8, 0.7, 0.9, 0.92],
  },
  {
    agent_name: 'ThreatMarshall',
    status: 'COMPLETE',
    last_poll: 'just now',
    last_anomaly: '2m ago',
    confidence_history: [0.1, 0.1, 0.2, 0.1, 0.3, 0.2, 0.7, 0.8, 0.95, 0.95],
  },
  {
    agent_name: 'PlatformAuditor',
    status: 'COMPLETE',
    last_poll: 'just now',
    last_anomaly: '5m ago',
    confidence_history: [0.2, 0.3, 0.2, 0.4, 0.3, 0.5, 0.4, 0.6, 0.5, 0.4],
  },
];

export function useAgentStatus(pollInterval = 15000) {
  const [agents, setAgents] = useState(INITIAL_AGENTS);

  useEffect(() => {
    // Simulate agent status cycling for demo purposes
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({
        ...agent,
        last_poll: 'just now',
        status: Math.random() > 0.8 ? 'INVESTIGATING' : 'COMPLETE',
      })));
    }, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval]);

  return { agents };
}
