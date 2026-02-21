import React, { useState } from 'react';

export function ScenarioSimulator({ sessionId, domain }) {
  const [scenario, setScenario] = useState('early_termination');
  const [parameters, setParameters] = useState({
    months_remaining: 8,
    penalty_rate_per_month: 250,
    base_penalty: 500
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleParameterChange = (key, value) => {
    setParameters(prev => ({
      ...prev,
      [key]: parseFloat(value) || 0
    }));
  };

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          scenario,
          parameters
        })
      });

      if (!response.ok) {
        throw new Error('Simulation failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (domain !== 'housing' && domain !== 'finance') {
    return null;
  }

  return (
    <div className="card">
      <h3 className="text-xl font-bold mb-4">Scenario Simulator</h3>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Scenario Type
        </label>
        <select
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-200"
        >
          <option value="early_termination">Early Lease Termination</option>
          <option value="enrollment_change">Enrollment Change</option>
        </select>
      </div>

      <div className="space-y-3 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Base Penalty ($)
          </label>
          <input
            type="number"
            value={parameters.base_penalty}
            onChange={(e) => handleParameterChange('base_penalty', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-200"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Penalty per Month ($)
          </label>
          <input
            type="number"
            value={parameters.penalty_rate_per_month}
            onChange={(e) => handleParameterChange('penalty_rate_per_month', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-200"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Months Remaining
          </label>
          <input
            type="number"
            value={parameters.months_remaining}
            onChange={(e) => handleParameterChange('months_remaining', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-200"
          />
        </div>
      </div>

      <button
        onClick={handleSimulate}
        disabled={loading}
        className="btn-primary w-full mb-4"
      >
        {loading ? 'Running simulation...' : 'Run Simulation'}
      </button>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <p className="text-2xl font-bold text-blue-900 mb-2">
            ${result.exposure_estimate.toFixed(2)}
          </p>
          <p className="text-sm text-gray-600 mb-3">
            <strong>Formula:</strong> {result.formula_used}
          </p>
          <p className="text-sm text-gray-700 mb-3">
            {result.explanation}
          </p>
          {result.caveats && result.caveats.length > 0 && (
            <div className="text-xs text-gray-600 bg-white p-2 rounded border border-blue-100">
              <strong>Important:</strong> {result.caveats.join(' ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
