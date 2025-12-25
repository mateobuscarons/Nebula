import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getAdminStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load admin stats:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading admin stats...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">
          {error.includes('403') || error.includes('Admin') ?
            'Access denied. Admin privileges required.' :
            `Error: ${error}`
          }
        </div>
        <button onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
        <button onClick={() => navigate('/dashboard')}>← Dashboard</button>
      </header>

      <div className="admin-content">
        {/* Summary Cards */}
        <div className="summary-cards">
          <div className="summary-card">
            <h3>Total Tokens Used</h3>
            <p className="big-number">{stats?.total_tokens?.toLocaleString() || 0}</p>
            <p className="sub-text">
              In: {stats?.total_input_tokens?.toLocaleString() || 0} | Out: {stats?.total_output_tokens?.toLocaleString() || 0}
            </p>
          </div>

          <div className="summary-card">
            <h3>Estimated Cost</h3>
            <p className="big-number">${(stats?.estimated_cost || 0).toFixed(4)}</p>
            <p className="sub-text">
              In: ${(stats?.input_cost || 0).toFixed(4)} | Out: ${(stats?.output_cost || 0).toFixed(4)}
            </p>
          </div>

          <div className="summary-card">
            <h3>Total Users</h3>
            <p className="big-number">{stats?.users?.length || 0}</p>
          </div>
        </div>

        {/* Users Table */}
        <div className="users-section">
          <h2>User Activity</h2>
          <div className="table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Tokens (In/Out)</th>
                  <th>Est. Cost</th>
                  <th>Paths</th>
                  <th>Lessons</th>
                  <th>Last Active</th>
                </tr>
              </thead>
              <tbody>
                {stats?.users?.map(user => {
                  const inputCost = ((user.input_tokens || 0) / 1_000_000) * 0.50;
                  const outputCost = ((user.output_tokens || 0) / 1_000_000) * 3.00;
                  const totalCost = inputCost + outputCost;
                  return (
                    <tr key={user.user_id}>
                      <td>{user.email || 'Unknown'}</td>
                      <td>
                        {(user.total_tokens || 0).toLocaleString()}
                        <span className="token-breakdown">
                          {(user.input_tokens || 0).toLocaleString()} / {(user.output_tokens || 0).toLocaleString()}
                        </span>
                      </td>
                      <td>${totalCost.toFixed(4)}</td>
                      <td>{user.paths_created || 0}</td>
                      <td>{user.lessons_completed || 0}</td>
                      <td>
                        {user.last_active ?
                          new Date(user.last_active).toLocaleDateString() :
                          'Never'
                        }
                      </td>
                    </tr>
                  );
                })}
                {(!stats?.users || stats.users.length === 0) && (
                  <tr>
                    <td colSpan="6" style={{textAlign: 'center', padding: '40px', color: '#999'}}>
                      No user activity yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Daily Usage Table */}
        <div className="daily-usage-section">
          <h2>Token Usage (Last 30 Days)</h2>
          <div className="table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Tokens</th>
                </tr>
              </thead>
              <tbody>
                {stats?.daily_usage?.map(day => (
                  <tr key={day.date}>
                    <td>{day.date}</td>
                    <td>{day.tokens.toLocaleString()}</td>
                  </tr>
                ))}
                {(!stats?.daily_usage || stats.daily_usage.length === 0) && (
                  <tr>
                    <td colSpan="2" style={{textAlign: 'center', padding: '40px', color: '#999'}}>
                      No usage data yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
