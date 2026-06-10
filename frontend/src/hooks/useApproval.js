import { useState, useCallback } from 'react';

/**
 * Hook: handles remediation approve/reject and MCP tool call execution via the backend.
 */
export function useApproval() {
  const [approvalStatus, setApprovalStatus] = useState({});

  const approveRemediation = useCallback(async (optionKey, incidentId, actionIndex) => {
    setApprovalStatus(prev => ({ ...prev, [optionKey]: 'approved' }));

    try {
      const res = await fetch(`http://localhost:8000/api/approve/${incidentId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action_index: actionIndex})
      });
      const result = await res.json();
      if (result.success) {
        setApprovalStatus(prev => ({ ...prev, [optionKey]: 'completed' }));
        return true;
      } else {
        setApprovalStatus(prev => ({ ...prev, [optionKey]: 'failed' }));
        return false;
      }
    } catch (error) {
      setApprovalStatus(prev => ({ ...prev, [optionKey]: 'failed' }));
      return false;
    }
  }, []);

  const rejectRemediation = useCallback((optionKey) => {
    setApprovalStatus(prev => ({ ...prev, [optionKey]: 'rejected' }));
  }, []);

  return { approveRemediation, rejectRemediation, approvalStatus };
}
