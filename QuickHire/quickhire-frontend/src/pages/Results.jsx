import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getResults, exportExcel } from '../services/api';

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    getResults(id, token)
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
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

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    if (score >= 40) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getRecommendationColor = (rec) => {
    if (rec?.includes('Highly')) return 'bg-green-100 text-green-700';
    if (rec?.includes('Recommended')) return 'bg-blue-100 text-blue-700';
    if (rec?.includes('Maybe')) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-4xl mb-4">🤖</p>
        <p className="text-xl text-gray-600">Loading results...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="hover:text-blue-200">← Dashboard</button>
          <h1 className="text-xl font-bold">📊 Screening Results</h1>
        </div>
        <button onClick={handleExport}
          className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-lg text-sm font-bold transition-all">
          📥 Export Excel
        </button>
      </nav>

      <div className="max-w-6xl mx-auto p-6">
        {data && (
          <>
            <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
              <h2 className="text-2xl font-bold text-gray-800">{data.job_title}</h2>
              <div className="flex gap-4 mt-2 text-sm text-gray-500">
                <span>📍 {data.location || 'Not specified'}</span>
                <span>👥 {data.total_candidates} candidates</span>
                <span className={`px-2 py-0.5 rounded-full font-semibold ${
                  data.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {data.status?.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Candidates List */}
              <div className="space-y-4">
                <h3 className="font-bold text-gray-700 text-lg">Ranked Candidates</h3>
                {(data.results || []).map((r) => (
                  <div key={r.rank}
                    onClick={() => setSelected(selected?.rank === r.rank ? null : r)}
                    className={`bg-white rounded-xl p-5 shadow-sm cursor-pointer transition-all border-2 ${
                      selected?.rank === r.rank ? 'border-blue-500' : 'border-transparent hover:border-blue-200'}`}>
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-900 text-white rounded-full flex items-center justify-center font-bold">
                          #{r.rank}
                        </div>
                        <div>
                          <p className="font-bold text-gray-800">{r.candidate_name}</p>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${getRecommendationColor(r.recommendation)}`}>
                            {r.recommendation}
                          </span>
                        </div>
                      </div>
                      <div className={`text-2xl font-bold px-3 py-1 rounded-lg border ${getScoreColor(r.overall_score)}`}>
                        {r.overall_score}
                      </div>
                    </div>

                    <div className="mt-3 flex gap-2 flex-wrap">
                      {(r.skills_matched || []).slice(0, 4).map((s, i) => (
                        <span key={i} className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">✓ {s}</span>
                      ))}
                      {(r.skills_missing || []).slice(0, 2).map((s, i) => (
                        <span key={i} className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">✗ {s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Detail Panel */}
              <div>
                {selected ? (
                  <div className="bg-white rounded-xl p-6 shadow-sm sticky top-6">
                    <h3 className="font-bold text-xl text-gray-800 mb-4">{selected.candidate_name}</h3>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <div className="bg-gray-50 p-3 rounded-lg text-center">
                        <p className="text-2xl font-bold text-blue-900">{selected.overall_score}/100</p>
                        <p className="text-xs text-gray-500">Overall Score</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg text-center">
                        <p className="text-2xl font-bold text-blue-900">{selected.match_percentage}%</p>
                        <p className="text-xs text-gray-500">Match Rate</p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700 mb-2">📝 Summary</p>
                      <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{selected.summary}</p>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700 mb-2">✅ Skills Matched</p>
                      <div className="flex flex-wrap gap-2">
                        {(selected.skills_matched || []).map((s, i) => (
                          <span key={i} className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">{s}</span>
                        ))}
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700 mb-2">❌ Skills Missing</p>
                      <div className="flex flex-wrap gap-2">
                        {(selected.skills_missing || []).map((s, i) => (
                          <span key={i} className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">{s}</span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-2">🎤 Interview Questions</p>
                      <div className="space-y-2">
                        {(selected.interview_questions || []).map((q, i) => (
                          <div key={i} className="bg-blue-50 p-3 rounded-lg">
                            <p className="text-sm text-blue-800"><strong>Q{i+1}:</strong> {q}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl p-12 shadow-sm text-center text-gray-400">
                    <p className="text-4xl mb-3">👆</p>
                    <p>Click a candidate to see detailed analysis</p>
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