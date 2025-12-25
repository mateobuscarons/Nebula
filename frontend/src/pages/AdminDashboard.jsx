import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const { user } = useAuth();
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
        <button onClick={() => window.history.back()}>Go Back</button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
        <button onClick={() => window.history.back()}>← Back</button>
      </header>

      <div className="admin-content">
        {/* Summary Cards */}
        <div className="summary-cards">
          <div className="summary-card">
            <h3>Total Tokens Used</h3>
            <p className="big-number">{stats?.total_tokens?.toLocaleString() || 0}</p>
          </div>

          <div className="summary-card">
            <h3>Estimated Cost</h3>
            <p className="big-number">${(stats?.estimated_cost || 0).toFixed(4)}</p>
            <p className="sub-text">~$0.15 per 1M tokens</p>
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
                  <th>Total Tokens</th>
                  <th>Paths Created</th>
                  <th>Lessons Completed</th>
                  <th>Last Active</th>
                </tr>
              </thead>
              <tbody>
                {stats?.users?.map(user => (
                  <tr key={user.user_id}>
                    <td>{user.email || 'Unknown'}</td>
                    <td>{(user.total_tokens || 0).toLocaleString()}</td>
                    <td>{user.paths_created || 0}</td>
                    <td>{user.lessons_completed || 0}</td>
                    <td>
                      {user.last_active ?
                        new Date(user.last_active).toLocaleDateString() :
                        'Never'
                      }
                    </td>
                  </tr>
                ))}
                {(!stats?.users || stats.users.length === 0) && (
                  <tr>
                    <td colSpan="5" style={{textAlign: 'center', padding: '40px', color: '#999'}}>
                      No user activity yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Daily Usage Chart (Simple List) */}
        <div className="daily-usage-section">
          <h2>Token Usage (Last 30 Days)</h2>
          <div className="usage-list">
            {stats?.daily_usage?.map(day => (
              <div key={day.date} className="usage-item">
                <span className="usage-date">{day.date}</span>
                <div className="usage-bar-container">
                  <div
                    className="usage-bar"
                    style={{width: `${Math.min(day.percentage, 100)}%`}}
                  ></div>
                </div>
                <span className="usage-count">{day.tokens.toLocaleString()}</span>
              </div>
            ))}
            {(!stats?.daily_usage || stats.daily_usage.length === 0) && (
              <p style={{textAlign: 'center', color: '#999', padding: '40px'}}>
                No usage data yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
