import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../api/auth';
import './Auth.css';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(username, password, email);
      navigate('/dashboard');
    } catch (err) {
      console.log('Backend error response:', err);
      // Show backend error details if available
      if (err.response && err.response.data) {
        // If backend returns an object with error property
        if (typeof err.response.data === 'object' && err.response.data.error) {
          setError(err.response.data.error);
        } else {
          setError(typeof err.response.data === 'string' ? err.response.data : 'Registration failed. Try again.');
        }
      } else {
        setError('Registration failed. Try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Price Tracker</h1>
        <h2>Register</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        <p>
          Already have an account?{' '}
          <a href="/login">Login here</a>
        </p>
      </div>
    </div>
  );
}
