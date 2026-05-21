import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewScreening from './pages/NewScreening';
import Results from './pages/Results';
import Pricing from './pages/Pricing';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  const token = localStorage.getItem('token');
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to={token ? "/dashboard" : "/login"} />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/new-screening" element={<PrivateRoute><NewScreening /></PrivateRoute>} />
        <Route path="/results/:id" element={<PrivateRoute><Results /></PrivateRoute>} />
        <Route path="/pricing" element={<PrivateRoute><Pricing /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;