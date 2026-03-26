export function RiskBadge({ level, score }) {
  const styles = {
    HIGH: 'bg-red-100 text-red-700 border-red-200 ring-red-200',
    MEDIUM: 'bg-amber-100 text-amber-700 border-amber-200 ring-amber-200',
    LOW: 'bg-emerald-100 text-emerald-700 border-emerald-200 ring-emerald-200',
  };
  const icons = { HIGH: '🔴', MEDIUM: '🟡', LOW: '🟢' };
  const norm = level?.toUpperCase() || 'UNKNOWN';
  const style = styles[norm] || 'bg-gray-100 text-gray-500 border-gray-200';
  const icon = icons[norm] || '⚪';

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ring-1 ring-offset-1 ${style}`}
    >
      {icon} {norm}
      {score !== undefined && <span className="ml-1 opacity-70">({score}%)</span>}
    </span>
  );
}

export default RiskBadge;
