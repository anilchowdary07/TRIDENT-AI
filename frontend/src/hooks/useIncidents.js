import { useState, useEffect, useRef } from 'react';

/**
 * Hook: polls for real incidents from the backend autonomous loop.
 * 
 * NO hardcoded demo data. The backend's autonomous loop genuinely processes
 * agent findings and produces incident packages. This hook just fetches them.
 * If the backend hasn't produced any incidents yet, we return an empty array
 * and the UI shows the processing/waiting state.
 */
export function useIncidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(false);
  const errorLogged = useRef(false);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/incidents');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setBackendConnected(true);
        setIncidents(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!errorLogged.current) {
          console.warn("Backend not reachable:", err.message, "— start the backend with: python3 -m uvicorn main:app --reload");
          errorLogged.current = true;
        }
        setBackendConnected(false);
        // Don't fake data — keep incidents empty
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
    // Poll every 5s so the UI picks up new incidents quickly after first poll cycle
    const interval = setInterval(fetchIncidents, 5000);
    return () => clearInterval(interval);
  }, []);

  return { incidents, loading, backendConnected };
}
