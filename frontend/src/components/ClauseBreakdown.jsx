import React, { useState } from 'react';

export function ClauseBreakdown({ clauses }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!clauses || clauses.length === 0) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Flagged Clauses</h3>
        <p className="text-gray-500">No flagged clauses found</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-xl font-bold mb-4">Flagged Clauses</h3>
      
      <div className="space-y-2">
        {clauses.map((clause, index) => (
          <div key={index} className="border border-gray-200 rounded">
            <button
              className="w-full px-4 py-3 text-left hover:bg-gray-50 transition"
              onClick={() => setExpandedId(expandedId === index ? null : index)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                      {clause.flag}
                    </span>
                    <span className="text-sm text-gray-500">
                      {(clause.risk_contribution * 100).toFixed(0)}% risk
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {clause.text}
                  </p>
                </div>
                <span className="ml-4 text-gray-400">
                  {expandedId === index ? '▼' : '▶'}
                </span>
              </div>
            </button>
            
            {expandedId === index && (
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                <p className="text-sm text-gray-700 mb-3">
                  <strong>Full clause:</strong> {clause.text}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>What this means:</strong> {clause.plain_explanation}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
