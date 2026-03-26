import React, { useState } from 'react';
import client from '../api/client';
import { Search, AlertCircle, CheckCircle, Lightbulb, AlertTriangle, TrendingDown } from 'lucide-react';
import { getRiskColor, getRiskLabel } from '../utils/riskHelpers';

const StudentProfile = () => {
  const [studentId, setStudentId] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!studentId) return;
    
    setLoading(true);
    setError('');
    setData(null);
    
    try {
      const res = await client.post('/predict-risk', { student_id: parseInt(studentId) });
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to predict risk');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">Student Risk Profile</h1>
        <form onSubmit={handlePredict} className="flex space-x-4">
          <input
            type="number"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="Enter Student DB ID (e.g., 1)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Search size={18} className="mr-2" />
            {loading ? 'Analyzing...' : 'Analyze Risk'}
          </button>
        </form>
        {error && <p className="mt-4 text-red-500 text-sm flex items-center"><AlertCircle size={16} className="mr-1"/> {error}</p>}
      </div>

      {data && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Risk Level Header */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-start md:items-center">
             <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Current Risk Assessment</p>
                <div className="mt-2 flex items-baseline space-x-2">
                   <p className="text-5xl font-black text-gray-900">{data.risk_score}</p>
                   <p className="text-lg text-gray-500">/ 100</p>
                </div>
             </div>
             <div className={`mt-4 md:mt-0 px-6 py-3 rounded-xl border-2 text-lg font-black tracking-wide shadow-sm flex items-center ${getRiskColor(data.risk_level)}`}>
               {getRiskLabel(data.risk_level)}
             </div>
          </div>

          {/* Intervention Simulation - DEMO WINNING FEATURE */}
          {data.simulated_impact?.projected_risk_after_intervention && (
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 rounded-xl shadow-lg text-white flex flex-col md:flex-row items-center justify-between border border-indigo-500">
               <div>
                 <h3 className="text-xl font-bold flex items-center mb-1"><TrendingDown className="mr-2"/> Intervention Simulation</h3>
                 <p className="text-blue-100 text-sm">Projected impact of implementing all recommended actions over 30 days.</p>
               </div>
               <div className="bg-white/10 px-6 py-4 rounded-xl mt-4 md:mt-0 flex items-center space-x-4 border border-white/20">
                  <div className="text-center">
                     <p className="text-xs text-blue-200 uppercase font-bold">Current</p>
                     <p className="text-2xl font-black">{data.risk_score}%</p>
                  </div>
                  <div className="text-blue-300 font-bold">➔</div>
                  <div className="text-center">
                     <p className="text-xs text-green-300 uppercase font-bold">Projected</p>
                     <p className="text-3xl font-black text-green-400">{data.simulated_impact.projected_risk_after_intervention}%</p>
                  </div>
                  <div className="bg-green-500/20 text-green-100 px-3 py-1 rounded-lg border border-green-500/30 text-sm font-bold ml-2">
                    -{data.simulated_impact.estimated_reduction}%
                  </div>
               </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top Factors */}
            <div className="lg:col-span-1 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center pb-2 border-b border-gray-100">
                <AlertTriangle size={20} className="mr-2 text-orange-500" />
                Root Causes
              </h3>
              <ul className="space-y-4">
                {data.top_factors.map((factor, idx) => (
                  <li key={idx} className="flex flex-col space-y-1">
                    <span className="font-semibold text-gray-800 flex items-center text-sm">
                      ⚠️ {factor.label || factor.feature}
                    </span>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                       <div className="bg-red-500 h-1.5 rounded-full" style={{ width: `${Math.min(factor.shap_value * 100, 100)}%` }}></div>
                    </div>
                    <span className="text-xs text-gray-500 text-right mt-1">Impact: {(factor.shap_value * 100).toFixed(1)}%</span>
                  </li>
                ))}
                {data.top_factors.length === 0 && <p className="text-gray-500 italic text-sm">No dominant risk factors.</p>}
              </ul>
            </div>

            {/* Recommendations */}
            <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center pb-2 border-b border-gray-100">
                <Lightbulb size={20} className="mr-2 text-yellow-500" />
                AI Intervention Plan
              </h3>
              
              <div className="space-y-6 mt-4">
                {/* Immediate */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-red-600 mb-3 flex items-center">
                    <span className="w-2 h-2 rounded-full bg-red-600 mr-2"></span>Immediate Actions (48h)
                  </h4>
                  <ul className="space-y-2">
                    {data.recommendations?.immediate?.map((rec, idx) => (
                      <li key={idx} className="flex items-start text-gray-700 bg-red-50 p-3 rounded-lg border border-red-100 text-sm">
                        🔴 <span className="ml-2 font-medium">{rec}</span>
                      </li>
                    ))}
                    {(!data.recommendations?.immediate || data.recommendations.immediate.length === 0) && <p className="text-gray-400 text-sm">None</p>}
                  </ul>
                </div>

                {/* Short term */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-yellow-600 mb-3 flex items-center">
                    <span className="w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>Short-Term Goals (30d)
                  </h4>
                  <ul className="space-y-2">
                    {data.recommendations?.short_term?.map((rec, idx) => (
                      <li key={idx} className="flex items-start text-gray-700 bg-yellow-50 p-3 rounded-lg border border-yellow-200 text-sm">
                        🟡 <span className="ml-2 font-medium">{rec}</span>
                      </li>
                    ))}
                    {(!data.recommendations?.short_term || data.recommendations.short_term.length === 0) && <p className="text-gray-400 text-sm">None</p>}
                  </ul>
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
