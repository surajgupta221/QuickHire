import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../services/api';

//GOOGLE_CLIENT_ID=your-google-client-id

export default function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMessage, setForgotMessage] = useState('');
  const [form, setForm] = useState({
    full_name: '', email: '', password: '',
    company_name: '', phone: ''
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = isLogin
        ? await loginUser(form.email, form.password)
        : await registerUser(form);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
    };

    const handleForgotPassword = async (e) => {
    e.preventDefault();
    setForgotLoading(true);
    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/forgot-password?email=${forgotEmail}`
      );
      setForgotMessage(res.data.message);
    } catch (err) {
      setForgotMessage('Error: ' + (err.response?.data?.detail || 'Something went wrong'));
    } finally {
      setForgotLoading(false);
    }
    };

    const handleGoogleSuccess = async (credentialResponse) => {
      try {
        const res = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/google-login?google_token=${credentialResponse.credential}`
        );
        localStorage.setItem('token', res.data.access_token);
        localStorage.setItem('user', JSON.stringify(res.data.user));
        navigate('/dashboard');
      } catch (err) {
        setError('Google login failed. Please try again.');
      }
    };
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-900">⚡ QuickHire</h1>
          <p className="text-gray-500 mt-2">AI-Powered Recruitment Assistant</p>
        </div>

        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 rounded-lg font-semibold transition-all ${isLogin ? 'bg-white text-blue-900 shadow' : 'text-gray-500'}`}>
            Login
          </button>
          <button onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 rounded-lg font-semibold transition-all ${!isLogin ? 'bg-white text-blue-900 shadow' : 'text-gray-500'}`}>
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Full Name</label>
                <input name="full_name" value={form.full_name} onChange={handleChange}
                  placeholder="Your full name" required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Company Name</label>
                <input name="company_name" value={form.company_name} onChange={handleChange}
                  placeholder="Your company"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Phone</label>
                <input name="phone" value={form.phone} onChange={handleChange}
                  placeholder="+91 9876543210"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </>
          )}

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
            <input type="email" name="email" value={form.email} onChange={handleChange}
              placeholder="you@company.com" required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div className="mb-4">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google login failed')}
              width="350"
              text="continue_with"
              shape="rectangular"
            />
            <div className="flex items-center gap-3 my-4">
              <hr className="flex-1" />
              <span className="text-gray-400 text-sm">or</span>
              <hr className="flex-1" />
            </div>
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
            <input type="password" name="password" value={form.password} onChange={handleChange}
              placeholder="••••••••" required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              ❌ {error}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-blue-900 text-white rounded-lg font-bold text-lg hover:bg-blue-800 disabled:opacity-50 transition-all">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Connecting to server... (first load takes ~30s)
              </span>
            ) : isLogin ? '🚀 Login' : '✅ Create Account'}
          </button>
        </form>

        <p className="text-center text-gray-500 text-sm mt-6">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button onClick={() => setIsLogin(!isLogin)} className="text-blue-900 font-semibold hover:underline">
            {isLogin ? 'Register here' : 'Login here'}
          </button>
        </p>

        {/* Forgot Password Link */}
{isLogin && !showForgot && (
  <p className="text-center text-sm mt-4">
    <button
      type="button"
      onClick={() => setShowForgot(true)}
      className="text-blue-600 hover:underline">
      Forgot Password?
    </button>
  </p>
)}

{/* Forgot Password Form */}
{showForgot && (
  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
    <h3 className="font-bold text-blue-900 mb-3">Reset Password</h3>
    {forgotMessage ? (
      <div className="text-green-700 bg-green-50 p-3 rounded-lg text-sm">
        ✅ {forgotMessage}
        <button
          onClick={() => { setShowForgot(false); setForgotMessage(''); }}
          className="block mt-2 text-blue-600 hover:underline text-xs">
          Back to Login
        </button>
      </div>
    ) : (
      <form onSubmit={handleForgotPassword}>
        <input
          type="email"
          value={forgotEmail}
          onChange={e => setForgotEmail(e.target.value)}
          placeholder="Enter your email"
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={forgotLoading}
            className="flex-1 py-2 bg-blue-900 text-white rounded-lg text-sm font-semibold hover:bg-blue-800 disabled:opacity-50">
            {forgotLoading ? '⏳ Sending...' : 'Send Reset Link'}
          </button>
          <button
            type="button"
            onClick={() => setShowForgot(false)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    )}
  </div>
)}
      </div>
    </div>
  );
}