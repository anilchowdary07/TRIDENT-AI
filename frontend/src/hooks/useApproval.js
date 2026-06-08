import { useState, useCallback } from 'react';

/**
 * Hook: handles remediation approve/reject and MCP tool call execution.
 */
export function useApproval() {
  const [approvalStatus, setApprovalStatus] = useState({});

  const approveRemediation = useCallback(async (optionKey, option) => {
    setApprovalStatus(prev => ({ ...prev, [optionKey]: 'approved' }));

    // Simulate MCP tool call execution
    try {
      // In production: POST /api/approve-remediation → backend calls MCP tool
      await new Promise(resolve => setTimeout(resolve, 3000));
      setApprovalStatus(prev => ({ ...prev, [optionKey]: 'completed' }));
    } catch (error) {
      setApprovalStatus(prev => ({ ...prev, [optionKey]: 'failed' }));
    }
  }, []);

  const rejectRemediation = useCallback((optionKey) => {
    setApprovalStatus(prev => ({ ...prev, [optionKey]: 'rejected' }));
  }, []);

  return { approveRemediation, rejectRemediation, approvalStatus };
}
