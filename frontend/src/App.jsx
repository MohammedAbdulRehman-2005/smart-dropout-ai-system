import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import React, { useEffect } from 'react';
import AdminDashboard from './pages/AdminDashboard';
import StudentProfile from './pages/StudentProfile';
import CounselorPanel from './pages/CounselorPanel';
import { LayoutDashboard, UserSearch, UserCheck } from 'lucide-react';
import axios from 'axios';

const App = () => {
  useEffect(() => {
    if (!localStorage.getItem('token')) {
      const formData = new URLSearchParams();
      formData.append('username', 'admin@school.edu');
      formData.append('password', 'admin123');
      axios.post('http://localhost:8000/auth/login', formData)
        .then(res => {
           localStorage.setItem('token', res.data.access_token);
           window.location.reload();
        })
        .catch(console.error);
    }
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100 flex flex-col">
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <span className="text-2xl font-black text-blue-600 tracking-tight flex items-center">
                   <LayoutDashboard className="mr-2" />
                   SmartEWS
                </span>
                <div className="ml-10 flex space-x-8">
                  <Link to="/admin" className="text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md font-medium flex items-center transition-colors">
                     <LayoutDashboard size={18} className="mr-2"/> Admin
                  </Link>
                  <Link to="/counselor" className="text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md font-medium flex items-center transition-colors">
                     <UserCheck size={18} className="mr-2"/> Counselor
                  </Link>
                  <Link to="/student" className="text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md font-medium flex items-center transition-colors">
                     <UserSearch size={18} className="mr-2"/> Student Search
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/admin" replace />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/counselor" element={<CounselorPanel />} />
            <Route path="/student" element={<StudentProfile />} />
          </Routes>
        </main>
        
        <footer className="bg-white border-t py-4 text-center text-gray-400 text-sm">
           Smart School Dropout Early Warning System &copy; 2026
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
