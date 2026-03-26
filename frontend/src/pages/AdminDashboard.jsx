import React, { useState, useEffect, useCallback } from 'react';
import client from '../api/client';
import { useToast } from '../hooks/useToast';
import StatCard from '../components/StatCard';
import EmptyState from '../components/EmptyState';
import RiskBadge from '../components/RiskBadge';
import { DashboardSkeleton } from '../components/Skeletons';
import {
  Users, AlertTriangle, CheckCircle, Brain, RefreshCw,
  Cpu, BarChart2, Zap, Activity, Download, ChevronRight,
  Database, TrendingUp
} from 'lucide-react';

// ── Train Model Step Progress ─────────────────────────────────
const TRAIN_STEPS = [
  { label: 'Extracting features…', icon: Database, duration: 1800 },
  { label: 'Training XGBoost model…', icon: Cpu, duration: 2800 },
  { label: 'Evaluating performance…', icon: BarChart2, duration: 1500 },
  { label: 'Finalizing model…', icon: Zap, duration: 1000 },
];

function TrainProgress({ step, metrics }) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-40 p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-200">
            <Cpu size={32} className="text-white animate-pulse" />
          </div>
          <h2 className="text-xl font-black text-gray-900">Training AI Model</h2>
          <p className="text-gray-500 text-sm mt-1">Please wait while the model trains…</p>
        </div>
        <div className="space-y-3">
          {TRAIN_STEPS.map((s, idx) => {
            const Icon = s.icon;
            const done = idx < step;
            const active = idx === step;
            return (
              <div key={idx} className={`flex items-center gap-3 p-3 rounded-xl transition-all
                ${done ? 'bg-emerald-50' : active ? 'bg-blue-50 ring-2 ring-blue-200' : 'bg-gray-50 opacity-50'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                  ${done ? 'bg-emerald-500' : active ? 'bg-blue-500' : 'bg-gray-200'}`}>
                  {done ? <CheckCircle size={16} className="text-white" /> : <Icon size={16} className="text-white" />}
                </div>
                <span className={`text-sm font-semibold
                  ${done ? 'text-emerald-700' : active ? 'text-blue-700' : 'text-gray-400'}`}>
                  {s.label}
                </span>
                {active && <span className="ml-auto w-4 h-4 border-2 border-blue-400 border-t-blue-700 rounded-full animate-spin flex-shrink-0" />}
                {done && <CheckCircle size={16} className="ml-auto text-emerald-500 flex-shrink-0" />}
              </div>
            );
          })}
        </div>
        {metrics && (
          <div className="mt-5 p-4 bg-emerald-50 rounded-xl border border-emerald-100">
            <p className="text-xs font-bold uppercase text-emerald-600 mb-2 tracking-wide">Training Complete ✅</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {metrics.accuracy && <span className="text-gray-600">Accuracy: <strong>{(metrics.accuracy * 100).toFixed(1)}%</strong></span>}
              {metrics.auc && <span className="text-gray-600">AUC-ROC: <strong>{metrics.auc.toFixed(3)}</strong></span>}
              {metrics.f1 && <span className="text-gray-600">F1 Score: <strong>{metrics.f1.toFixed(3)}</strong></span>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────
const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainStep, setTrainStep] = useState(0);
  const [trainMetrics, setTrainMetrics] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const { addToast } = useToast();

  const fetchDashboard = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const res = await client.get('/admin/dashboard');
      setData(res.data);
      setLastRefreshed(new Date());
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to load dashboard';
      setError(msg);
      if (!silent) addToast(msg, 'error');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [addToast]);

  // Initial load
  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => fetchDashboard(true), 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const handleTrainModel = async () => {
    setIsTraining(true);
    setTrainStep(0);
    setTrainMetrics(null);

    // Animate steps while waiting for real API call
    let stepIdx = 0;
    const stepForward = () => {
      if (stepIdx < TRAIN_STEPS.length - 1) {
        stepIdx += 1;
        setTrainStep(stepIdx);
      }
    };

    // Schedule step animations
    let elapsed = 0;
    const timers = TRAIN_STEPS.slice(0, -1).map((s) => {
      elapsed += s.duration;
      return setTimeout(stepForward, elapsed);
    });

    try {
      const res = await client.post('/train-model');
      timers.forEach(clearTimeout);
      setTrainStep(TRAIN_STEPS.length - 1);
      setTimeout(() => {
        setTrainMetrics(res.data.metrics || {});
      }, 800);
      addToast('🎉 Model trained successfully!', 'success', 5000);
      setTimeout(() => {
        setIsTraining(false);
        fetchDashboard(true);
      }, 3500);
    } catch (err) {
      timers.forEach(clearTimeout);
      const msg = err.response?.data?.detail || 'Training failed. Check data availability.';
      addToast(msg, 'error');
      setIsTraining(false);
    }
  };

  const handleExportReport = () => {
    const summary = data?.summary;
    if (!summary) return;
    const content = [
      'SmartEWS - Dashboard Report',
      `Generated: ${new Date().toLocaleString()}`,
      '',
      `Total Students: ${summary.total_students}`,
      `High Risk: ${summary.high_risk_count}`,
      `Medium Risk: ${summary.medium_risk_count}`,
      `Low Risk: ${summary.low_risk_count}`,
      `No Data: ${summary.no_data_count}`,
      '',
      'High Risk Students:',
      ...(data.high_risk_students || []).map(
        (s) => `  • ${s.full_name} (Grade ${s.grade}) — Risk Score: ${s.risk_score}/100`
      ),
    ].join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `smartews_report_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    addToast('Report exported successfully', 'success');
  };

  if (loading) return <DashboardSkeleton />;

  if (error) return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
        <AlertTriangle className="mx-auto mb-3 text-red-400" size={36} />
        <p className="font-semibold text-red-700 mb-1">Unable to load dashboard</p>
        <p className="text-red-500 text-sm mb-4">{error}</p>
        <button onClick={() => fetchDashboard()} className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors">
          Retry
        </button>
      </div>
    </div>
  );

  const s = data?.summary || {};
  const total = s.total_students || 1;

  return (
    <>
      {isTraining && <TrainProgress step={trainStep} metrics={trainMetrics} />}

      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-7">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-gray-900">Admin Dashboard</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                <Activity size={12} className="animate-pulse" /> System Live
              </span>
              {lastRefreshed && (
                <span className="text-xs text-gray-400">
                  Updated {lastRefreshed.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchDashboard()}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all"
            >
              <RefreshCw size={15} /> Refresh
            </button>
            <button
              onClick={handleExportReport}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-all"
            >
              <Download size={15} /> Export
            </button>
            <button
              onClick={handleTrainModel}
              disabled={isTraining}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-bold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-60 transition-all shadow-md shadow-blue-200"
            >
              <Brain size={16} /> Train Model
            </button>
          </div>
        </div>

        {/* Model Status Banner */}
        {!s.model_trained && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
            <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <p className="font-semibold text-amber-800 text-sm">Model not trained yet</p>
              <p className="text-amber-600 text-xs mt-0.5">
                Click <strong>Train Model</strong> to enable risk predictions for all students.
              </p>
            </div>
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <StatCard icon={Users} label="Total Students" value={s.total_students} color="blue" subtext="Enrolled" />
          <StatCard icon={AlertTriangle} label="High Risk" value={s.high_risk_count} color="red" subtext="Need attention" />
          <StatCard icon={TrendingUp} label="Medium Risk" value={s.medium_risk_count} color="amber" subtext="Being monitored" />
          <StatCard icon={CheckCircle} label="Low Risk" value={s.low_risk_count} color="green" subtext="On track" />
        </div>

        {/* Risk Distribution Bar */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
              <BarChart2 size={18} className="text-blue-500" /> Risk Distribution
            </h2>
            <div className="flex items-center gap-4 text-xs font-medium text-gray-500">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500" />High</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400" />Medium</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />Low</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-gray-300" />No Data</span>
            </div>
          </div>
          <div className="w-full h-4 flex rounded-full overflow-hidden gap-0.5">
            {s.high_risk_count > 0 && (
              <div style={{ width: `${(s.high_risk_count / total) * 100}%` }}
                className="bg-red-500 h-full transition-all" title={`High: ${s.high_risk_count}`} />
            )}
            {s.medium_risk_count > 0 && (
              <div style={{ width: `${(s.medium_risk_count / total) * 100}%` }}
                className="bg-amber-400 h-full transition-all" title={`Medium: ${s.medium_risk_count}`} />
            )}
            {s.low_risk_count > 0 && (
              <div style={{ width: `${(s.low_risk_count / total) * 100}%` }}
                className="bg-emerald-500 h-full transition-all" title={`Low: ${s.low_risk_count}`} />
            )}
            {s.no_data_count > 0 && (
              <div style={{ width: `${(s.no_data_count / total) * 100}%` }}
                className="bg-gray-200 h-full transition-all" title={`No Data: ${s.no_data_count}`} />
            )}
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-2">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* High Risk Students Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
            <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
              <AlertTriangle size={18} className="text-red-500" /> High Risk Students
            </h2>
            <span className="text-xs font-semibold bg-red-100 text-red-700 px-2.5 py-1 rounded-full">
              {data.high_risk_students?.length ?? 0} students
            </span>
          </div>

          {data.high_risk_students?.length === 0 ? (
            <EmptyState
              icon={CheckCircle}
              title="No high-risk students"
              description="All students are within safe risk thresholds."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/30">
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase tracking-wide">Student ID</th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase tracking-wide">Name</th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase tracking-wide">Grade</th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase tracking-wide">Risk Score</th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase tracking-wide"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data.high_risk_students.map((s) => (
                    <tr key={s.id} className="hover:bg-gray-50/70 transition-colors group">
                      <td className="py-3.5 px-6 text-sm text-gray-500 font-mono">{s.student_id}</td>
                      <td className="py-3.5 px-6 text-sm font-semibold text-gray-900">{s.full_name}</td>
                      <td className="py-3.5 px-6 text-sm text-gray-600">Grade {s.grade}</td>
                      <td className="py-3.5 px-6">
                        <RiskBadge level="HIGH" score={s.risk_score} />
                      </td>
                      <td className="py-3.5 px-6">
                        <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors ml-auto" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        {data.recent_alerts?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
              <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Activity size={18} className="text-amber-500" /> Recent Alerts
              </h2>
            </div>
            <div className="divide-y divide-gray-50">
              {data.recent_alerts.map((alert) => (
                <div key={alert.id} className="px-6 py-4 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{alert.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Student #{alert.student_id} · {new Date(alert.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full capitalize
                    ${alert.severity === 'critical' ? 'bg-red-100 text-red-700' : 
                      alert.severity === 'high' ? 'bg-orange-100 text-orange-700' : 
                      'bg-amber-100 text-amber-700'}`}>
                    {alert.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminDashboard;
