import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../services/api';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    full_name: '',
    email: '',
    password: '',
    company_name: '',
    phone: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'phone') {
      const digits = value.replace(/\D/g, '').slice(0, 10);
      setForm({ ...form, phone: digits });
    } else {
      setForm({ ...form, [name]: value });
    }
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!isLogin && form.phone && form.phone.length !== 10) {
      setError('Phone number must be exactly 10 digits');
      setLoading(false);
      return;
    }

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

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_URL}/auth/google-login`, {
        google_token: credentialResponse.credential
      });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Google sign-in failed. Please try again.');
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setForgotLoading(true);
    try {
      const res = await axios.post(
        `${API_URL}/auth/forgot-password?email=${forgotEmail}`
      );
      setForgotMessage(res.data.message);
    } catch (err) {
      setForgotMessage('Error sending reset link. Please try again.');
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">

        {/* Logo */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-blue-900">⚡ QuickHire</h1>
          <p className="text-gray-500 mt-1 text-sm">AI-Powered Recruitment Assistant</p>
        </div>

        {/* Tabs */}
        <div className="flex mb-5 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => { setIsLogin(true); setError(''); }}
            className={`flex-1 py-2 rounded-lg font-semibold transition-all text-sm ${
              isLogin ? 'bg-white text-blue-900 shadow' : 'text-gray-500'
            }`}>
            Login
          </button>
          <button
            onClick={() => { setIsLogin(false); setError(''); }}
            className={`flex-1 py-2 rounded-lg font-semibold transition-all text-sm ${
              !isLogin ? 'bg-white text-blue-900 shadow' : 'text-gray-500'
            }`}>
            Register
          </button>
        </div>

        {/* Google Login Button */}
        <div className="mb-4">
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google sign-in failed. Please try again.')}
              text={isLogin ? 'signin_with' : 'signup_with'}
              shape="rectangular"
              theme="outline"
              size="large"
              width="368"
            />
          </div>

          <div className="flex items-center gap-3 my-4">
            <hr className="flex-1 border-gray-200" />
            <span className="text-gray-400 text-xs font-medium">
              or continue with email
            </span>
            <hr className="flex-1 border-gray-200" />
          </div>
        </div>

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div className="mb-3">
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={form.full_name}
                  onChange={handleChange}
                  placeholder="Suraj Kumar Gupta"
                  required
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
              <div className="mb-3">
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={form.company_name}
                  onChange={handleChange}
                  placeholder="Your Company"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
              <div className="mb-3">
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Phone (10 digits)
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  placeholder="9876543210"
                  maxLength={10}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
                {form.phone && form.phone.length > 0 && form.phone.length !== 10 && (
                  <p className="text-red-500 text-xs mt-1">
                    ⚠️ Must be exactly 10 digits ({form.phone.length}/10)
                  </p>
                )}
              </div>
            </>
          )}

          <div className="mb-3">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@company.com"
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Password *
            </label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {error && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              ❌ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-900 text-white rounded-lg font-bold text-sm hover:bg-blue-800 disabled:opacity-50 transition-all">
            {loading
              ? '⏳ Please wait...'
              : isLogin ? '🚀 Login' : '✅ Create Account'}
          </button>
        </form>

        {/* Forgot Password */}
        {isLogin && (
          <div className="mt-4">
            {!showForgot ? (
              <p className="text-center text-sm text-gray-500">
                <button
                  onClick={() => setShowForgot(true)}
                  className="text-blue-600 hover:underline font-medium">
                  Forgot Password?
                </button>
              </p>
            ) : (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h3 className="font-bold text-blue-900 mb-3 text-sm">
                  Reset Password
                </h3>
                {forgotMessage ? (
                  <div>
                    <p className="text-green-700 bg-green-50 p-3 rounded-lg text-sm">
                      ✅ {forgotMessage}
                    </p>
                    <button
                      onClick={() => { setShowForgot(false); setForgotMessage(''); }}
                      className="text-blue-600 text-xs mt-2 hover:underline">
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>
        )}

        <p className="text-center text-gray-500 text-xs mt-4">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            className="text-blue-900 font-semibold hover:underline">
            {isLogin ? 'Register here' : 'Login here'}
          </button>
        </p>
      </div>
    </div>
  );
}