export function StatCard({ icon: Icon, label, value, color = 'blue', subtext }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-5 hover:shadow-md transition-shadow">
      <div className={`p-3.5 rounded-xl flex-shrink-0 ${colorMap[color] || colorMap.blue}`}>
        <Icon size={28} />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-500 truncate">{label}</p>
        <p className="text-3xl font-black text-gray-900 mt-0.5">{value ?? '—'}</p>
        {subtext && <p className="text-xs text-gray-400 mt-0.5">{subtext}</p>}
      </div>
    </div>
  );
}

export default StatCard;
