import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Users, AlertTriangle } from 'lucide-react';

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/admin/dashboard')
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch dashboard', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-600">Loading dashboard...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Error loading dashboard</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-full">
            <Users size={32} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Total Students</p>
            <p className="text-3xl font-bold text-gray-900">{data.summary.total_students}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-red-50 text-red-600 rounded-full">
            <AlertTriangle size={32} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">High Risk Students</p>
            <p className="text-3xl font-bold text-gray-900">{data.summary.high_risk_count}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-center">
            <p className="text-sm font-medium text-gray-500 mb-3">Risk Distribution</p>
            <div className="w-full h-4 flex rounded-full overflow-hidden">
               <div style={{width: `${(data.summary.high_risk_count / data.summary.total_students) * 100}%`}} className="bg-red-500 h-full" title="High Risk"></div>
               <div style={{width: `${(data.summary.medium_risk_count / data.summary.total_students) * 100}%`}} className="bg-orange-400 h-full" title="Medium Risk"></div>
               <div style={{width: `${(data.summary.low_risk_count / data.summary.total_students) * 100}%`}} className="bg-green-500 h-full" title="Low Risk"></div>
            </div>
            <div className="flex justify-between text-xs mt-2 text-gray-500 font-medium">
                <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-red-500 mr-1"></span>{data.summary.high_risk_count} High</span>
                <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-orange-400 mr-1"></span>{data.summary.medium_risk_count} Med</span>
                <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>{data.summary.low_risk_count} Low</span>
            </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">High Risk Students</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-3 px-4 text-sm font-semibold text-gray-600">Student ID</th>
                <th className="py-3 px-4 text-sm font-semibold text-gray-600">Name</th>
                <th className="py-3 px-4 text-sm font-semibold text-gray-600">Grade</th>
                <th className="py-3 px-4 text-sm font-semibold text-gray-600">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {data.high_risk_students.map(s => (
                <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-600">{s.student_id}</td>
                  <td className="py-3 px-4 text-sm font-medium text-gray-900">{s.full_name}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{s.grade}</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          style={{ backgroundColor: `${s.risk_color}20`, color: s.risk_color }}>
                      {s.risk_score} / 100
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.high_risk_students.length === 0 && (
            <p className="text-center text-gray-500 py-4">No high risk students found.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
