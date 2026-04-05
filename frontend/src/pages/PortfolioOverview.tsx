import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import './PortfolioOverview.css';

const API = '/api/v1';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ─── Types ───────────────────────────────────────────────────────────────────

interface AssetAllocation {
  stocks: number;
  options: number;
  dividends: number;
}

interface TopPerformer {
  symbol: string;
  change_pct: number;
  current_value: number;
}

interface UpcomingDividend {
  symbol: string;
  ex_dividend_date: string;
  payment_date: string;
  amount_per_share: number;
}

interface AISignalsSummary {
  buy: number;
  hold: number;
  sell: number;
}

interface RecentAlert {
  id: string;
  symbol: string;
  condition_type: string;
  threshold: number;
  triggered_at: string | null;
}

interface OptionsGreeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

interface PortfolioOverview {
  total_value: number;
  daily_change: number;
  daily_change_pct: number;
  asset_allocation: AssetAllocation;
  top_gainers: TopPerformer[];
  top_losers: TopPerformer[];
  upcoming_dividends: UpcomingDividend[];
  ai_signals_summary: AISignalsSummary;
  portfolio_health_score: number;
  recent_alerts: RecentAlert[];
  options_greeks: OptionsGreeks;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const GREEK_COLORS = ['#4ade80', '#60a5fa', '#f97316', '#a78bfa'];
const ALLOCATION_COLORS = ['#4ade80', '#f97316', '#60a5fa'];
const SIGNAL_COLORS = { buy: '#4ade80', hold: '#fbbf24', sell: '#f87171' };

// ─── Sub-components ──────────────────────────────────────────────────────────

function HealthBadge({ score }: { score: number }) {
  const color = score >= 70 ? '#4ade80' : score >= 40 ? '#fbbf24' : '#f87171';
  const label = score >= 70 ? 'Excellent' : score >= 40 ? 'Fair' : 'Poor';
  return (
    <div className="health-badge" style={{ borderColor: color }}>
      <span className="health-score" style={{ color }}>{score}</span>
      <span className="health-label">{label}</span>
    </div>
  );
}

function SignalBar({ summary }: { summary: AISignalsSummary }) {
  const total = summary.buy + summary.hold + summary.sell || 1;
  return (
    <div className="signal-bar-container">
      <div className="signal-bar">
        <div className="signal-segment buy" style={{ width: `${(summary.buy / total) * 100}%` }} />
        <div className="signal-segment hold" style={{ width: `${(summary.hold / total) * 100}%` }} />
        <div className="signal-segment sell" style={{ width: `${(summary.sell / total) * 100}%` }} />
      </div>
      <div className="signal-legend">
        <span className="signal-item"><span className="dot" style={{ background: SIGNAL_COLORS.buy }} />Buy: {summary.buy}</span>
        <span className="signal-item"><span className="dot" style={{ background: SIGNAL_COLORS.hold }} />Hold: {summary.hold}</span>
        <span className="signal-item"><span className="dot" style={{ background: SIGNAL_COLORS.sell }} />Sell: {summary.sell}</span>
      </div>
    </div>
  );
}

function GreekRow({ label, value, color }: { label: string; value: number; color: string }) {
  const sign = value >= 0 ? '+' : '';
  return (
    <div className="greek-row">
      <span className="greek-label">{label}</span>
      <span className="greek-bar-wrap">
        <span className="greek-bar" style={{ width: `${Math.min(Math.abs(value) * 50, 100)}%`, background: color }} />
      </span>
      <span className="greek-value" style={{ color }}>{sign}{value.toFixed(4)}</span>
    </div>
  );
}

function changeColor(pct: number) {
  return pct >= 0 ? '#4ade80' : '#f87171';
}

// ─── Main Component ──────────────────────────────────────────────────────────

const PortfolioOverview: React.FC = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<PortfolioOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchOverview = async () => {
    try {
      setError(null);
      const response = await axios.get(`${API}/portfolio/overview`, {
        headers: getAuthHeaders(),
      });
      setData(response.data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch portfolio overview:', err);
      setError('Failed to load portfolio overview.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="overview-loading"><div className="spinner" />{t('common.loading', 'Loading...')}</div>;
  }

  if (error || !data) {
    return (
      <div className="overview-error">
        <p>{error || 'No data'}</p>
        <button onClick={fetchOverview}>{t('common.retry', 'Retry')}</button>
      </div>
    );
  }

  const isPositive = data.daily_change >= 0;
  const changeSign = isPositive ? '+' : '';

  // Pie chart data
  const allocationData = [
    { name: 'Stocks', value: data.asset_allocation.stocks },
    { name: 'Options', value: data.asset_allocation.options },
    { name: 'Dividends', value: data.asset_allocation.dividends },
  ].filter(d => d.value > 0);

  // Greeks data
  const greeks = [
    { label: 'Delta', value: data.options_greeks.delta, color: GREEK_COLORS[0] },
    { label: 'Gamma', value: data.options_greeks.gamma, color: GREEK_COLORS[1] },
    { label: 'Theta', value: data.options_greeks.theta, color: GREEK_COLORS[2] },
    { label: 'Vega', value: data.options_greeks.vega, color: GREEK_COLORS[3] },
  ];

  // Format upcoming dividends
  const fmtDate = (iso: string) => {
    if (!iso) return '—';
    try { return new Date(iso).toLocaleDateString(); } catch { return iso; }
  };

  return (
    <div className="portfolio-overview">
      {/* ── Header ── */}
      <div className="overview-header">
        <h2>{t('portfolio.overview', 'Portfolio Overview')}</h2>
        <span className="refresh-time">
          {t('common.updatedAt', 'Updated')}: {lastRefresh.toLocaleTimeString()}
          <button className="refresh-btn" onClick={fetchOverview}>↻</button>
        </span>
      </div>

      {/* ── Row 1: Net Worth + Asset Allocation ── */}
      <div className="overview-row row-3col">
        {/* Net Worth Widget */}
        <div className="card net-worth-card">
          <h3>{t('overview.netWorth', 'Net Worth')}</h3>
          <div className="net-worth-value">${data.total_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="net-worth-change" style={{ color: changeColor(data.daily_change_pct) }}>
            {changeSign}{data.daily_change.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({changeSign}{data.daily_change_pct.toFixed(2)}%)
            <span className="change-label">{t('overview.today', 'Today')}</span>
          </div>
          <HealthBadge score={data.portfolio_health_score} />
        </div>

        {/* Asset Allocation */}
        <div className="card allocation-card">
          <h3>{t('overview.assetAllocation', 'Asset Allocation')}</h3>
          {allocationData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={allocationData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                >
                  {allocationData.map((_, i) => (
                    <Cell key={i} fill={ALLOCATION_COLORS[i % ALLOCATION_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="no-data">{t('overview.noHoldings', 'No holdings yet.')}</p>
          )}
          <div className="allocation-legend">
            <div className="alloc-item"><span className="dot" style={{ background: ALLOCATION_COLORS[0] }} />Stocks: ${data.asset_allocation.stocks.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <div className="alloc-item"><span className="dot" style={{ background: ALLOCATION_COLORS[1] }} />Options: ${data.asset_allocation.options.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <div className="alloc-item"><span className="dot" style={{ background: ALLOCATION_COLORS[2] }} />Dividends: ${data.asset_allocation.dividends.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          </div>
        </div>

        {/* AI Signals */}
        <div className="card signals-card">
          <h3>{t('overview.aiSignals', 'AI Signal Summary')}</h3>
          <SignalBar summary={data.ai_signals_summary} />
        </div>
      </div>

      {/* ── Row 2: Top Gainers / Losers ── */}
      <div className="overview-row row-2col">
        <div className="card">
          <h3>🏆 {t('overview.topGainers', 'Top Gainers')}</h3>
          {data.top_gainers.length > 0 ? (
            <table className="performers-table">
              <thead><tr><th>Symbol</th><th>{t('overview.change', 'Change %')}</th><th>{t('overview.value', 'Value')}</th></tr></thead>
              <tbody>
                {data.top_gainers.map(g => (
                  <tr key={g.symbol}>
                    <td className="symbol">{g.symbol}</td>
                    <td className="change" style={{ color: changeColor(g.change_pct) }}>+{g.change_pct.toFixed(2)}%</td>
                    <td>${g.current_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="no-data">{t('overview.noData', 'No data available')}</p>}
        </div>

        <div className="card">
          <h3>📉 {t('overview.topLosers', 'Top Losers')}</h3>
          {data.top_losers.length > 0 ? (
            <table className="performers-table">
              <thead><tr><th>Symbol</th><th>{t('overview.change', 'Change %')}</th><th>{t('overview.value', 'Value')}</th></tr></thead>
              <tbody>
                {data.top_losers.map(l => (
                  <tr key={l.symbol}>
                    <td className="symbol">{l.symbol}</td>
                    <td className="change" style={{ color: changeColor(l.change_pct) }}>{l.change_pct.toFixed(2)}%</td>
                    <td>${l.current_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="no-data">{t('overview.noData', 'No data available')}</p>}
        </div>
      </div>

      {/* ── Row 3: Upcoming Dividends + Options Greeks + Recent Alerts ── */}
      <div className="overview-row row-3col">
        <div className="card">
          <h3>💰 {t('overview.upcomingDividends', 'Upcoming Dividends (30d)')}</h3>
          {data.upcoming_dividends.length > 0 ? (
            <table className="dividends-table">
              <thead><tr><th>Symbol</th><th>Ex-Date</th><th>Payment</th><th>Amount</th></tr></thead>
              <tbody>
                {data.upcoming_dividends.map(d => (
                  <tr key={d.symbol + d.ex_dividend_date}>
                    <td className="symbol">{d.symbol}</td>
                    <td>{fmtDate(d.ex_dividend_date)}</td>
                    <td>{fmtDate(d.payment_date)}</td>
                    <td>${d.amount_per_share.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="no-data">{t('overview.noData', 'No upcoming dividends')}</p>}
        </div>

        <div className="card">
          <h3>📐 {t('overview.optionsGreeks', 'Options Greeks Summary')}</h3>
          <div className="greeks-container">
            {greeks.map(g => (
              <GreekRow key={g.label} label={g.label} value={g.value} color={g.color} />
            ))}
          </div>
        </div>

        <div className="card">
          <h3>🔔 {t('overview.recentAlerts', 'Recent Alerts')}</h3>
          {data.recent_alerts.length > 0 ? (
            <ul className="alerts-list">
              {data.recent_alerts.map(a => (
                <li key={a.id} className="alert-item">
                  <span className="alert-symbol">{a.symbol}</span>
                  <span className="alert-condition">
                    {a.condition_type} ${a.threshold}
                  </span>
                  <span className="alert-time">
                    {a.triggered_at ? fmtDate(a.triggered_at) : '—'}
                  </span>
                </li>
              ))}
            </ul>
          ) : <p className="no-data">{t('overview.noAlerts', 'No recent alerts')}</p>}
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview;
