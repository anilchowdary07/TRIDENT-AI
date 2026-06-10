import { useState, useEffect } from 'react';

const DEMO_AGENTS = [
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

export function useAgentStatus(pollInterval = 5000) {
  const [agents, setAgents] = useState(DEMO_AGENTS);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/agent-status');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data && data.length > 0) {
          setAgents(data);
        }
      } catch (err) {
        // Keep demo data if backend unreachable
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval]);

  return { agents };
}
