import React, { useState, useEffect } from 'react';

// Minimal terminal style component
const Terminal = ({ lines }) => (
  <pre style={{
    background: '#0c0c0c',
    color: '#00ff00',
    padding: '1rem',
    height: '100vh',
    margin: 0,
    overflowY: 'auto',
    fontFamily: 'monospace',
    fontSize: '14px',
  }}>
    {lines.map((line, i) => (
      <div key={i}>{line}</div>
    ))}
  </pre>
);

export default function App() {
  const [lines, setLines] = useState([
    'Welcome to Blooberge Terminal',
    'Fetching market data...'
  ]);

  // Simple fetch to backend market data
  useEffect(() => {
    fetch('/api/market-data')
      .then(res => res.json())
      .then(data => {
        const output = [];
        if (data && data.data) {
          for (const [ticker, info] of Object.entries(data.data)) {
            output.push(`${ticker}: $${info.price?.toFixed(2)} (${info.chg?.toFixed(2)}%)`);
          }
        } else {
          output.push('No data received');
        }
        setLines(prev => [...prev, ...output]);
      })
      .catch(err => {
        setLines(prev => [...prev, `Error: ${err.message}`]);
      });
  }, []);

  return <Terminal lines={lines} />;
}
