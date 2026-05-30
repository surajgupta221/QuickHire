import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AutoLogout from '../components/AutoLogout';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function LinkedInSearch() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    job_title: '',
    location: '',
    must_have_skills: '',
    good_to_have_skills: '',
    num_results: 10
  });

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_URL}/linkedin/search`, {
        params: { ...form, token }
      });
      setResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getXrayQuery = async () => {
    try {
      const res = await axios.get(`${API_URL}/linkedin/xray-query`, {
        params: {
          job_title: form.job_title,
          location: form.location,
          must_have_skills: form.must_have_skills,
          good_to_have_skills: form.good_to_have_skills,
          token
        }
      });
      window.open(res.data.google_search_url, '_blank');
    } catch (err) {
      // Fallback — build query manually
      let query = `site:linkedin.com/in "${form.job_title}"`;
      if (form.location) query += ` "${form.location}"`;
      if (form.must_have_skills) query += ` "${form.must_have_skills.split(',')[0].trim()}"`;
      const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
      window.open(url, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AutoLogout />

      <nav className="bg-blue-900 text-white px-6 py-4 flex items-center gap-4 shadow-lg">
        <button onClick={() => navigate('/dashboard')}
          className="hover:text-blue-200 transition-colors">
          ← Dashboard
        </button>
        <span className="text-blue-300">|</span>
        <h1 className="text-xl font-bold">🔍 LinkedIn Candidate Search</h1>
      </nav>

      <div className="max-w-4xl mx-auto p-6">
        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm text-blue-800">
          <strong>How it works:</strong> Enter job details → AI builds an X-Ray search query →
          finds matching LinkedIn profiles via Google Custom Search.
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-2xl p-8 shadow-sm mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Find Candidates on LinkedIn
          </h2>
          <p className="text-gray-500 text-sm mb-6">
            Uses Google X-Ray search to find matching LinkedIn profiles
          </p>

          <form onSubmit={handleSearch}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Job Title *
                </label>
                <input
                  value={form.job_title}
                  onChange={e => setForm({...form, job_title: e.target.value})}
                  placeholder="e.g. Python Backend Developer"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Location
                </label>
                <input
                  value={form.location}
                  onChange={e => setForm({...form, location: e.target.value})}
                  placeholder="e.g. Bangalore"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold mb-2"
                  style={{color: '#DC2626'}}>
                  🔴 Must Have Skills
                </label>
                <input
                  value={form.must_have_skills}
                  onChange={e => setForm({...form, must_have_skills: e.target.value})}
                  placeholder="Python, FastAPI, PostgreSQL"
                  className="w-full px-4 py-3 border-2 border-red-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-300 bg-red-50"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2"
                  style={{color: '#16A34A'}}>
                  🟢 Good to Have Skills
                </label>
                <input
                  value={form.good_to_have_skills}
                  onChange={e => setForm({...form, good_to_have_skills: e.target.value})}
                  placeholder="Docker, AWS, Redis"
                  className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-300 bg-green-50"
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Results
              </label>
              <select
                value={form.num_results}
                onChange={e => setForm({...form, num_results: parseInt(e.target.value)})}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value={5}>5 profiles</option>
                <option value={10}>10 profiles</option>
                <option value={20}>20 profiles</option>
              </select>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                ❌ {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={getXrayQuery}
                disabled={!form.job_title}
                className="px-6 py-3 border-2 border-blue-900 text-blue-900 rounded-lg font-semibold hover:bg-blue-50 transition-all disabled:opacity-50">
                🔗 Open X-Ray on Google
              </button>
              <button
                type="submit"
                disabled={loading || !form.job_title}
                className="flex-1 py-3 bg-blue-900 text-white rounded-lg font-bold hover:bg-blue-800 disabled:opacity-50 transition-all">
                {loading
                  ? '⏳ Searching LinkedIn...'
                  : '🔍 Search Candidates'}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {results && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-800">
                {results.total_found > 0
                  ? `Found ${results.total_found} Candidates`
                  : 'No Candidates Found'}
              </h3>
              {results.xray_query && (
                <button
                  onClick={getXrayQuery}
                  className="text-xs text-blue-600 hover:underline">
                  🔗 Open in Google
                </button>
              )}
            </div>

            {results.error && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
                ⚠️ {results.error}
                <br />
                <button onClick={getXrayQuery}
                  className="text-blue-600 hover:underline mt-2 text-xs">
                  Try manual Google X-Ray search →
                </button>
              </div>
            )}

            <div className="space-y-4">
              {(results.profiles || []).map((p, i) => (
                <div key={i}
                  className="border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-900 text-lg flex-shrink-0">
                        {p.name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-800">{p.name}</h4>
                        {p.current_role && (
                          <p className="text-sm text-gray-500">{p.current_role}</p>
                        )}
                      </div>
                    </div>
                    <a
                      href={p.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-800 transition-all flex-shrink-0">
                      View Profile →
                    </a>
                  </div>
                  {p.snippet && (
                    <p className="text-sm text-gray-500 mt-3 leading-relaxed border-t border-gray-100 pt-3">
                      {p.snippet}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {results.profiles?.length === 0 && !results.error && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-5xl mb-4">🔍</p>
                <p className="text-lg font-medium mb-2">No profiles found</p>
                <p className="text-sm text-gray-400 mb-4">
                  Try different keywords or broader location
                </p>
                <button
                  onClick={getXrayQuery}
                  className="bg-blue-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-800 transition-all">
                  Search manually on Google →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}