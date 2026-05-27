import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadJD, uploadResumes } from '../services/api';
import AutoLogout from '../components/AutoLogout';

export default function NewScreening() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [step, setStep] = useState(1);
  const [screeningId, setScreeningId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [files, setFiles] = useState([]);
  const [jdForm, setJdForm] = useState({
    job_title: '', location: '', jd_text: ''
  });

  const handleJDSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('token', token);
      fd.append('job_title', jdForm.job_title);
      fd.append('location', jdForm.location);
      fd.append('jd_text', jdForm.jd_text);
      const res = await uploadJD(fd);
      setScreeningId(res.data.screening_id);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload JD');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeSubmit = async () => {
    if (!token) { setError('Please login first'); return; }
    if (!screeningId) { setError('Please upload JD first'); return; }

    const fileList = files;
    if (fileList.length === 0) { setError('Please select resume files'); return; }

    setLoading(true);
    setError('');

    try {
      const fd = new FormData();
      fd.append('token', token);
      fileList.forEach(f => fd.append('resumes', f));

      await uploadResumes(screeningId, fd);
      
      // Redirect immediately to polling results screen dashboard
      navigate(`/results/${screeningId}`);

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process resumes');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AutoLogout />   {/* ← CORRECT POSITION */}
      <nav className="bg-blue-900 text-white px-6 py-4 flex items-center gap-4 shadow-lg">
        <button onClick={() => navigate('/dashboard')} className="hover:text-blue-200">← Back</button>
        <h1 className="text-xl font-bold">⚡ New Screening</h1>
      </nav>

      <div className="max-w-2xl mx-auto p-6">
        {/* Progress Grid Row */}
        <div className="flex items-center mb-8">
          {['Job Description', 'Upload Resumes', 'AI Screening'].map((s, i) => (
            <div key={i} className="flex items-center flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step > i + 1 ? 'bg-green-500 text-white' :
                step === i + 1 ? 'bg-blue-900 text-white' :
                'bg-gray-200 text-gray-500'}`}>
                {step > i + 1 ? '✓' : i + 1}
              </div>
              <span className={`ml-2 text-sm font-medium ${step === i + 1 ? 'text-blue-900' : 'text-gray-400'}`}>
                {s}
              </span>
              {i < 2 && <div className={`flex-1 h-1 mx-3 rounded ${step > i + 1 ? 'bg-green-500' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        {/* Step 1 - JD Workspace */}
        {step === 1 && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📋 Job Description</h2>
            <form onSubmit={handleJDSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Job Title *</label>
                <input value={jdForm.job_title}
                  onChange={e => setJdForm({...jdForm, job_title: e.target.value})}
                  placeholder="e.g. Python Backend Developer"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Location</label>
                <input value={jdForm.location}
                  onChange={e => setJdForm({...jdForm, location: e.target.value})}
                  placeholder="e.g. Noida, India / Remote"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Job Description *</label>
                <textarea value={jdForm.jd_text}
                  onChange={e => setJdForm({...jdForm, jd_text: e.target.value})}
                  placeholder="Paste your job description here..."
                  required rows={8}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">❌ {error}</div>}

              <button type="submit" disabled={loading}
                className="w-full py-3 bg-blue-900 text-white rounded-lg font-bold text-lg hover:bg-blue-800 disabled:opacity-50 transition-all">
                {loading ? '⏳ Saving...' : 'Next — Upload Resumes →'}
              </button>
            </form>
          </div>
        )}

        {/* Step 2 - Resumes Workspace */}
        {step === 2 && (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">📄 Upload Resumes</h2>
            <p className="text-gray-500 mb-6">Select up to 20 resumes — PDF, Word, or TXT format</p>

            <div
              className="border-2 border-dashed border-blue-300 rounded-xl p-10 text-center cursor-pointer hover:bg-blue-50 transition-all"
              onClick={() => document.getElementById('resumeInput').click()}>
              <p className="text-4xl mb-3">📁</p>
              <p className="text-gray-600 font-semibold">Click to select files</p>
              <p className="text-gray-400 text-sm mt-1">Hold Ctrl to select multiple files</p>
              <input id="resumeInput" type="file" multiple accept=".pdf,.docx,.doc,.txt"
                className="hidden"
                onChange={e => setFiles(Array.from(e.target.files))} />
            </div>

            {files.length > 0 && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-green-700 font-semibold mb-2">✅ {files.length} file(s) selected:</p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {files.map((f, i) => (
                    <p key={i} className="text-sm text-gray-600">📄 {f.name}</p>
                  ))}
                </div>
              </div>
            )}

            {error && <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">❌ {error}</div>}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(1)} className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-bold hover:bg-gray-100 transition-all">
                ← Back
              </button>
              
              <button onClick={handleResumeSubmit}
                disabled={loading || files.length === 0}
                className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 disabled:opacity-50 transition-all">
                {loading ? (
                  <div className="flex flex-col items-center">
                    <div className="flex items-center gap-2 mb-1">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      <span>AI Analyzing {files.length} resume(s)...</span>
                    </div>
                  </div>
                ) : `🤖 Screen ${files.length} Resume(s) with AI`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
