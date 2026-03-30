import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Watchlist from './pages/Watchlist'
import Alerts from './pages/Alerts'
import StockSearch from './pages/StockSearch'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <h1>Stock Tracker</h1>
          <ul className="nav-links">
            <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink></li>
            <li><NavLink to="/search" className={({ isActive }) => isActive ? 'active' : ''}>Search</NavLink></li>
            <li><NavLink to="/watchlist" className={({ isActive }) => isActive ? 'active' : ''}>Watchlist</NavLink></li>
            <li><NavLink to="/alerts" className={({ isActive }) => isActive ? 'active' : ''}>Alerts</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<StockSearch />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/alerts" element={<Alerts />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
