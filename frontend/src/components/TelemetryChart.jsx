import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
  annotationPlugin
);

export default function TelemetryChart({ telemetryData, timeline }) {
  let labels = [];
  let actual = [];
  let upper = [];
  let lower = [];
  let anomalyIndex = -1;

  if (timeline && timeline.length > 0) {
    labels = timeline.map(t => {
      const d = new Date(t.timestamp);
      return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
    });
    
    // Extrapolate some realistic metrics matching the narrative
    actual = [120, 150, 180, 240, 310, 340];
    upper = [156, 156, 156, 156, 156, 156];
    lower = [80, 80, 80, 80, 80, 80];
    anomalyIndex = actual.findIndex((v, i) => v > upper[i]);
  } else {
    // Generate 50 points if no timeline available
    const now = new Date();
    for (let i = 0; i < 50; i++) {
      const d = new Date(now.getTime() - (50 - i) * 60000);
      labels.push(`${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`);
      
      const isAnomaly = i >= 40;
      const u = 150 + Math.sin(i * 0.2) * 10;
      const l = 100 + Math.sin(i * 0.2) * 10;
      const a = isAnomaly ? 160 + (i - 40) * 15 : 125 + Math.sin(i * 0.2) * 10 + (Math.random() * 10 - 5);
      
      upper.push(u);
      lower.push(l);
      actual.push(a);
      if (isAnomaly && anomalyIndex === -1) anomalyIndex = i;
    }
  }

  const data = {
    labels,
    datasets: [
      {
        label: 'Actual Metric',
        data: actual,
        borderColor: '#ffffff',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        segment: {
          borderColor: ctx => {
            if (actual[ctx.p1DataIndex] > upper[ctx.p1DataIndex]) return '#ff2d55';
            return '#ffffff';
          }
        },
        fill: false,
        zIndex: 3
      },
      {
        label: 'Q80 Upper Band',
        data: upper,
        borderColor: 'rgba(0, 229, 204, 0.5)',
        borderWidth: 1,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: '+1', // Fill down to the Q20 dataset
        backgroundColor: 'rgba(0, 229, 204, 0.1)',
        zIndex: 2
      },
      {
        label: 'Q20 Lower Band',
        data: lower,
        borderColor: 'rgba(0, 229, 204, 0.5)',
        borderWidth: 1,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        zIndex: 1
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(10, 14, 23, 0.9)',
        titleFont: { family: 'var(--font-sans)', size: 11 },
        bodyFont: { family: 'var(--font-sans)', size: 11 },
        borderColor: 'var(--border-light)',
        borderWidth: 1,
      },
      annotation: {
        annotations: anomalyIndex !== -1 ? {
          anomalyLine: {
            type: 'line',
            xMin: labels[anomalyIndex],
            xMax: labels[anomalyIndex],
            borderColor: '#ff2d55',
            borderWidth: 1,
            borderDash: [4, 4],
            label: {
              display: true,
              content: 'ANOMALY DETECTED — TRIDENT TRIGGERED',
              position: 'start',
              backgroundColor: 'rgba(255, 45, 85, 0.15)',
              color: '#ff2d55',
              font: {
                family: 'var(--font-mono)',
                size: 9,
                weight: 'bold'
              },
              yAdjust: 0
            }
          }
        } : {}
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: '#a8b2c1',
          font: { family: 'var(--font-mono)', size: 10 },
          maxTicksLimit: 8
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#a8b2c1',
          font: { family: 'var(--font-mono)', size: 10 },
        }
      }
    }
  };

  return (
    <div style={{ width: '100%', height: '220px', padding: '8px 0', background: 'var(--bg-surface)' }}>
      <Line data={data} options={options} />
    </div>
  );
}
