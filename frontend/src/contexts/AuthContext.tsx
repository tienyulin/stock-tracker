import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { authService, type User } from '../services/api'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'stock_tracker_token'
const USER_KEY = 'stock_tracker_user'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    const storedUser = localStorage.getItem(USER_KEY)
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    setError(null)
    setIsLoading(true)
    try {
      const response = await authService.login(email, password)
      setToken(response.access_token)
      localStorage.setItem(TOKEN_KEY, response.access_token)
      
      // Fetch user info
      const userInfo = await authService.getCurrentUser(response.access_token)
      setUser(userInfo)
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed'
      setError(message)
      throw new Error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (email: string, username: string, password: string) => {
    setError(null)
    setIsLoading(true)
    try {
      const response = await authService.signup(email, username, password)
      setToken(response.access_token)
      localStorage.setItem(TOKEN_KEY, response.access_token)
      
      // Fetch user info
      const userInfo = await authService.getCurrentUser(response.access_token)
      setUser(userInfo)
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Signup failed'
      setError(message)
      throw new Error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    setError(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    authService.logout()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        signup,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
