import React, { useState } from 'react';
import { FileText, AlertTriangle, Headphones, Send, Menu, X } from 'lucide-react';
import { UploadZone } from '../components/UploadZone';
import { RiskScoreCard } from '../components/RiskScoreCard';
import { ScenarioSimulator } from '../components/ScenarioSimulator';
import { ChatWindow } from '../components/ChatWindow';

export function Dashboard() {
  const [sessionId, setSessionId] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUploadComplete = async (sid, fname) => {
    setSessionId(sid);
    setFileName(fname);
    fetchAnalysis(sid);
  };

  const fetchAnalysis = async (sid) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sid,
          language: 'en'
        })
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setFileName(null);
    setAnalysis(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 mx-auto">
              <div className="w-12 h-12 bg-gradient-to-br from-crimson-500 to-coral-500 rounded-lg flex items-center justify-center shadow-lg shadow-crimson-500/20">
                <FileText className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-crimson-400 via-coral-400 to-orange-400 bg-clip-text text-transparent tracking-tight">Navigate413</h1>
                <p className="text-sm text-slate-300">Document Intelligence Platform</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {!sessionId ? (
          // Initial State
          <div className="space-y-16">
            {/* Hero Section */}
            <div className="space-y-8 text-center animate-[fadeInUp_0.6s_ease-out]">
              <div>
                <h2 className="text-5xl font-bold text-white mb-3 tracking-tight">
                  Understand Your Documents
                </h2>
                <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
                  Extract key information, identify risks, and understand your obligations with intelligent document analysis.
                </p>
              </div>

              {/* Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 hover:border-crimson-500/50 hover:bg-slate-800/80 hover:scale-[1.02] transition-all duration-300 cursor-pointer group animate-[fadeInUp_0.6s_ease-out_0.1s_both]">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-crimson-500/10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-crimson-500/20 transition-colors">
                      <FileText className="w-6 h-6 text-crimson-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Smart Extraction</h3>
                      <p className="text-slate-300 text-base leading-relaxed">
                        Automatically extract obligations, deadlines, and key terms from financial aid letters, lease agreements, and visa documents.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 hover:border-coral-500/50 hover:bg-slate-800/80 hover:scale-[1.02] transition-all duration-300 cursor-pointer group animate-[fadeInUp_0.6s_ease-out_0.2s_both]">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-coral-500/10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-coral-500/20 transition-colors">
                      <AlertTriangle className="w-6 h-6 text-coral-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Risk Analysis</h3>
                      <p className="text-slate-300 text-base leading-relaxed">
                        Get detailed risk assessments with color-coded severity levels. Understand penalties and financial exposure before committing.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 hover:border-blue-500/50 hover:bg-slate-800/80 hover:scale-[1.02] transition-all duration-300 cursor-pointer group animate-[fadeInUp_0.6s_ease-out_0.3s_both]">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500/20 transition-colors">
                      <Headphones className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">AI Support</h3>
                      <p className="text-slate-300 text-base leading-relaxed">
                        Ask follow-up questions about your documents. Get instant answers in plain language with context-aware responses.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Upload Section */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 overflow-hidden">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Upload Document</h2>
                <p className="text-slate-400">Drag and drop your PDF or click to browse</p>
              </div>
              <UploadZone onUploadComplete={handleUploadComplete} />
            </div>

            {/* Chat Section */}
            <div className="h-96">
              <ChatWindow sessionId={null} />
            </div>
          </div>
        ) : (
          // Analysis State - Dual Column
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Document Header */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-8">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Analysis Results</h2>
                    <p className="text-slate-400 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      {fileName}
                    </p>
                  </div>
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition text-sm flex items-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    New Document
                  </button>
                </div>
              </div>

              {loading && (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                  <p className="text-slate-300 font-medium flex items-center gap-2">
                    <div className="animate-spin">
                      <FileText className="w-5 h-5" />
                    </div>
                    Analyzing document...
                  </p>
                </div>
              )}

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6">
                  <p className="text-red-300 font-medium flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                  </p>
                </div>
              )}

              {analysis && !loading && (
                <div className="space-y-6">
                  {/* Risk Score */}
                  <RiskScoreCard
                    domain={analysis.domain}
                    riskScore={analysis.risk_score}
                    riskLevel={analysis.risk_level}
                    summary={analysis.summary}
                  />


                  {/* Scenario Simulator */}
                  <ScenarioSimulator 
                    sessionId={sessionId} 
                    domain={analysis.domain}
                    availableSimulations={analysis.available_simulations || []}
                  />

                  {/* Obligations */}
                  {analysis.obligations && analysis.obligations.length > 0 && (
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-8">
                      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <div className="w-8 h-8 bg-green-500/10 rounded-lg flex items-center justify-center">
                          <AlertTriangle className="w-5 h-5 text-green-400" />
                        </div>
                        Your Obligations
                      </h3>
                      <ul className="space-y-4">
                        {analysis.obligations.map((obligation, i) => (
                          <li key={i} className="flex items-start gap-3">
                            <div className="w-5 h-5 rounded border border-green-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                            </div>
                            <span className="text-slate-300">{obligation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Chat Sidebar */}
            <div className="lg:col-span-1 h-fit sticky top-24">
              <ChatWindow sessionId={sessionId} />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 mt-20 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-8">
            <div>
              <h4 className="font-semibold text-white mb-3">Navigate</h4>
              <p className="text-sm text-slate-400 leading-relaxed">
                A hackathon project making institutional documents accessible and understandable.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-3">Capabilities</h4>
              <ul className="text-sm text-slate-400 space-y-2">
                <li><a href="#" className="hover:text-slate-300 transition">Document Analysis</a></li>
                <li><a href="#" className="hover:text-slate-300 transition">Risk Assessment</a></li>
                <li><a href="#" className="hover:text-slate-300 transition">AI Support</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-3">Legal</h4>
              <ul className="text-sm text-slate-400 space-y-2">
                <li><a href="#" className="hover:text-slate-300 transition">Privacy</a></li>
                <li><a href="#" className="hover:text-slate-300 transition">Terms</a></li>
                <li><a href="#" className="hover:text-slate-300 transition">Accessibility</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-center text-sm text-slate-500">
            <p>© 2026 Navigate. Built for students everywhere.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

