import { ShieldOff, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Unauthorized = () => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-red-50 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-red-100 border border-red-200 flex items-center justify-center">
          <ShieldOff size={36} className="text-red-500" />
        </div>
        <h1 className="text-3xl font-black text-gray-900 mb-2">Access Denied</h1>
        <p className="text-gray-500 mb-2 text-sm">
          You don't have permission to view this page.
        </p>
        <p className="text-gray-400 text-xs mb-7">
          Contact your system administrator if you believe this is an error.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-5 py-2.5 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 font-semibold text-sm transition-colors"
          >
            <ArrowLeft size={16} /> Go Back
          </button>
          <button
            onClick={() => navigate('/admin')}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-semibold text-sm transition-colors"
          >
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default Unauthorized;
