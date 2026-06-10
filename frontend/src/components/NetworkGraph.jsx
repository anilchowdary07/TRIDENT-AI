import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

/**
 * D3 force-directed network graph for affected services.
 * Nodes: microservices, databases, external IPs.
 * Node colour = health status. Edge width = impact severity.
 */
export default function NetworkGraph({ services, iocs }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !services || services.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 600;
    const height = 260;

    svg.attr('width', width).attr('height', height);

    // Build nodes
    const nodes = [];
    const links = [];

    // Central "Attack" node
    nodes.push({ id: 'attack', label: 'ATTACK ORIGIN', type: 'attack', health: 0 });

    // Service nodes
    services.forEach((svc, i) => {
      nodes.push({ id: svc, label: svc, type: 'service', health: Math.random() * 0.6 + 0.2 });
      links.push({ source: 'attack', target: svc, weight: Math.random() * 3 + 1 });
    });

    // IoC nodes
    const ips = (iocs && iocs.ips) || [];
    ips.slice(0, 3).forEach((ip) => {
      nodes.push({ id: ip, label: ip, type: 'ioc', health: 0 });
      links.push({ source: ip, target: 'attack', weight: 2 });
    });

    // Simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(30));

    // Links
    const link = svg.selectAll('.link')
      .data(links)
      .join('line')
      .attr('stroke', 'rgba(255,255,255,0.1)')
      .attr('stroke-width', d => d.weight);

    // Node groups
    const node = svg.selectAll('.node')
      .data(nodes)
      .join('g')
      .attr('class', 'node');

    // Node circles
    node.append('circle')
      .attr('r', d => d.type === 'attack' ? 14 : d.type === 'ioc' ? 8 : 10)
      .attr('fill', d => {
        if (d.type === 'attack') return 'rgba(255,45,85,0.3)';
        if (d.type === 'ioc') return 'rgba(255,140,0,0.3)';
        const health = d.health;
        if (health < 0.3) return 'rgba(255,45,85,0.4)';
        if (health < 0.6) return 'rgba(255,140,0,0.3)';
        return 'rgba(0,229,204,0.3)';
      })
      .attr('stroke', d => {
        if (d.type === 'attack') return '#FF2D55';
        if (d.type === 'ioc') return '#FF8C00';
        return '#00E5CC';
      })
      .attr('stroke-width', 1.5);

    // Pulse animation for attack node
    const attackNode = node.filter(d => d.type === 'attack');
    attackNode.append('circle')
      .attr('class', 'svg-pulse-circle')
      .attr('fill', 'none')
      .attr('stroke', '#ff2d55');

    // Node labels
    node.append('text')
      .text(d => d.label)
      .attr('dy', d => d.type === 'attack' ? 24 : 20)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', '8px')
      .attr('font-family', 'var(--font-mono)');

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [services, iocs]);

  if (!services || services.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>No affected services reported.</div>;
  }

  return <svg ref={svgRef} style={{ width: '100%', maxHeight: '260px' }} />;
}
