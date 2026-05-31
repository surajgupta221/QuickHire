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

const US_CITIES = [
  'New York', 'San Francisco', 'Seattle', 'Austin', 'Chicago',
  'Los Angeles', 'Boston', 'Dallas', 'Atlanta', 'Washington DC',
  'Remote', 'United States'
];

const CANADA_CITIES = [
  'Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa',
  'Edmonton', 'Winnipeg', 'Quebec City', 'Mississauga',
  'Halifax', 'Remote', 'Canada'
];

const CITY_OPTIONS = {
  IN: INDIA_CITIES,
  US: US_CITIES,
  CA: CANADA_CITIES,
};

const SOURCES = [
  { id: 'linkedin', label: 'LinkedIn', icon: '💼' },
  { id: 'github', label: 'GitHub', icon: '🐙' },
  { id: 'web', label: 'Open Web', icon: '🌐' },
];

export default function LinkedInSearch() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [findingEmail, setFindingEmail] = useState({});
  const [selectedSources, setSelectedSources] = useState(['linkedin', 'github']);

  const [form, setForm] = useState({
    job_title: '',
    country: 'IN',
    city: '',
    must_have_skills: '',
    good_to_have_skills: '',
    jd_text: '',
    num_results: 10,
  });

  const toggleSource = (id) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const getLocation = () => {
    const country = COUNTRIES.find((c) => c.code === form.country)?.name || '';
    return form.city ? `${form.city}, ${country}` : country;
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!form.job_title.trim()) {
      setError('Job title is required');
      return;
    }

    if (selectedSources.length === 0) {
      setError('Please select at least one source');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const res = await axios.get(`${API_URL}/linkedin/search`, {
        params: {
          job_title: form.job_title,
          location: getLocation(),
          must_have_skills: form.must_have_skills,
          good_to_have_skills: form.good_to_have_skills,
          jd_text: form.jd_text,
          num_results: form.num_results,
          sources: selectedSources.join(','),
          token,
        },
      });

      setResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Check API configuration.');
    } finally {
      setLoading(false);
    }
  };

  const findEmail = async (candidate, index) => {
    setFindingEmail((prev) => ({ ...prev, [index]: true }));

    try {
      const res = await axios.get(`${API_URL}/linkedin/find-email`, {
        params: {
          name: candidate.name,
          company_domain: '',
          token,
        },
      });

      if (res.data.email) {
        setResults((prev) => {
          const updated = { ...prev };
          updated.profiles = [...(updated.profiles || [])];
          updated.profiles[index] = {
            ...updated.profiles[index],
            email: res.data.email,
          };
          return updated;
        });
      } else {
        alert(`No email found for ${candidate.name}. Try with company domain.`);
      }
    } catch (err) {
      alert('Email search failed');
    } finally {
      setFindingEmail((prev) => ({ ...prev, [index]: false }));
    }
  };

  const openGoogleSearch = () => {
    let query = `site:linkedin.com/in "${form.job_title}"`;

    const location = getLocation();
    if (location) query += ` "${location}"`;

    if (form.must_have_skills) {
      const skills = form.must_have_skills.split(',').slice(0, 2);
      skills.forEach((s) => {
        if (s.trim()) query += ` "${s.trim()}"`;
      });
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
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm text-blue-800">
          <strong>🔍 How it works:</strong> Fill job details → AI generates Google X-Ray query →
          finds LinkedIn, GitHub, and open web profiles matching your requirements.
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-sm mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-1">
            Find Candidates Across Multiple Sources
          </h2>

          <p className="text-gray-500 text-sm mb-6">
            LinkedIn • GitHub • Open Web • Public Portfolios
          </p>

          <form onSubmit={handleSearch}>
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Search Sources
              </label>

              <div className="flex gap-3 flex-wrap">
                {SOURCES.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => toggleSource(s.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 font-semibold text-sm transition-all ${
                      selectedSources.includes(s.id)
                        ? 'bg-blue-900 text-white border-blue-900'
                        : 'border-gray-200 text-gray-600 hover:border-blue-300'
                    }`}
                  >
                    {s.icon} {s.label}
                    {selectedSources.includes(s.id) && <span>✓</span>}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Title *
              </label>
              <input
                value={form.job_title}
                onChange={(e) => setForm({ ...form, job_title: e.target.value })}
                placeholder="e.g. Java Developer with Angular"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  🌍 Country *
                </label>
                <select
                  value={form.country}
                  onChange={(e) =>
                    setForm({ ...form, country: e.target.value, city: '' })
                  }
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📍 City / Location
                </label>

                {CITY_OPTIONS[form.country] ? (
                  <select
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Locations</option>
                    {CITY_OPTIONS[form.country].map((city) => (
                      <option key={city} value={city}>
                        {city}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    placeholder="e.g. London, Dubai, Singapore"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label
                  className="block text-sm font-semibold mb-2"
                  style={{ color: '#DC2626' }}
                >
                  🔴 Must Have Skills
                  <span className="text-gray-400 font-normal text-xs ml-1">
                    (comma separated)
                  </span>
                </label>
                <input
                  value={form.must_have_skills}
                  onChange={(e) =>
                    setForm({ ...form, must_have_skills: e.target.value })
                  }
                  placeholder="Java, Spring Boot, Angular"
                  className="w-full px-4 py-3 border-2 border-red-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-300 bg-red-50"
                />
              </div>

              <div>
                <label
                  className="block text-sm font-semibold mb-2"
                  style={{ color: '#16A34A' }}
                >
                  🟢 Good to Have Skills
                </label>
                <input
                  value={form.good_to_have_skills}
                  onChange={(e) =>
                    setForm({ ...form, good_to_have_skills: e.target.value })
                  }
                  placeholder="Docker, Microservices, AWS"
                  className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-300 bg-green-50"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Description
                <span className="text-gray-400 font-normal text-xs ml-1">
                  (helps AI find better matches and improve search accuracy)
                </span>
              </label>
              <textarea
                value={form.jd_text}
                onChange={(e) => setForm({ ...form, jd_text: e.target.value })}
                placeholder="Paste job description here for better candidate matching..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Candidates to Find
              </label>

              <div className="flex gap-3">
                {[5, 10, 20].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setForm({ ...form, num_results: n })}
                    className={`px-6 py-2 rounded-lg font-semibold text-sm transition-all ${
                      form.num_results === n
                        ? 'bg-blue-900 text-white'
                        : 'border border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
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

            <div className="flex gap-3">
              <button
                type="button"
                onClick={openGoogleSearch}
                disabled={!form.job_title}
                className="px-6 py-3 border-2 border-blue-900 text-blue-900 rounded-lg font-semibold hover:bg-blue-50 transition-all disabled:opacity-50"
              >
                🔗 X-Ray Search
              </button>

              <button
                type="submit"
                disabled={loading || !form.job_title || selectedSources.length === 0}
                className="flex-1 py-3 bg-blue-900 text-white rounded-lg font-bold hover:bg-blue-800 disabled:opacity-50 transition-all"
              >
                {loading ? '⏳ Searching Candidates...' : '🔍 Find Matching Candidates'}
              </button>
            </div>
          </form>
        </div>

        {results && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="bg-blue-50 rounded-xl px-4 py-3 text-center">
                <p className="text-2xl font-bold text-blue-900">
                  {results.total_found || 0}
                </p>
                <p className="text-xs text-gray-500">Total Found</p>
              </div>

              {results.stats && (
                <>
                  <div className="bg-blue-50 rounded-xl px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-blue-700">
                      {results.stats.linkedin || 0}
                    </p>
                    <p className="text-xs text-gray-500">💼 LinkedIn</p>
                  </div>

                  <div className="bg-gray-50 rounded-xl px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-gray-700">
                      {results.stats.github || 0}
                    </p>
                    <p className="text-xs text-gray-500">🐙 GitHub</p>
                  </div>

                  <div className="bg-green-50 rounded-xl px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-green-700">
                      {results.stats.emails_found || 0}
                    </p>
                    <p className="text-xs text-gray-500">📧 Emails Found</p>
                  </div>
                </>
              )}
            </div>

            {results.error && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
                ⚠️ {results.error}
              </div>
            )}

            <h3 className="text-xl font-bold text-gray-800 mb-4">
              Matching Candidates
            </h3>

            <div className="space-y-4">
              {(results.profiles || []).map((p, i) => (
                <div
                  key={i}
                  className="border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all"
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-900 text-xl flex-shrink-0">
                        {p.avatar ? (
                          <img
                            src={p.avatar}
                            alt={p.name || 'Candidate'}
                            className="w-12 h-12 rounded-full object-cover"
                          />
                        ) : (
                          p.name?.charAt(0)?.toUpperCase() || '?'
                        )}
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold text-gray-800 text-lg">
                            {p.name || 'Unknown Candidate'}
                          </h4>

                          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                            {p.source_icon || '🔎'} {p.source || 'Source'}
                          </span>

                          {p.email && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                              ✅ Email Found
                            </span>
                          )}
                        </div>

                        {p.current_role && (
                          <p className="text-sm text-gray-600 mt-0.5">
                            {p.current_role}
                          </p>
                        )}

                        {p.snippet && (
                          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                            {p.snippet.substring(0, 150)}...
                          </p>
                        )}

                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          {p.email && (
                            <span className="text-xs text-green-700 font-medium">
                              📧 {p.email}
                            </span>
                          )}

                          {p.company && (
                            <span className="text-xs text-gray-500">
                              🏢 {p.company}
                            </span>
                          )}

                          {p.location && (
                            <span className="text-xs text-gray-500">
                              📍 {p.location}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <a
                        href={p.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-blue-900 text-white px-3 py-2 rounded-lg text-xs font-semibold hover:bg-blue-800 transition-all text-center"
                      >
                        View Profile →
                      </a>

                      {!p.email && p.can_find_email && (
                        <button
                          onClick={() => findEmail(p, i)}
                          disabled={findingEmail[i]}
                          className="border border-green-600 text-green-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-green-50 transition-all disabled:opacity-50"
                        >
                          {findingEmail[i] ? '⏳ Finding...' : '📧 Find Email'}
                        </button>
                      )}

                      {p.email && (
                        <a
                          href={`mailto:${p.email}`}
                          className="bg-green-600 text-white px-3 py-2 rounded-lg text-xs font-semibold hover:bg-green-700 transition-all text-center"
                        >
                          📧 Send Email
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {results.profiles?.length === 0 && (
              <div className="text-center py-12">
                <p className="text-5xl mb-4">🔍</p>
                <p className="text-lg font-bold text-gray-700 mb-2">
                  No profiles found
                </p>
                <p className="text-sm text-gray-400 mb-6">
                  Try different skills, broader location, or add more sources.
                </p>
                <button
                  onClick={openGoogleSearch}
                  className="bg-blue-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-800"
                >
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