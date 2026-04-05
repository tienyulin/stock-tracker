import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
        <li><NavLink to="/portfolio-signals" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.portfolioSignals')}</NavLink></li>
        <li><NavLink to="/portfolio-health" className={({ isActive }) => isActive ? 'active' : ''}>{t('nav.portfolioHealth')}</NavLink></li>
        <li><NavLink to="/retirement" className={({ isActive }) => isActive ? 'active' : ''}>🎲 {t('nav.retirement', 'Retirement')}</NavLink></li>
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
        <Route path="/portfolio-health" element={<RequireAuth><PortfolioHealth /></RequireAuth>} />
        <Route path="/retirement" element={<RequireAuth><RetirementSimulation /></RequireAuth>} />
      </Routes>
    </Suspense>
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
