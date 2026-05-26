import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory } from '../services/api';
import AutoLogout from '../components/AutoLogout';

export default function Dashboard() {
  const navigate = useNavigate();
  const [screenings, setScreenings] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const token = localStorage.getItem('token');

  useEffect(() => {
    getHistory(token)
      .then(res => setScreenings(res.data.screenings || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const logout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <h1 className="text-xl font-bold">⚡ QuickHire</h1>
        <div className="flex items-center gap-4">
          <span className="text-blue-200 text-sm">
            👤 {user.full_name} |
            🎯 Credits: <strong className="text-white">{user.screening_credits}</strong> |
            📋 Plan: <strong className="text-yellow-300 uppercase">{user.plan}</strong>
            <button onClick={() => navigate('/pricing')}
  className="bg-yellow-500 hover:bg-yellow-900 px-4 py-2 rounded-lg text-sm font-bold transition-all">
  ⚡Upgrade Plan
</button>
          </span>
          <button onClick={logout}
            className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg text-sm font-semibold transition-all">
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border-l-4 border-blue-500">
            <p className="text-gray-500 text-sm">Total Screenings</p>
            <p className="text-3xl font-bold text-blue-900">{screenings.length}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm border-l-4 border-green-500">
            <p className="text-gray-500 text-sm">Credits Remaining</p>
            <p className="text-3xl font-bold text-green-700">{user.screening_credits}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm border-l-4 border-purple-500">
            <p className="text-gray-500 text-sm">Current Plan</p>
            <p className="text-3xl font-bold text-purple-700 uppercase">{user.plan}</p>
          </div>
        </div>

        {/* New Screening Button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Recent Screenings</h2>
          <button onClick={() => navigate('/new-screening')}
            className="bg-blue-900 hover:bg-blue-800 text-white px-6 py-3 rounded-xl font-bold shadow-lg transition-all flex items-center gap-2">
            ➕ New Screening
          </button>
        </div>

        {/* Screenings List */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : screenings.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center shadow-sm">
            <p className="text-5xl mb-4">🔍</p>
            <h3 className="text-xl font-bold text-gray-700 mb-2">No screenings yet</h3>
            <p className="text-gray-500 mb-6">Start your first AI-powered candidate screening</p>
            <button onClick={() => navigate('/new-screening')}
              className="bg-blue-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-800 transition-all">
              Start First Screening
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {screenings.map(s => (
              <div key={s.id} onClick={() => navigate(`/results/${s.id}`)}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md cursor-pointer transition-all border border-gray-100 hover:border-blue-200">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">{s.job_title}</h3>
                    <p className="text-gray-500 text-sm mt-1">📍 {s.location || 'Not specified'}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      s.status === 'completed' ? 'bg-green-100 text-green-700' :
                      s.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'}`}>
                      {s.status?.toUpperCase()}
                    </span>
                    <p className="text-gray-500 text-sm mt-2">👥 {s.total_candidates} candidates</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div> <AutoLogout />
    </div>
  );
}