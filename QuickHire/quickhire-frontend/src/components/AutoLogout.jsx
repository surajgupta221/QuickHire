import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startAutoLogout, resetAutoLogout, clearTimers } from '../utils/autoLogout';

export default function AutoLogout() {
  const navigate = useNavigate();
  const [showWarning, setShowWarning] = useState(false);
  const [countdown, setCountdown] = useState(120);

  const handleLogout = () => {
    clearTimers();
    localStorage.clear();
    navigate('/login');
  };

  const handleStayLoggedIn = () => {
    setShowWarning(false);
    setCountdown(120);
    resetAutoLogout(handleLogout, () => setShowWarning(true));
  };

  useEffect(() => {
    // Start timer
    startAutoLogout(handleLogout, () => setShowWarning(true));

    // Reset on any user activity
    const resetOnActivity = () => {
      resetAutoLogout(handleLogout, () => setShowWarning(true));
      setShowWarning(false);
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => document.addEventListener(event, resetOnActivity));

    return () => {
      clearTimers();
      events.forEach(event => document.removeEventListener(event, resetOnActivity));
    };
  }, []);

  // Countdown timer when warning shows
  useEffect(() => {
    if (!showWarning) return;
    setCountdown(120);
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          handleLogout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [showWarning]);

  if (!showWarning) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          <div className="text-5xl mb-4">⏰</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Session Expiring Soon
          </h2>
          <p className="text-gray-500 mb-4">
            You'll be logged out in{' '}
            <strong className="text-red-500 text-xl">{countdown}s</strong>{' '}
            due to inactivity.
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
            <div
              className="bg-red-500 h-2 rounded-full transition-all"
              style={{ width: `${(countdown / 120) * 100}%` }}
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleLogout}
              className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-600 hover:bg-gray-50 font-semibold">
              Logout Now
            </button>
            <button
              onClick={handleStayLoggedIn}
              className="flex-1 py-3 bg-blue-900 text-white rounded-xl font-bold hover:bg-blue-800">
              Stay Logged In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}