import React from 'react';

const InsightReport = ({ report }) => {
  if (!report) return null;

  return (
    <div className="insight-report">
      <h3>Clinical Insight Report</h3>

      <pre style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', textAlign: 'left', overflowX: 'auto' }}>
        {JSON.stringify(report, null, 2)}
      </pre>
    </div>
  );
};

export default InsightReport;
