export const getRiskColor = (level) => {
  switch (level?.toUpperCase()) {
    case 'HIGH': return 'text-red-700 bg-red-100 border-red-200';
    case 'MEDIUM': return 'text-orange-700 bg-orange-100 border-orange-200';
    case 'LOW': return 'text-green-700 bg-green-100 border-green-200';
    default: return 'text-gray-700 bg-gray-100 border-gray-200';
  }
};

export const getRiskLabel = (level) => {
  switch (level?.toUpperCase()) {
    case 'HIGH': return '🔴 HIGH RISK';
    case 'MEDIUM': return '🟡 MEDIUM RISK';
    case 'LOW': return '🟢 LOW RISK';
    default: return 'Unknown Risk';
  }
};
