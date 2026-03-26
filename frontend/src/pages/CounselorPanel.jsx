import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Bell, AlertOctagon, CheckCircle } from 'lucide-react';

const CounselorPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const res = await client.get('/alerts?unresolved_only=true');
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const resolveAlert = async (id) => {
    try {
      await client.post(`/alerts/${id}/resolve`);
      setAlerts(alerts.filter(a => a.id !== id));
    } catch (err) {
      console.error('Failed to resolve alert', err);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500 flex items-center justify-center space-x-2"><Bell className="animate-bounce" /><span>Loading alerts...</span></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
           <Bell size={28} />
        </div>
        <h1 className="text-3xl font-bold text-gray-800">Counselor Panel</h1>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-700 flex items-center">
                <AlertOctagon size={20} className="mr-2 text-red-500" />
                Active High-Risk Interventions
            </h2>
            <span className="bg-red-100 text-red-700 py-1 px-3 rounded-full text-xs font-bold shadow-sm">{alerts.length} ACTION REQUIRED</span>
        </div>
        
        <div className="divide-y divide-gray-100">
          {alerts.map(alert => (
            <div key={alert.id} className="p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center hover:bg-gray-50/50 transition-colors">
              <div className="space-y-1 max-w-2xl">
                <div className="flex items-center space-x-2">
                    <h3 className="text-md font-bold text-gray-900">{alert.title}</h3>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${alert.severity === 'critical' ? 'bg-red-50 text-red-600 border-red-200' : 'bg-orange-50 text-orange-600 border-orange-200'}`}>
                        {alert.severity}
                    </span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">{alert.message}</p>
                <div className="flex items-center space-x-4 mt-2">
                    <span className="text-xs text-gray-400 font-medium tracking-wide border-r pr-4 border-gray-200">
                        Student DB ID: {alert.student_id}
                    </span>
                    <span className="text-xs text-gray-400">
                        Generated: {new Date(alert.created_at).toLocaleString()}
                    </span>
                </div>
              </div>
              
              <button
                onClick={() => resolveAlert(alert.id)}
                className="mt-4 sm:mt-0 px-5 py-2 flex items-center space-x-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-green-50 hover:text-green-700 hover:border-green-300 transition-all font-medium whitespace-nowrap"
              >
                <CheckCircle size={18} className="text-green-500" />
                <span>Mark Resolved</span>
              </button>
            </div>
          ))}

          {alerts.length === 0 && (
            <div className="p-12 text-center text-gray-400">
               <CheckCircle size={48} className="mx-auto mb-4 text-green-200" />
               <p className="font-medium text-gray-600">All caught up!</p>
               <p className="text-sm">There are no active alerts requiring intervention.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CounselorPanel;
