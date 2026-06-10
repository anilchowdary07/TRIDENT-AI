import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export default function TelemetryChart({ telemetryData }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 600;
    const height = 160;
    const margin = { top: 20, right: 20, bottom: 20, left: 40 };

    const data = [];
    const now = new Date();
    if (telemetryData && telemetryData.actual_vs_forecast && telemetryData.actual_vs_forecast.actual && telemetryData.actual_vs_forecast.actual.length > 0) {
      const actuals = telemetryData.actual_vs_forecast.actual;
      const lowers = telemetryData.forecast_band?.lower || [];
      const uppers = telemetryData.forecast_band?.upper || [];
      const length = actuals.length;
      for (let i = 0; i < length; i++) {
        // We consider it an anomaly if actual goes above the Q80 upper band
        const isAnomaly = actuals[i] > (uppers[i] || Infinity);
        data.push({
          time: new Date(now.getTime() - (length - 1 - i) * 60000),
          lower: lowers[i] !== undefined ? lowers[i] : actuals[i] * 0.8,
          upper: uppers[i] !== undefined ? uppers[i] : actuals[i] * 1.2,
          actual: actuals[i],
          isAnomaly
        });
      }
    } else {
      // Fallback mock data if real data is missing
      for (let i = 0; i < 50; i++) {
        const isAnomaly = i >= 40;
        data.push({
          time: new Date(now.getTime() - (50 - i) * 60000),
          lower: 100 + Math.sin(i * 0.2) * 10,
          upper: 150 + Math.sin(i * 0.2) * 10,
          actual: isAnomaly ? 160 + (i - 40) * 15 : 125 + Math.sin(i * 0.2) * 10 + (Math.random() * 10 - 5),
          isAnomaly
        });
      }
    }

    const x = d3.scaleTime()
      .domain(d3.extent(data, d => d.time))
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => Math.max(d.upper, d.actual)) * 1.1])
      .range([height - margin.bottom, margin.top]);

    // Area between lower and upper (safe zone)
    const safeZoneArea = d3.area()
      .x(d => x(d.time))
      .y0(d => y(d.lower))
      .y1(d => y(d.upper))
      .curve(d3.curveMonotoneX);

    svg.append('path')
      .datum(data)
      .attr('fill', 'rgba(0, 229, 204, 0.15)')
      .attr('d', safeZoneArea);

    // Lines
    const lineLower = d3.line()
      .x(d => x(d.time))
      .y(d => y(d.lower))
      .curve(d3.curveMonotoneX);

    const lineUpper = d3.line()
      .x(d => x(d.time))
      .y(d => y(d.upper))
      .curve(d3.curveMonotoneX);

    svg.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0, 229, 204, 0.5)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .attr('d', lineLower);

    svg.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0, 229, 204, 0.5)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .attr('d', lineUpper);

    // Actual line segments (split into safe and anomaly parts)
    const actualLine = d3.line()
      .x(d => x(d.time))
      .y(d => y(d.actual))
      .curve(d3.curveMonotoneX);

    svg.append('linearGradient')
      .attr('id', 'line-gradient')
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', x(data[0].time)).attr('y1', 0)
      .attr('x2', x(data[data.length - 1].time)).attr('y2', 0)
      .selectAll('stop')
      .data([
        { offset: '0%', color: '#ffffff' },
        { offset: '79%', color: '#ffffff' },
        { offset: '80%', color: '#ff2d55' },
        { offset: '100%', color: '#ff2d55' }
      ])
      .enter().append('stop')
      .attr('offset', d => d.offset)
      .attr('stop-color', d => d.color);

    svg.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', 'url(#line-gradient)')
      .attr('stroke-width', 2)
      .attr('d', actualLine);

    // Axes
    svg.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat('%H:%M')))
      .attr('color', 'var(--text-muted)')
      .attr('font-family', 'var(--font-mono)')
      .attr('font-size', '10px');

    svg.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(4))
      .attr('color', 'var(--text-muted)')
      .attr('font-family', 'var(--font-mono)')
      .attr('font-size', '10px');

    // Anomaly Marker
    const anomalyPoint = data.find(d => d.isAnomaly);
    if (anomalyPoint) {
      svg.append('line')
        .attr('x1', x(anomalyPoint.time))
        .attr('y1', margin.top)
        .attr('x2', x(anomalyPoint.time))
        .attr('y2', height - margin.bottom)
        .attr('stroke', '#ff2d55')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '4,4');

      svg.append('text')
        .attr('x', x(anomalyPoint.time) - 5)
        .attr('y', margin.top + 10)
        .attr('fill', '#ff2d55')
        .attr('font-size', '9px')
        .attr('font-family', 'var(--font-mono)')
        .attr('font-weight', 'bold')
        .attr('text-anchor', 'end')
        .text('ANOMALY DETECTED');
    }

  }, [telemetryData]);

  return (
    <svg 
      ref={svgRef} 
      style={{ width: '100%', height: '160px', background: 'var(--bg-surface)' }} 
      viewBox="0 0 600 160"
      preserveAspectRatio="xMidYMid meet"
    />
  );
}
