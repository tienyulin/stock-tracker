import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
<<<<<<< HEAD
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './pages/Dashboard'
import Watchlist from './pages/Watchlist'
import Alerts from './pages/Alerts'
import StockSearch from './pages/StockSearch'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Portfolio from './pages/Portfolio'
import PortfolioSignals from './pages/PortfolioSignals'
import RetirementSimulation from './pages/RetirementSimulation'
import './App.css'

=======
import { lazy, Suspense } from 'react'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import './App.css'

// Lazy load all page components for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Watchlist = lazy(() => import('./pages/Watchlist'))
const Alerts = lazy(() => import('./pages/Alerts'))
const StockSearch = lazy(() => import('./pages/StockSearch'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const Portfolio = lazy(() => import('./pages/Portfolio'))
const PortfolioSignals = lazy(() => import('./pages/PortfolioSignals'))

>>>>>>> origin/develop
function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'zh-TW' : 'en'
    i18n.changeLanguage(newLang)
  }

  return (
    <button onClick={toggleLanguage} className="btn-lang-switch" title="Toggle Language">
      {i18n.language === 'en' ? '中文' : 'EN'}
    </button>
  )
}

function NavBar() {
  const { t } = useTranslation()
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <nav className="navbar">
      <h1>Stock Tracker</h1>
      <ul className="nav-links">
        <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.dashboard')}</NavLink></li>
        <li><NavLink to="/search" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.dashboard')}</NavLink></li>
        <li><NavLink to="/watchlist" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.watchlist')}</NavLink></li>
        <li><NavLink to="/alerts" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.alerts')}</NavLink></li>
        <li><NavLink to="/portfolio" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.portfolio')}</NavLink></li>
        <li><NavLink to="/portfolio-signals" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.portfolio')}</NavLink></li>
<<<<<<< HEAD
        <li><NavLink to="/retirement" className={({ isActive }) => isActive ? 'active' : ''}>🎲 {t('nav.retirement', 'Retirement')}</NavLink></li>
=======
>>>>>>> origin/develop
        <li><NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.settings')}</NavLink></li>
      </ul>
      <div className="nav-auth">
        <LanguageSwitcher />
        {isAuthenticated ? (
          <>
            <span className="nav-user">{user?.username || user?.email}</span>
            <button onClick={logout} className="btn-logout">{t('nav.logout')}</button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="btn-nav">{t('auth.login')}</NavLink>
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
    return <LoadingFallback />
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function LoadingFallback() {
  return <div className="loading">Loading...</div>
}

function AppRoutes() {
  return (
<<<<<<< HEAD
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/search" element={<RequireAuth><StockSearch /></RequireAuth>} />
      <Route path="/watchlist" element={<RequireAuth><Watchlist /></RequireAuth>} />
      <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
      <Route path="/portfolio" element={<RequireAuth><Portfolio /></RequireAuth>} />
      <Route path="/portfolio-signals" element={<RequireAuth><PortfolioSignals /></RequireAuth>} />
      <Route path="/retirement" element={<RequireAuth><RetirementSimulation /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
    </Routes>
=======
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/search" element={<RequireAuth><StockSearch /></RequireAuth>} />
        <Route path="/watchlist" element={<RequireAuth><Watchlist /></RequireAuth>} />
        <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
        <Route path="/portfolio" element={<RequireAuth><Portfolio /></RequireAuth>} />
        <Route path="/portfolio-signals" element={<RequireAuth><PortfolioSignals /></RequireAuth>} />
        <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
      </Routes>
    </Suspense>
>>>>>>> origin/develop
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
