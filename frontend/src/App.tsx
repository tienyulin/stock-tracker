import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './pages/Dashboard'
import Watchlist from './pages/Watchlist'
import Alerts from './pages/Alerts'
import StockSearch from './pages/StockSearch'
import Login from './pages/Login'
import Signup from './pages/Signup'
import './App.css'

function NavBar() {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <nav className="navbar">
      <h1>Stock Tracker</h1>
      <ul className="nav-links">
        <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink></li>
        <li><NavLink to="/search" className={({ isActive }) => isActive ? 'active' : ''}>Search</NavLink></li>
        <li><NavLink to="/watchlist" className={({ isActive }) => isActive ? 'active' : ''}>Watchlist</NavLink></li>
        <li><NavLink to="/alerts" className={({ isActive }) => isActive ? 'active' : ''}>Alerts</NavLink></li>
      </ul>
      <div className="nav-auth">
        {isAuthenticated ? (
          <>
            <span className="nav-user">{user?.username || user?.email}</span>
            <button onClick={logout} className="btn-logout">Logout</button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="btn-nav">Login</NavLink>
            <NavLink to="/signup" className="btn-nav">Sign Up</NavLink>
          </>
        )}
      </div>
    </nav>
  )
}

// Protected route wrapper
function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return <div className="loading">Loading...</div>
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/search" element={<RequireAuth><StockSearch /></RequireAuth>} />
      <Route path="/watchlist" element={<RequireAuth><Watchlist /></RequireAuth>} />
      <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app">
          <NavBar />
          <main className="main-content">
            <ErrorBoundary>
              <AppRoutes />
            </ErrorBoundary>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
