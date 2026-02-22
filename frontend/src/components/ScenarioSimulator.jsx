import React, { useState, useEffect } from 'react';
import { Calculator, Play, AlertCircle, TrendingUp } from 'lucide-react';

export function ScenarioSimulator({ sessionId, domain, availableSimulations = [] }) {
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [parameters, setParameters] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  console.log('🎲 [ScenarioSimulator] Render - Props received:');
  console.log('🎲 [ScenarioSimulator]   sessionId:', sessionId);
  console.log('🎲 [ScenarioSimulator]   domain:', domain);
  console.log('🎲 [ScenarioSimulator]   availableSimulations:', availableSimulations);
  console.log('🎲 [ScenarioSimulator]   availableSimulations count:', availableSimulations?.length || 0);

  // Set initial scenario when availableSimulations changes
  useEffect(() => {
    console.log('🎲 [ScenarioSimulator] useEffect triggered - availableSimulations changed');
    if (availableSimulations.length > 0 && !selectedScenario) {
      const firstSim = availableSimulations[0];
      console.log('🎲 [ScenarioSimulator] Setting initial scenario:', firstSim.scenario_type);
      console.log('🎲 [ScenarioSimulator] Setting initial parameters:', firstSim.parameters);
      setSelectedScenario(firstSim.scenario_type);
      setParameters(firstSim.parameters || {});
    }
  }, [availableSimulations, selectedScenario]);

  // Update parameters when scenario changes
  const handleScenarioChange = (scenarioType) => {
    console.log('🎲 [ScenarioSimulator] Scenario changed to:', scenarioType);
    setSelectedScenario(scenarioType);
    setResult(null);
    const sim = availableSimulations.find(s => s.scenario_type === scenarioType);
    if (sim) {
      console.log('🎲 [ScenarioSimulator] Loading parameters for scenario:', sim.parameters);
      setParameters(sim.parameters || {});
    }
  };

  const handleParameterChange = (key, value) => {
    console.log('🎲 [ScenarioSimulator] Parameter changed:', key, '=', value);
    setParameters(prev => ({
      ...prev,
      [key]: key === 'has_rpe_approval' ? value === 'true' : (parseFloat(value) || 0)
    }));
  };

  const handleSimulate = async () => {
    if (!selectedScenario) return;
    
    console.log('🎲 [ScenarioSimulator] ========================================');
    console.log('🎲 [ScenarioSimulator] RUN SIMULATION clicked');
    console.log('🎲 [ScenarioSimulator] Scenario:', selectedScenario);
    console.log('🎲 [ScenarioSimulator] Parameters:', parameters);
    console.log('🎲 [ScenarioSimulator] ========================================');
    
    setLoading(true);
    setError(null);
    
    try {
      const requestBody = {
        session_id: sessionId,
        scenario_type: selectedScenario,
        parameters
      };
      console.log('🎲 [ScenarioSimulator] Sending POST /api/simulate with body:', requestBody);
      
      const response = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      console.log('🎲 [ScenarioSimulator] Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.log('🎲 [ScenarioSimulator] ❌ Error response:', errorData);
        throw new Error(errorData.detail || 'Simulation failed');
      }

      const data = await response.json();
      console.log('🎲 [ScenarioSimulator] ✅ Success! Response:', data);
      setResult(data);
    } catch (err) {
      console.log('🎲 [ScenarioSimulator] ❌ Exception:', err.message);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Don't render if no simulations available
  if (!availableSimulations || availableSimulations.length === 0) {
    return null;
  }

  const currentSimulation = availableSimulations.find(s => s.scenario_type === selectedScenario);

  // Format parameter name for display
  const formatParamName = (key) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  // Determine if result is a risk score (0-100) or dollar amount
  // Use backend's is_risk flag if available, otherwise infer from value
  // Risk scores are 0-100, anything over 100 is definitely a dollar amount
  const isRiskScore = result?.is_risk !== undefined 
    ? result.is_risk 
    : (result?.exposure_estimate <= 100);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-8">
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-purple-500/10 rounded-lg flex items-center justify-center">
          <Calculator className="w-5 h-5 text-purple-400" />
        </div>
        Scenario Simulator
      </h3>
      
      <p className="text-slate-400 text-sm mb-6">
        Run "what-if" simulations based on your document. Values are pre-filled from document analysis.
      </p>
      
      {/* Scenario Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Select Scenario
        </label>
        <select
          value={selectedScenario || ''}
          onChange={(e) => handleScenarioChange(e.target.value)}
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          {availableSimulations.map((sim) => (
            <option key={sim.scenario_type} value={sim.scenario_type}>
              {sim.label}
            </option>
          ))}
        </select>
        {currentSimulation && (
          <p className="text-slate-500 text-xs mt-2">{currentSimulation.description}</p>
        )}
      </div>

      {/* Dynamic Parameter Inputs */}
      {currentSimulation && (
        <div className="space-y-4 mb-6">
          <p className="text-sm text-slate-400 font-medium">Adjust Parameters:</p>
          {Object.entries(parameters).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                {formatParamName(key)}
              </label>
              {key === 'has_rpe_approval' ? (
                <select
                  value={value.toString()}
                  onChange={(e) => handleParameterChange(key, e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="false">No</option>
                  <option value="true">Yes</option>
                </select>
              ) : (
                <input
                  type="number"
                  value={value}
                  onChange={(e) => handleParameterChange(key, e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Formula Display */}
      {currentSimulation && (
        <div className="bg-slate-700/50 rounded-lg p-3 mb-6">
          <p className="text-xs text-slate-400">
            <strong className="text-slate-300">Formula:</strong> {currentSimulation.formula}
          </p>
        </div>
      )}

      {/* Run Button */}
      <button
        onClick={handleSimulate}
        disabled={loading || !selectedScenario}
        className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            Running Simulation...
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Run Simulation
          </>
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="mt-6 p-6 bg-slate-700 border border-slate-600 rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-6 h-6 text-purple-400" />
            <span className="text-sm text-slate-400">{result.scenario_label}</span>
          </div>
          
          <p className={`text-3xl font-bold mb-3 ${
            result.severity === 'CRITICAL' || result.severity === 'HIGH'
              ? 'text-red-400'
              : result.severity === 'MODERATE'
                ? 'text-yellow-400'
                : result.severity === 'LOW' || result.severity === 'NONE'
                  ? 'text-green-400'
                  : 'text-purple-300'
          }`}>
            {/* Show severity word + dollar amount if applicable */}
            {result.severity && result.severity !== 'UNKNOWN' 
              ? `${result.severity.charAt(0) + result.severity.slice(1).toLowerCase()} Risk`
              : result.exposure_estimate <= 100 
                ? `${result.exposure_estimate.toFixed(0)}% Risk`
                : `$${result.exposure_estimate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            }
          </p>
          {/* Show dollar amount separately if it's meaningful */}
          {result.exposure_estimate > 0 && result.severity && result.severity !== 'UNKNOWN' && (
            <p className="text-lg text-slate-400 mb-2">
              ${result.exposure_estimate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} at stake
            </p>
          )}
          
          <p className="text-slate-300 text-sm">
            {result.explanation}
          </p>
        </div>
      )}
    </div>
  );
}
