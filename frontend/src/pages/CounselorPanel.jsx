import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { useToast } from '../hooks/useToast';
import EmptyState from '../components/EmptyState';
import { Bell, AlertOctagon, CheckCircle, RefreshCw } from 'lucide-react';

const CounselorPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);
  const { addToast } = useToast();

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await client.get('/alerts?unresolved_only=true');
      setAlerts(res.data.alerts || []);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to fetch alerts';
      addToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const resolveAlert = async (id) => {
    setResolvingId(id);
    try {
      await client.post(`/alerts/${id}/resolve`);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      addToast('Alert resolved successfully ✓', 'success');
    } catch (err) {
      addToast('Failed to resolve alert. Please try again.', 'error');
    } finally {
      setResolvingId(null);
    }
  };

  const SEVERITY_STYLES = {
    critical: 'bg-red-50 text-red-700 border-red-200',
    high: 'bg-orange-50 text-orange-700 border-orange-200',
    medium: 'bg-amber-50 text-amber-700 border-amber-200',
    low: 'bg-blue-50 text-blue-700 border-blue-200',
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-50 rounded-xl">
            <Bell size={26} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">Counselor Panel</h1>
            <p className="text-gray-400 text-sm">Manage active student intervention alerts</p>
          </div>
        </div>
        <button
          onClick={fetchAlerts}
          className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-all"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Alerts Panel */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
          <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
            <AlertOctagon size={18} className="text-red-500" />
            Active Interventions Required
          </h2>
          <span className={`text-xs font-bold px-3 py-1 rounded-full border
            ${alerts.length > 0 ? 'bg-red-100 text-red-700 border-red-200' : 'bg-gray-100 text-gray-500 border-gray-200'}`}>
            {loading ? '…' : `${alerts.length} alerts`}
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <span className="inline-block w-8 h-8 border-3 border-gray-200 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-sm text-gray-400 mt-3">Loading alerts…</p>
          </div>
        ) : alerts.length === 0 ? (
          <EmptyState
            icon={CheckCircle}
            title="All caught up!"
            description="There are no active alerts requiring intervention right now."
          />
        ) : (
          <div className="divide-y divide-gray-50">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-gray-50/50 transition-colors"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-gray-900">{alert.title}</h3>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border flex-shrink-0
                      ${SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.medium}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">{alert.message}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-400 font-mono">Student #{alert.student_id}</span>
                    <span className="text-gray-200">|</span>
                    <span className="text-xs text-gray-400">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => resolveAlert(alert.id)}
                  disabled={resolvingId === alert.id}
                  className="flex-shrink-0 flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200 disabled:opacity-50 transition-all text-sm font-semibold whitespace-nowrap"
                >
                  {resolvingId === alert.id ? (
                    <span className="w-4 h-4 border-2 border-gray-200 border-t-emerald-600 rounded-full animate-spin" />
                  ) : (
                    <CheckCircle size={16} className="text-emerald-500" />
                  )}
                  {resolvingId === alert.id ? 'Resolving…' : 'Mark Resolved'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CounselorPanel;
