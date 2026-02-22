import React from 'react';
import { Shield, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

export function RiskScoreCard({ domain, riskScore, riskLevel, summary }) {
  const getRiskConfig = (level) => {
    switch (level) {
      case 'HIGH':
        return { 
          color: 'text-red-400', 
          bgColor: 'bg-red-500/20', 
          borderColor: 'border-red-500/30',
          barColor: 'from-red-500 to-red-600',
          icon: AlertTriangle
        };
      case 'MEDIUM':
        return { 
          color: 'text-yellow-400', 
          bgColor: 'bg-yellow-500/20', 
          borderColor: 'border-yellow-500/30',
          barColor: 'from-yellow-500 to-orange-500',
          icon: AlertCircle
        };
      case 'LOW':
        return { 
          color: 'text-green-400', 
          bgColor: 'bg-green-500/20', 
          borderColor: 'border-green-500/30',
          barColor: 'from-green-500 to-emerald-500',
          icon: CheckCircle
        };
      default:
        return { 
          color: 'text-slate-400', 
          bgColor: 'bg-slate-500/20', 
          borderColor: 'border-slate-500/30',
          barColor: 'from-slate-500 to-slate-600',
          icon: Shield
        };
    }
  };

  const config = getRiskConfig(riskLevel);
  const IconComponent = config.icon;
  const percentage = Math.min(riskScore * 100, 100);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-3">
          <div className="w-8 h-8 bg-purple-500/10 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-purple-400" />
          </div>
          Risk Assessment
        </h2>
        <span className="text-sm text-slate-400 capitalize px-3 py-1 bg-slate-700 rounded-full">
          {domain}
        </span>
      </div>
      
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <span className="text-slate-400 text-sm">Risk Score</span>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.bgColor} ${config.borderColor} border`}>
            <IconComponent className={`w-4 h-4 ${config.color}`} />
            <span className={`text-sm font-semibold ${config.color}`}>{riskLevel}</span>
          </div>
        </div>
        
        <div className="relative">
          <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${config.barColor} rounded-full transition-all duration-500 ease-out`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-slate-500">0%</span>
            <span className={`text-2xl font-bold ${config.color}`}>
              {percentage.toFixed(0)}%
            </span>
            <span className="text-xs text-slate-500">100%</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-700">
        <p className="text-slate-300 text-sm leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}
