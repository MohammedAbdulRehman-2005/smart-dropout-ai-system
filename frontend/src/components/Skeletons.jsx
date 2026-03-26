// Skeleton shimmer pulse style — reused across pages
function Pulse({ className = '' }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}

export function DashboardSkeleton() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <Pulse className="h-9 w-64 rounded-xl" />
      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 flex items-center gap-5">
            <Pulse className="w-14 h-14 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Pulse className="h-3 w-24" />
              <Pulse className="h-8 w-16" />
            </div>
          </div>
        ))}
      </div>
      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4">
        <Pulse className="h-6 w-48 rounded-lg" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex gap-4">
            <Pulse className="h-4 w-20" />
            <Pulse className="h-4 flex-1" />
            <Pulse className="h-4 w-16" />
            <Pulse className="h-4 w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ProfileSkeleton() {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-gray-100 space-y-4">
        <Pulse className="h-7 w-48 rounded-xl" />
        <div className="flex gap-4">
          <Pulse className="h-10 flex-1 rounded-xl" />
          <Pulse className="h-10 w-32 rounded-xl" />
        </div>
      </div>
      <div className="bg-white p-6 rounded-2xl border border-gray-100">
        <Pulse className="h-24 w-full rounded-xl" />
      </div>
      <div className="grid grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 space-y-3">
            <Pulse className="h-5 w-32 rounded" />
            {[...Array(4)].map((_, j) => <Pulse key={j} className="h-3 w-full rounded" />)}
          </div>
        ))}
      </div>
    </div>
  );
}

export function TableRowSkeleton({ rows = 5 }) {
  return (
    <>
      {[...Array(rows)].map((_, i) => (
        <tr key={i} className="border-b border-gray-50">
          {[...Array(4)].map((_, j) => (
            <td key={j} className="py-3 px-4">
              <Pulse className="h-4 rounded" style={{ width: `${60 + Math.random() * 40}%` }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
