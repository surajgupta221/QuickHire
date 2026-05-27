import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const IDLE_TIMEOUT = 5 * 60 * 1000;      // 5 minutes
const WARNING_BEFORE = 2 * 60 * 1000;      // warn 2 min before
const WARNING_TIMEOUT = IDLE_TIMEOUT - WARNING_BEFORE;

export default function AutoLogout() {
  const navigate = useNavigate();
  const [showWarning, setShowWarning] = useState(false);
  const [countdown, setCountdown] = useState(120);

  const logout = useCallback(() => {
    localStorage.clear();
    navigate('/login');
  }, [navigate]);

  useEffect(() => {
    let warningTimer;
    let logoutTimer;
    let countdownInterval;

    const resetTimers = () => {
      // Clear existing
      clearTimeout(warningTimer);
      clearTimeout(logoutTimer);
      clearInterval(countdownInterval);
      setShowWarning(false);
      setCountdown(120);

      // Set warning timer
      warningTimer = setTimeout(() => {
        setShowWarning(true);
        setCountdown(120);

        // Start countdown
        countdownInterval = setInterval(() => {
          setCountdown(prev => {
            if (prev <= 1) {
              clearInterval(countdownInterval);
              logout();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);

      }, WARNING_TIMEOUT);

      // Set logout timer
      logoutTimer = setTimeout(() => {
        logout();
      }, IDLE_TIMEOUT);
    };

    // Start timers
    resetTimers();

    // Reset on user activity
    const events = [
      'mousedown', 'mousemove', 'keydown',
      'scroll', 'touchstart', 'click', 'keypress'
    ];

    const handleActivity = () => {
      if (!showWarning) {
        resetTimers();
      }
    };

    events.forEach(e => window.addEventListener(e, handleActivity));

    return () => {
      clearTimeout(warningTimer);
      clearTimeout(logoutTimer);
      clearInterval(countdownInterval);
      events.forEach(e => window.removeEventListener(e, handleActivity));
    };
  }, [logout]);

  const stayLoggedIn = () => {
    setShowWarning(false);
    setCountdown(120);
    // Trigger activity reset by dispatching event
    window.dispatchEvent(new Event('mousedown'));
  };

  if (!showWarning) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl animate-bounce-once">
        <div className="text-center">
          <div className="text-5xl mb-4">⏰</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">
            Session Expiring!
          </h2>
          <p className="text-gray-500 mb-4 text-sm">
            You'll be logged out in{' '}
            <strong className="text-red-500 text-2xl">{countdown}s</strong>
            {' '}due to inactivity
          </p>

          {/* Progress bar */}
          <div className="w-full bg-gray-100 rounded-full h-3 mb-6">
            <div
              className="bg-red-500 h-3 rounded-full transition-all duration-1000"
              style={{ width: `${(countdown / 120) * 100}%` }}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={logout}
              className="flex-1 py-2.5 border-2 border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 font-semibold text-sm">
              Logout
            </button>
            <button
              onClick={stayLoggedIn}
              className="flex-1 py-2.5 bg-blue-900 text-white rounded-xl font-bold hover:bg-blue-800 text-sm">
              Stay Logged In ✓
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}