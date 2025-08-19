import { useState } from "react";
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Alert, CircularProgress } from "@mui/material";
import { useAuth } from "../contexts/AuthContext";

const LoginPage = () => {
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  
  const from = location.state?.from?.pathname || '/dashboard';

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    
    if (!formData.id || !formData.password) {
      setError('Enter ID and password.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      
      const result = await login(formData.id, formData.password);
      
      if (result.success) {
        
        navigate(from, { replace: true });
      } else {
        setError(result.error || 'Invalid data for sign up.');
      }
    } catch (err) {
      setError('Error. Try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-blue-700">
      <div className="bg-white shadow-xl p-8 w-130 rounded-lg">
        <h1 className="text-3xl text-center text-blue-700 font-medium mb-8">
          Sign In
        </h1>

        
        {error && (
          <Alert 
            severity="error" 
            className="mb-4"
            onClose={() => setError('')}
          >
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <div className="pb-6">
            <div className="pb-4">
              <input
                type="text"
                name="id"
                placeholder="ID"
                value={formData.id}
                onChange={handleInputChange}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                required
              />
            </div>
            <div className="relative">
              <input
                type={passwordVisible ? "text" : "password"}
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                required
              />
              <button
                type="button"
                onClick={() => setPasswordVisible(!passwordVisible)}
                disabled={loading}
                className="absolute right-3 top-2/4 -translate-y-2/4 text-gray-500 hover:text-blue-700 disabled:cursor-not-allowed"
              >
                {passwordVisible ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div className="mb-4">
            <Button 
              type="submit"
              variant="contained" 
              size="large" 
              className="w-full"
              disabled={loading || !formData.id || !formData.password}
              startIcon={loading && <CircularProgress size={20} color="inherit" />}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </Button>
          </div>

         
        </form>
      </div>
    </div>
  );
};

export default LoginPage;