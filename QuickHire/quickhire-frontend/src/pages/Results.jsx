import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getResults, exportExcel } from '../services/api';
import AutoLogout from '../components/AutoLogout';

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let pollInterval;

    const fetchResults = async () => {
      try {
        const res = await getResults(id, token);
        setData(res.data);

        // If still processing keep polling
        if (res.data.status === 'processing') {
          pollInterval = setTimeout(fetchResults, 5000); // Poll every 5 seconds
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };

    fetchResults();

    return () => {
      if (pollInterval) clearTimeout(pollInterval);
    };
  }, [id]);

  const handleExport = async () => {
    try {
      const res = await exportExcel(id, token);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `QuickHire_Results_${id}.xlsx`;
      a.click();
    } catch (err) {
      alert('Export failed');
    }
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Match';
    if (score >= 40) return 'Fair Match';
    return 'Poor Match';
  };

  const getRecColor = (rec) => {
    if (!rec) return 'bg-gray-100 text-gray-600';
    if (rec.includes('Highly') || rec.includes('Strongly')) return 'bg-green-100 text-green-700';
    if (rec.includes('Recommend')) return 'bg-blue-100 text-blue-700';
    if (rec.includes('Maybe')) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  if (loading || data?.status === 'processing') return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center bg-white p-12 rounded-2xl shadow-lg max-w-md">
        <div className="text-6xl mb-6 animate-bounce">🤖</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-3">
          AI is Analyzing Resumes
        </h2>
        <p className="text-gray-500 mb-6">
          Processing {data?.total_candidates || '...'} candidates.
          This takes 1-2 minutes.
        </p>
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse w-3/4"></div>
        </div>
        <p className="text-sm text-gray-400">
          Page updates automatically every 5 seconds...
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <AutoLogout />
      <nav className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 hover:text-blue-200 transition-colors">
            ← Dashboard
          </button>
          <span className="text-blue-300">|</span>
          <h1 className="text-xl font-bold">📊 Screening Results</h1>
        </div>
        <button onClick={handleExport}
          className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2">
          📥 Export Excel
        </button>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        {data && (
          <>
            {/* Job Info Card */}
            <div className="bg-white rounded-xl p-6 shadow-sm mb-6 border-l-4 border-blue-500">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">{data.job_title}</h2>
                  <div className="flex gap-4 mt-2 text-sm text-gray-500">
                    <span>📍 {data.location || 'Not specified'}</span>
                    <span>👥 {data.total_candidates} candidates screened</span>
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-semibold">
                      ✅ {data.status?.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Screening ID</p>
                  <p className="text-2xl font-bold text-blue-900">#{id}</p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-3xl font-bold text-blue-900">{data.total_candidates}</p>
                <p className="text-sm text-gray-500">Total Screened</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-3xl font-bold text-green-600">
                  {(data.results || []).filter(r => r.recommendation?.includes('Recommend') || r.recommendation?.includes('Strongly')).length}
                </p>
                <p className="text-sm text-gray-500">Recommended</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-3xl font-bold text-purple-600">
                  {Math.round((data.results || []).reduce((sum, r) => sum + (r.overall_score || 0), 0) / (data.total_candidates || 1))}
                </p>
                <p className="text-sm text-gray-500">Avg Score</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left — Ranked List */}
              <div>
                <h3 className="font-bold text-gray-700 text-lg mb-4">
                  🏆 Ranked Candidates
                  <span className="text-sm font-normal text-gray-400 ml-2">Click to see details</span>
                </h3>
                <div className="space-y-3">
                  {(data.results || []).map((r) => (
                    <div key={r.rank}
                      onClick={() => setSelected(selected?.rank === r.rank ? null : r)}
                      className={`bg-white rounded-xl p-5 shadow-sm cursor-pointer transition-all border-2 ${
                        selected?.rank === r.rank
                          ? 'border-blue-500 shadow-md'
                          : 'border-transparent hover:border-blue-200 hover:shadow-md'
                      }`}>
                      <div className="flex items-center gap-4">
                        {/* Rank Badge */}
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white text-lg flex-shrink-0 ${
                          r.rank === 1 ? 'bg-yellow-500' :
                          r.rank === 2 ? 'bg-gray-400' :
                          r.rank === 3 ? 'bg-orange-400' : 'bg-blue-900'
                        }`}>
                          {r.rank === 1 ? '🥇' : r.rank === 2 ? '🥈' : r.rank === 3 ? '🥉' : `#${r.rank}`}
                        </div>

                        {/* Info */}
                        <div>
                          <p className="font-bold text-gray-800 text-lg">{r.candidate_name}</p>
                          <div className="flex gap-2 mt-1 flex-wrap">
                            <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${getRecColor(r.recommendation)}`}>
                              {r.recommendation}
                            </span>
                            {/* 🚀 NEW TIER BADGE ADDED HERE */}
                            {r.tier_category && (
                              <span className={`text-[11px] px-2 py-0.5 rounded-full font-bold text-white ${
                                r.tier_category.includes('Top 20%') ? 'bg-amber-600' :
                                r.tier_category.includes('Mid 30%') ? 'bg-indigo-600' : 'bg-gray-500'
                              }`}>
                                {r.tier_category}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Score Circle */}
                        <div className="flex-shrink-0 text-center">
                          <div className={`w-14 h-14 rounded-full ${getScoreBg(r.overall_score)} flex items-center justify-center`}>
                            <span className="text-white font-bold text-lg">{r.overall_score}</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">out of 100</p>
                        </div>
                      </div>

                      {/* Skills Preview */}
                      <div className="mt-3 flex gap-2 flex-wrap">
                        {(r.skills_matched || []).slice(0, 3).map((s, i) => (
                          <span key={i} className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium">
                            ✓ {s.length > 20 ? s.substring(0, 20) + '...' : s}
                          </span>
                        ))}
                        {(r.skills_missing || []).slice(0, 2).map((s, i) => (
                          <span key={i} className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full font-medium">
                            ✗ {s.length > 20 ? s.substring(0, 20) + '...' : s}
                          </span>
                        ))}
                      </div>

                      {selected?.rank === r.rank && (
                        <p className="text-xs text-blue-500 mt-2 font-medium">← See full details on right →</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Right — Detail Panel */}
              <div className="lg:sticky lg:top-6">
                {selected ? (
                  <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                    {/* Header */}
                    <div className={`p-6 text-white ${getScoreBg(selected.overall_score)}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-bold text-2xl">{selected.candidate_name}</h3>
                          <span className="bg-white bg-opacity-20 text-white text-sm px-3 py-1 rounded-full mt-2 inline-block">
                            {selected.recommendation}
                          </span>
                        </div>
                        <div className="text-center">
                          <p className="text-5xl font-bold">{selected.overall_score}</p>
                          <p className="text-sm opacity-80">out of 100</p>
                          <p className="text-xs opacity-70">{getScoreLabel(selected.overall_score)}</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-6 space-y-5">
                      {/* Stats Row */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-gray-50 p-3 rounded-lg text-center">
                          <p className="text-xl font-bold text-blue-900">{selected.match_percentage}%</p>
                          <p className="text-xs text-gray-500">Match Rate</p>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg text-center">
                          <p className="text-sm font-bold text-gray-700">{selected.experience_match}</p>
                          <p className="text-xs text-gray-500">Experience</p>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg text-center">
                          <p className="text-sm font-bold text-gray-700">{selected.education_match}</p>
                          <p className="text-xs text-gray-500">Education</p>
                        </div>
                      </div>

                      {/* Summary */}
                      <div>
                        <p className="text-sm font-bold text-gray-700 mb-2">📝 AI Summary</p>
                        <p className="text-sm text-gray-600 bg-blue-50 p-4 rounded-lg leading-relaxed">
                          {selected.summary}
                        </p>
                      </div>

                      {/* Skills Matched */}
                      <div>
                        <p className="text-sm font-bold text-gray-700 mb-2">
                          ✅ Skills Matched ({(selected.skills_matched || selected.skills_match || selected.skills || []).length})
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {(selected.skills_matched || selected.skills_match || selected.skills || []).map((s, i) => (
                            <span key={i} className="bg-green-100 text-green-700 text-xs px-3 py-1 rounded-full font-medium">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Skills Missing */}
                      <div>
                        <p className="text-sm font-bold text-gray-700 mb-2">
                          ❌ Skills Missing ({(selected.skills_missing || selected.skills_missed || selected.missing_skills || []).length})
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {(selected.skills_missing || selected.skills_missed || selected.missing_skills || []).map((s, i) => (
                            <span key={i} className="bg-red-100 text-red-600 text-xs px-3 py-1 rounded-full font-medium">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Strengths */}
                      {(selected.strengths || []).length > 0 && (
                        <div>
                          <p className="text-sm font-bold text-gray-700 mb-2">💪 Strengths</p>
                          <ul className="space-y-1">
                            {(selected.strengths || []).map((s, i) => (
                              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                                <span className="text-green-500 mt-0.5">→</span> {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Interview Questions */}
                      <div>
                        <p className="text-sm font-bold text-gray-700 mb-2">
                          🎤 Interview Questions
                        </p>
                        <div className="space-y-2">
                          {(selected.interview_questions || []).map((q, i) => (
                            <div key={i} className="bg-blue-50 border border-blue-100 p-3 rounded-lg">
                              <p className="text-sm text-blue-800">
                                <strong>Q{i + 1}:</strong> {q}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl p-16 shadow-sm text-center">
                    <p className="text-6xl mb-4">👆</p>
                    <p className="text-gray-500 text-lg font-medium">Click any candidate</p>
                    <p className="text-gray-400 text-sm mt-1">to see detailed AI analysis</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}