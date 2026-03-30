import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import type { StockHistory } from '../services/api'
import './StockChart.css'

interface StockChartProps {
  data: StockHistory
  symbol: string
}

function StockChart({ data, symbol }: StockChartProps) {
  if (!data || !data.timestamps || data.timestamps.length === 0) {
    return <div className="chart-empty">No chart data available</div>
  }

  // Format data for recharts
  const chartData = data.timestamps.map((ts, i) => ({
    date: new Date(ts * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    price: data.closes[i] ?? null,
    volume: data.volumes[i] ?? null,
  }))

  return (
    <div className="stock-chart">
      <h4>{symbol} Price History</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `$${v.toFixed(0)}`}
          />
          <Tooltip
            formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Price']}
            labelStyle={{ color: '#333' }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#2563eb' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default StockChart
