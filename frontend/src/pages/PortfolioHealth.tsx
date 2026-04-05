import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './PortfolioHealth.css';

interface HealthScore {
  score: number;
  diversification_score: number;
  risk_score: number;
  performance_score: number;
  trend_score: number;
  calculated_at: string;
}

interface HealthHistory {
  date: string;
  score: number;
  diversification_score: number;
  risk_score: number;
  performance_score: number;
  trend_score: number;
}

interface HealthAlert {
  id: string;
  threshold: number;
  is_active: boolean;
  created_at: string;
}

const PortfolioHealth: React.FC = () => {
  const { t } = useTranslation();
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);
  const [history, setHistory] = useState<HealthHistory[]>([]);
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [alertThreshold, setAlertThreshold] = useState<string>('50');

  useEffect(() => {
    fetchHealthScore();
    fetchHistory();
    fetchAlerts();
  }, []);

  const fetchHealthScore = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/v1/portfolio/health/score', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHealthScore(response.data);
    } catch (err) {
      console.error('Failed to fetch health score:', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/v1/portfolio/health/history?days=30', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data.history);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/v1/portfolio/health/alerts', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  };

  const createAlert = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/v1/portfolio/health/alerts',
        { threshold: parseFloat(alertThreshold) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAlertThreshold('50');
      fetchAlerts();
    } catch (err) {
      console.error('Failed to create alert:', err);
    }
  };

  const deleteAlert = async (alertId: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/v1/portfolio/health/alerts/${alertId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to delete alert:', err);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#84cc16';
    if (score >= 40) return '#eab308';
    if (score >= 20) return '#f97316';
    return '#ef4444';
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return t('health.excellent');
    if (score >= 60) return t('health.good');
    if (score >= 40) return t('health.fair');
    if (score >= 20) return t('health.poor');
    return t('health.critical');
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };

  if (loading) {
    return <div className="portfolio-health loading">{t('common.loading')}</div>;
  }

  return (
    <div className="portfolio-health">
      <h1>{t('health.title')}</h1>

      {healthScore && (
        <>
          <div className="health-score-card">
            <div className="score-gauge">
              <div
                className="score-circle"
                style={{
                  background: `conic-gradient(${getScoreColor(healthScore.score)} ${healthScore.score * 3.6}deg, #e5e7eb 0deg)`
                }}
              >
                <div className="score-inner">
                  <span className="score-value">{healthScore.score}</span>
                  <span className="score-label">{getScoreLabel(healthScore.score)}</span>
                </div>
              </div>
            </div>

            <div className="score-breakdown">
              <h3>{t('health.scoreBreakdown')}</h3>
              <div className="breakdown-item">
                <span className="breakdown-label">{t('health.diversification')}</span>
                <div className="breakdown-bar">
                  <div
                    className="breakdown-fill"
                    style={{ width: `${healthScore.diversification_score}%`, backgroundColor: '#3b82f6' }}
                  />
                </div>
                <span className="breakdown-value">{healthScore.diversification_score}</span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">{t('health.risk')}</span>
                <div className="breakdown-bar">
                  <div
                    className="breakdown-fill"
                    style={{ width: `${healthScore.risk_score}%`, backgroundColor: '#8b5cf6' }}
                  />
                </div>
                <span className="breakdown-value">{healthScore.risk_score}</span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">{t('health.performance')}</span>
                <div className="breakdown-bar">
                  <div
                    className="breakdown-fill"
                    style={{ width: `${healthScore.performance_score}%`, backgroundColor: '#10b981' }}
                  />
                </div>
                <span className="breakdown-value">{healthScore.performance_score}</span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">{t('health.trend')}</span>
                <div className="breakdown-bar">
                  <div
                    className="breakdown-fill"
                    style={{ width: `${healthScore.trend_score}%`, backgroundColor: '#f59e0b' }}
                  />
                </div>
                <span className="breakdown-value">{healthScore.trend_score}</span>
              </div>
            </div>
          </div>

          {history.length > 0 && (
            <div className="history-chart">
              <h3>{t('health.history')}</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <Tooltip
                    labelFormatter={(label) => formatDate(String(label))}
                    formatter={(value) => {
                      const num = typeof value === 'number' ? value : 0;
                      return [`${num.toFixed(1)}`, t('health.score')];
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}

      <div className="health-alerts">
        <h3>{t('health.alerts')}</h3>
        <div className="create-alert">
          <input
            type="number"
            min="0"
            max="100"
            value={alertThreshold}
            onChange={(e) => setAlertThreshold(e.target.value)}
            placeholder={t('health.threshold')}
          />
          <button onClick={createAlert}>{t('health.createAlert')}</button>
        </div>

        {alerts.length === 0 ? (
          <p className="no-alerts">{t('health.noAlerts')}</p>
        ) : (
          <ul className="alerts-list">
            {alerts.map((alert) => (
              <li key={alert.id} className="alert-item">
                <span>{t('health.alertThreshold')}: {alert.threshold}</span>
                <button
                  className="delete-btn"
                  onClick={() => deleteAlert(alert.id)}
                >
                  {t('common.delete')}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default PortfolioHealth;
