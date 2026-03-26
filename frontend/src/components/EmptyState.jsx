export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {Icon && (
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center">
          <Icon size={32} className="text-gray-300" />
        </div>
      )}
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-400 max-w-xs leading-relaxed">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export default EmptyState;
