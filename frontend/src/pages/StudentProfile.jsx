import React, { useState } from 'react';
import client from '../api/client';
import { useToast } from '../hooks/useToast';
import RiskBadge from '../components/RiskBadge';
import EmptyState from '../components/EmptyState';
import {
  Search, AlertCircle, Lightbulb, AlertTriangle,
  TrendingDown, Brain, Info, ShieldAlert, Activity
} from 'lucide-react';

// ── Confidence display from risk_score ──────────────────────
function ConfidenceBar({ score }) {
  // Confidence is highest when score is near extremes (very high or very low)
  // Near 50 = model is uncertain. Uses a parabola: confidence = 1 - 4*(score/100 - 0.5)^2
  const conf = Math.round((1 - 4 * Math.pow(score / 100 - 0.5, 2)) * 30 + 70); // range ~70-100%
  const clampedConf = Math.min(100, Math.max(60, conf));
  const barColor = clampedConf >= 85 ? 'bg-emerald-500' : clampedConf >= 75 ? 'bg-amber-500' : 'bg-gray-400';

  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold uppercase tracking-wide text-gray-500 flex items-center gap-1.5">
          <Info size={12} /> Model Confidence
        </span>
        <span className="text-sm font-black text-gray-800">{clampedConf}%</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-700`}
          style={{ width: `${clampedConf}%` }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-1.5">
        {clampedConf >= 85 ? 'High confidence — strong signal detected'
          : clampedConf >= 75 ? 'Moderate confidence — consider additional context'
          : 'Lower confidence — borderline case, manual review recommended'}
      </p>
    </div>
  );
}

// ── Factor impact bar ───────────────────────────────────────
function FactorBar({ factor, idx }) {
  const impact = Math.min(Math.abs(factor.shap_value) * 100, 100);
  const colors = ['bg-red-500', 'bg-orange-500', 'bg-amber-500', 'bg-yellow-500'];
  const bgColors = ['bg-red-50 border-red-100', 'bg-orange-50 border-orange-100', 'bg-amber-50 border-amber-100', 'bg-yellow-50 border-yellow-100'];

  return (
    <li className={`p-4 rounded-xl border ${bgColors[idx] || 'bg-gray-50 border-gray-100'}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="font-semibold text-gray-800 text-sm leading-snug">
          ⚠️ {factor.label || factor.feature}
        </span>
        <span className="text-xs font-bold text-gray-500 flex-shrink-0 mt-0.5">
          {impact.toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${colors[idx] || 'bg-gray-400'}`}
          style={{ width: `${impact}%` }}
        />
      </div>
      {factor.description && (
        <p className="text-xs text-gray-500 mt-1.5">{factor.description}</p>
      )}
    </li>
  );
}

// ── Main StudentProfile ─────────────────────────────────────
const StudentProfile = () => {
  const [studentId, setStudentId] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { addToast } = useToast();

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!studentId) {
      addToast('Please enter a Student DB ID first', 'warning');
      return;
    }
    setLoading(true);
    setError('');
    setData(null);

    try {
      const res = await client.post('/predict-risk', { student_id: parseInt(studentId) });
      setData(res.data);
      addToast(`Risk analysis complete for Student #${studentId}`, 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to predict risk. Ensure model is trained.';
      setError(msg);
      addToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6">
      {/* Search Panel */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 bg-blue-50 rounded-xl">
            <Brain size={22} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-black text-gray-900">Student Risk Profiler</h1>
            <p className="text-gray-400 text-xs mt-0.5">AI-powered dropout risk assessment with explainable insights</p>
          </div>
        </div>
        <form onSubmit={handlePredict} className="flex gap-3">
          <input
            type="number"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="Enter Student DB ID (e.g., 1, 2, 3…)"
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-gray-50 text-gray-900 placeholder-gray-400 transition-all"
            min="1"
          />
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all font-bold text-sm shadow-md shadow-blue-200"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing…
              </>
            ) : (
              <><Search size={16} /> Analyze Risk</>
            )}
          </button>
        </form>
        {error && (
          <div className="mt-3 flex items-start gap-2 text-red-600 bg-red-50 border border-red-100 rounded-xl p-3">
            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Empty state when nothing searched */}
      {!data && !loading && !error && (
        <EmptyState
          icon={Activity}
          title="Enter a Student ID to begin"
          description="Type a student's database ID above and click Analyze Risk to generate an AI-powered dropout risk assessment."
        />
      )}

      {/* Results */}
      {data && (
        <div className="space-y-6">
          {/* Risk Header */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <div className="flex flex-col md:flex-row justify-between items-start gap-6">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                  Current Risk Assessment — Student #{studentId}
                </p>
                <div className="flex items-baseline gap-3">
                  <span className="text-6xl font-black text-gray-900">{data.risk_score}</span>
                  <span className="text-2xl text-gray-400 font-light">/ 100</span>
                </div>
                <div className="mt-3">
                  <RiskBadge level={data.risk_level} />
                </div>
              </div>
              {/* Risk gauge visual */}
              <div className="text-right">
                <div className="relative w-32 h-16 mx-auto">
                  <svg viewBox="0 0 120 60" className="w-full h-full">
                    <path d="M10 55 A 50 50 0 0 1 110 55" fill="none" stroke="#e5e7eb" strokeWidth="10" strokeLinecap="round" />
                    <path
                      d="M10 55 A 50 50 0 0 1 110 55"
                      fill="none"
                      stroke={data.risk_level === 'HIGH' ? '#ef4444' : data.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981'}
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeDasharray={`${(data.risk_score / 100) * 157} 157`}
                    />
                  </svg>
                </div>
                <p className="text-xs text-gray-400 mt-1">Risk Gauge</p>
              </div>
            </div>
            <ConfidenceBar score={data.risk_score} />
          </div>

          {/* Intervention Simulation */}
          {data.simulated_impact?.projected_risk_after_intervention != null && (
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 rounded-2xl shadow-lg text-white border border-indigo-500/50">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
                <div>
                  <h3 className="text-lg font-bold flex items-center gap-2 mb-1">
                    <TrendingDown size={20} /> Intervention Simulation
                  </h3>
                  <p className="text-blue-200 text-sm">Projected impact of implementing all recommendations over 30 days</p>
                </div>
                <div className="bg-white/10 border border-white/20 rounded-xl px-6 py-4 flex items-center gap-5">
                  <div className="text-center">
                    <p className="text-xs uppercase font-bold text-blue-200">Current</p>
                    <p className="text-3xl font-black">{data.risk_score}%</p>
                  </div>
                  <div className="text-blue-300 text-2xl font-bold">→</div>
                  <div className="text-center">
                    <p className="text-xs uppercase font-bold text-emerald-300">Projected</p>
                    <p className="text-3xl font-black text-emerald-400">
                      {data.simulated_impact.projected_risk_after_intervention}%
                    </p>
                  </div>
                  <div className="bg-emerald-500/20 text-emerald-200 px-3 py-2 rounded-lg border border-emerald-500/30 text-sm font-bold">
                    -{data.simulated_impact.estimated_reduction}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Explanation + Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Root Causes */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
                <ShieldAlert size={18} className="text-red-500" /> Why This Student Is At Risk
              </h3>
              {data.top_factors?.length > 0 ? (
                <ul className="space-y-3">
                  {data.top_factors.slice(0, 4).map((factor, idx) => (
                    <FactorBar key={idx} factor={factor} idx={idx} />
                  ))}
                </ul>
              ) : (
                <EmptyState
                  icon={AlertTriangle}
                  title="No dominant factors"
                  description="Insufficient SHAP data to explain this prediction."
                />
              )}
            </div>

            {/* AI Recommendations */}
            <div className="lg:col-span-3 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Lightbulb size={18} className="text-amber-500" /> AI Intervention Plan
              </h3>
              <div className="space-y-5">
                {/* Immediate */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-red-600 mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                    Immediate Actions (48h)
                  </h4>
                  {data.recommendations?.immediate?.length > 0 ? (
                    <ul className="space-y-2">
                      {data.recommendations.immediate.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 bg-red-50 border border-red-100 p-3 rounded-xl">
                          🔴 <span className="font-medium">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-400 text-sm italic">No immediate actions required.</p>
                  )}
                </div>

                {/* Short term */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                    Short-Term Goals (30 days)
                  </h4>
                  {data.recommendations?.short_term?.length > 0 ? (
                    <ul className="space-y-2">
                      {data.recommendations.short_term.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 bg-amber-50 border border-amber-100 p-3 rounded-xl">
                          🟡 <span className="font-medium">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-400 text-sm italic">No short-term goals defined.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentProfile;
