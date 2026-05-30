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

  const handleSearch = (e) => {
  if (e && e.preventDefault) e.preventDefault();
  console.log("LinkedIn Custom Search triggered inside LinkedInSearch panel!");


  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    console.log('LinkedIn search clicked', {
      job_title: form.job_title,
      location: form.location,
      must_have_skills: form.must_have_skills,
      good_to_have_skills: form.good_to_have_skills,
      num_results: form.num_results
    });

    try {
      const res = await axios.get(`${API_URL}/linkedin/search`, {
        params: { ...form, token }
      });
      console.log('LinkedIn search response', res.data);
      setResults(res.data);
    } catch (err) {
      console.error('LinkedIn search error', err);
      setError(err.response?.data?.detail || 'Search failed');
    } finally { setLoading(false); }
  };

  const getXrayQuery = async () => {
    console.log('Requesting X-Ray query', {
      job_title: form.job_title,
      location: form.location,
      must_have_skills: form.must_have_skills,
      good_to_have_skills: form.good_to_have_skills
    });
    // Simple structural string builder fallback
      let query = "site:://linkedin.com ";
      if (title) query += `"${title}" `;
      if (location) query += `"${location}" `;
      if (skills) query += `"${skills}"`;
    
      return query.trim();
    
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
      
      console.log('X-Ray query response', res.data);
      window.open(res.data.google_search_url, '_blank');
    } catch (err) {
      console.error('X-Ray query error', err);
      setError('Failed to generate query');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <h1 className="text-2xl font-bold text-blue-900">LinkedIn Search</h1>
      <p className="mt-2 text-gray-600">Find candidates from LinkedIn.</p>
    </div>
  );
}
{(
    <div className="min-h-screen bg-gray-50">
      <AutoLogout />
      <nav className="bg-blue-900 text-white px-6 py-4 flex items-center gap-4 shadow-lg">
        <button onClick={() => navigate('/dashboard')} className="hover:text-blue-200">
          ← Dashboard
        </button>
        <h1 className="text-xl font-bold">🔍 LinkedIn Candidate Search</h1>
      </nav>

      <div className="max-w-4xl mx-auto p-6">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-semibold mb-2" style={{color:'#DC2626'}}>
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
                <label className="block text-sm font-semibold mb-2" style={{color:'#16A34A'}}>
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

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                ❌ {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={getXrayQuery}
                className="px-6 py-3 border-2 border-blue-900 text-blue-900 rounded-lg font-semibold hover:bg-blue-50 transition-all">
                🔗 Open X-Ray Search on Google
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 bg-blue-900 text-white rounded-lg font-bold hover:bg-blue-800 disabled:opacity-50 transition-all">
                {loading ? '⏳ Searching LinkedIn...' : '🔍 Search Candidates'}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {results && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                Found {results.total_found} Candidates
              </h3>
              {results.xray_query && (
                <div className="text-xs text-gray-400 bg-gray-50 px-3 py-2 rounded-lg max-w-md truncate">
                  Query: {results.xray_query}
                </div>
              )}
            </div>

            {results.error && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
                ⚠️ {results.error}
              </div>
            )}

            <div className="space-y-4">
              {results.profiles.map((p, i) => (
                <div key={i}
                  className="border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-900">
                        {p.name?.charAt(0) || '?'}
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
                      className="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-800 transition-all">
                      View Profile →
                    </a>
                  </div>
                  {p.snippet && (
                    <p className="text-sm text-gray-500 mt-3 leading-relaxed">
                      {p.snippet}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {results.profiles.length === 0 && !results.error && (
              <div className="text-center py-8 text-gray-500">
                <p className="text-4xl mb-3">🔍</p>
                <p>No profiles found. Try different keywords.</p>
                <button
                  onClick={getXrayQuery}
                  className="mt-4 text-blue-600 hover:underline text-sm">
                  Search manually on Google →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}}