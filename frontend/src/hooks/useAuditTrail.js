import { useState, useEffect } from 'react';

const DEMO_AUDIT = [
  { timestamp: new Date(Date.now() - 45000).toISOString(), rpc_id: 'rpc-a1b2c3', method: 'tools/list', status: 200, security_violation: false },
  { timestamp: new Date(Date.now() - 38000).toISOString(), rpc_id: 'rpc-d4e5f6', method: 'tools/call', status: 200, security_violation: false },
  { timestamp: new Date(Date.now() - 30000).toISOString(), rpc_id: 'rpc-g7h8i9', method: 'resources/read', status: 200, security_violation: false },
  { timestamp: new Date(Date.now() - 22000).toISOString(), rpc_id: 'rpc-j0k1l2', method: 'tools/call', status: 400, security_violation: true },
  { timestamp: new Date(Date.now() - 15000).toISOString(), rpc_id: 'rpc-m3n4o5', method: 'tools/call', status: 200, security_violation: false },
];

export function useAuditTrail() {
  const [auditLogs, setAuditLogs] = useState(DEMO_AUDIT);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/audit-trail');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data && data.length > 0) {
          setAuditLogs(data);
        }
      } catch (err) {
        // Keep demo data
      }
    };
    
    fetchAudit();
    const interval = setInterval(fetchAudit, 5000);
    return () => clearInterval(interval);
  }, []);

  return { auditLogs };
}
