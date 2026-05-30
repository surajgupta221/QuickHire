import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AutoLogout from '../components/AutoLogout';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const COUNTRIES = [
  { code: 'IN', name: 'India' },
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'SG', name: 'Singapore' },
  { code: 'AE', name: 'UAE' },
  { code: 'AU', name: 'Australia' },
  { code: 'CA', name: 'Canada' },
  { code: 'DE', name: 'Germany' },
];

const INDIA_CITIES = [
  'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai',
  'Pune', 'Kolkata', 'Noida', 'Gurgaon', 'Ahmedabad',
  'Remote', 'Pan India'
];

export default function LinkedInSearch() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('search');
  const [form, setForm] = useState({
    job_title: '',
    country: 'IN',
    city: '',
    must_have_skills: '',
    good_to_have_skills: '',
    jd_text: '',
    num_results: 10,
    source: 'linkedin'
  });

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!form.job_title) { setError('Job title is required'); return; }
    setLoading(true); setError(''); setResults(null);

    try {
      const location = form.city
        ? `${form.city}, ${COUNTRIES.find(c => c.code === form.country)?.name}`
        : COUNTRIES.find(c => c.code === form.country)?.name;

      const res = await axios.get(`${API_URL}/linkedin/search`, {
        params: {
          job_title: form.job_title,
          location,
          must_have_skills: form.must_have_skills,
          good_to_have_skills: form.good_to_have_skills,
          num_results: form.num_results,
          source: form.source,
          token
        }
      });
      setResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally { setLoading(false); }
  };

  const openGoogleSearch = () => {
    const location = form.city || COUNTRIES.find(c => c.code === form.country)?.name || '';
    let query = `site:linkedin.com/in "${form.job_title}"`;
    if (location) query += ` "${location}"`;
    if (form.must_have_skills) {
      const skills = form.must_have_skills.split(',').slice(0, 2);
      skills.forEach(s => { if (s.trim()) query += ` "${s.trim()}"`; });
    }
    window.open(`https://www.google.com/search?q=${encodeURIComponent(query)}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AutoLogout />

      <nav className="bg-blue-900 text-white px-6 py-4 flex items-center gap-4 shadow-lg">
        <button onClick={() => navigate('/dashboard')} className="hover:text-blue-200">
          ← Dashboard
        </button>
        <span className="text-blue-300">|</span>
        <h1 className="text-xl font-bold">🔍 Smart Candidate Search</h1>
      </nav>

      <div className="max-w-5xl mx-auto p-6">
        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm text-blue-800">
          <strong>🔍 How it works:</strong> Fill job details → AI generates Google X-Ray query →
          finds LinkedIn profiles matching your exact requirements →
          Click profiles to view and screen candidates.
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-2xl p-8 shadow-sm mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Find Matching Candidates
          </h2>
          <p className="text-gray-500 text-sm mb-6">
            Search across LinkedIn using AI-powered X-Ray queries
          </p>

          <form onSubmit={handleSearch}>
            {/* Job Title */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Title *
              </label>
              <input
                value={form.job_title}
                onChange={e => setForm({...form, job_title: e.target.value})}
                placeholder="e.g. Java Developer with Angular"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Country + City */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  🌍 Country *
                </label>
                <select
                  value={form.country}
                  onChange={e => setForm({...form, country: e.target.value, city: ''})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                  {COUNTRIES.map(c => (
                    <option key={c.code} value={c.code}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📍 City / Location
                </label>
                {form.country === 'IN' ? (
                  <select
                    value={form.city}
                    onChange={e => setForm({...form, city: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">All India</option>
                    {INDIA_CITIES.map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={form.city}
                    onChange={e => setForm({...form, city: e.target.value})}
                    placeholder="e.g. London, New York"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>
            </div>

            {/* Must Have + Good to Have */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold mb-2"
                  style={{color: '#DC2626'}}>
                  🔴 Must Have Skills
                  <span className="text-gray-400 font-normal text-xs ml-1">
                    (comma separated)
                  </span>
                </label>
                <input
                  value={form.must_have_skills}
                  onChange={e => setForm({...form, must_have_skills: e.target.value})}
                  placeholder="Java, Spring Boot, Angular"
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
                  placeholder="Docker, Microservices, AWS"
                  className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-300 bg-green-50"
                />
              </div>
            </div>

            {/* JD Text */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Description
                <span className="text-gray-400 font-normal text-xs ml-1">
                  (helps AI find better matches)
                </span>
              </label>
              <textarea
                value={form.jd_text}
                onChange={e => setForm({...form, jd_text: e.target.value})}
                placeholder="Paste job description here for better candidate matching..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {/* Results Count */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Candidates to Find
              </label>
              <div className="flex gap-3">
                {[5, 10, 20].map(n => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setForm({...form, num_results: n})}
                    className={`px-6 py-2 rounded-lg font-semibold text-sm transition-all ${
                      form.num_results === n
                        ? 'bg-blue-900 text-white'
                        : 'border border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}>
                    {n} profiles
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                ❌ {error}
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={openGoogleSearch}
                disabled={!form.job_title}
                className="px-6 py-3 border-2 border-blue-900 text-blue-900 rounded-lg font-semibold hover:bg-blue-50 transition-all disabled:opacity-50">
                🔗 X-Ray Search
              </button>
              <button
                type="submit"
                disabled={loading || !form.job_title}
                className="flex-1 py-3 bg-blue-900 text-white rounded-lg font-bold hover:bg-blue-800 disabled:opacity-50 transition-all">
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10"
                        stroke="currentColor" strokeWidth="4" fill="none"/>
                      <path className="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Searching Candidates...
                  </span>
                ) : '🔍 Find Matching Candidates'}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {results && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-xl font-bold text-gray-800">
                  {results.total_found > 0
                    ? `Found ${results.total_found} Matching Profiles`
                    : 'No Profiles Found'}
                </h3>
                {results.xray_query && (
                  <p className="text-xs text-gray-400 mt-1 font-mono bg-gray-50 px-2 py-1 rounded">
                    {results.xray_query}
                  </p>
                )}
              </div>
            </div>

            {results.error && (
              <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-800 text-sm">
                <p className="font-semibold mb-1">⚠️ Search Note</p>
                <p>{results.error}</p>
                <button onClick={openGoogleSearch}
                  className="mt-2 text-blue-600 hover:underline text-xs font-semibold">
                  → Try manual Google X-Ray search
                </button>
              </div>
            )}

            <div className="space-y-4">
              {(results.profiles || []).map((p, i) => (
                <div key={i}
                  className="border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-900 rounded-full flex items-center justify-center font-bold text-white text-xl flex-shrink-0">
                        {p.name?.charAt(0)?.toUpperCase() || '#'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-gray-800 text-lg">{p.name}</h4>
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                            #{i + 1}
                          </span>
                        </div>
                        {p.current_role && (
                          <p className="text-sm text-gray-600 mt-0.5">{p.current_role}</p>
                        )}
                        {p.snippet && (
                          <p className="text-xs text-gray-400 mt-1 max-w-lg line-clamp-2">
                            {p.snippet}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <a
                        href={p.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-800 transition-all text-center">
                        View LinkedIn →
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {results.profiles?.length === 0 && !results.error && (
              <div className="text-center py-12">
                <p className="text-5xl mb-4">🔍</p>
                <p className="text-lg font-bold text-gray-700 mb-2">No profiles found</p>
                <p className="text-gray-400 text-sm mb-6">
                  Try: broader location, fewer skills, or different job title
                </p>
                <button onClick={openGoogleSearch}
                  className="bg-blue-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-800">
                  Search manually on Google →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Honest Capability Note */}
        <div className="mt-6 p-4 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-500">
          <p className="font-semibold text-gray-700 mb-2">📋 About Candidate Contact Details</p>
          <p>LinkedIn and job portals don't allow automated extraction of email/phone numbers.
          To get contact details, use these legal methods:</p>
          <ul className="mt-2 space-y-1 list-disc list-inside">
            <li>Connect with candidates on LinkedIn directly</li>
            <li><strong>Hunter.io</strong> — find professional emails by name + company</li>
            <li><strong>Apollo.io</strong> — B2B contact database</li>
            <li>Post jobs on <strong>Naukri/LinkedIn</strong> and get applications</li>
          </ul>
        </div>
      </div>
    </div>
  );
}