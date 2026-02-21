import React from 'react';

export function RiskScoreCard({ domain, riskScore, riskLevel, summary }) {
  const getColorClass = (level) => {
    switch (level) {
      case 'HIGH':
        return 'badge-high';
      case 'MEDIUM':
        return 'badge-medium';
      case 'LOW':
        return 'badge-low';
      default:
        return 'badge-low';
    }
  };

  const getGaugeColor = (score) => {
    if (score < 0.4) return '#10b981'; // green
    if (score < 0.7) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4">Risk Assessment</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <p className="text-gray-600 text-sm mb-1">Domain</p>
          <p className="text-lg font-semibold capitalize">{domain}</p>
        </div>
        <div>
          <p className="text-gray-600 text-sm mb-1">Risk Level</p>
          <div className={getColorClass(riskLevel)}>
            {riskLevel}
          </div>
        </div>
      </div>

      <div className="mb-6">
        <p className="text-gray-600 text-sm mb-2">Risk Score</p>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${Math.min(riskScore * 100, 100)}%`,
                  backgroundColor: getGaugeColor(riskScore)
                }}
              />
            </div>
          </div>
          <span className="text-xl font-bold text-gray-800">
            {(riskScore * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="pt-4 border-t">
        <p className="text-gray-700 text-sm">{summary}</p>
      </div>
    </div>
  );
}
