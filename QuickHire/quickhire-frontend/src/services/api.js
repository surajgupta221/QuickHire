import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const loginUser = (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email); // FastAPI OAuth2 expects 'username'
  formData.append('password', password);

  return API.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
};

export const registerUser = (data) =>
  API.post('/auth/register', data);

export const uploadJD = (formData) =>
  API.post('/screening/upload-jd', formData);

export const uploadResumes = (screeningId, formData) =>
  API.post(`/screening/upload-resumes/${screeningId}`, formData);

export const getResults = (screeningId, token) =>
  API.get(`/screening/results/${screeningId}`, { params: { token } });

export const getHistory = (token) =>
  API.get('/screening/history', { params: { token } });

export const exportExcel = (screeningId, token) =>
  API.get(`/screening/export/${screeningId}`, {
    params: { token },
    responseType: 'blob'
  });