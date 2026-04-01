import { useState, useEffect } from 'react'
import { authService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Settings.css'

export default function Settings() {
  const { user } = useAuth()
  const [lineToken, setLineToken] = useState('')
  const [lineConnected, setLineConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadLineStatus()
  }, [])

  const loadLineStatus = async () => {
    try {
      const status = await authService.getLineTokenStatus()
      setLineConnected(status.line_notify_connected)
    } catch (err) {
      console.error('Failed to load LINE status:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveToken = async () => {
    if (!lineToken.trim()) {
      setMessage({ type: 'error', text: 'Please enter a LINE Notify token' })
      return
    }

    setIsSaving(true)
    setMessage(null)

    try {
      await authService.updateLineToken(lineToken.trim())
      setLineConnected(true)
      setLineToken('')
      setMessage({ type: 'success', text: 'LINE Notify connected successfully!' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to connect LINE Notify' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleTestToken = async () => {
    if (!lineToken.trim()) {
      setMessage({ type: 'error', text: 'Please enter a LINE Notify token first' })
      return
    }

    setIsTesting(true)
    setMessage(null)

    try {
      const result = await authService.testLineToken(lineToken.trim())
      if (result.success) {
        setMessage({ type: 'success', text: 'Test message sent! Check your LINE app.' })
      } else {
        setMessage({ type: 'error', text: result.message })
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Failed to send test message' })
    } finally {
      setIsTesting(false)
    }
  }

  const handleDisconnect = async () => {
    setIsSaving(true)
    setMessage(null)

    try {
      await authService.deleteLineToken()
      setLineConnected(false)
      setLineToken('')
      setMessage({ type: 'success', text: 'LINE Notify disconnected.' })
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Failed to disconnect LINE Notify' })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <div className="settings-loading">Loading...</div>
  }

  return (
    <div className="settings-container">
      <h2>Settings</h2>

      <div className="settings-section">
        <h3>Account</h3>
        <div className="settings-info">
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Email:</strong> {user?.email}</p>
        </div>
      </div>

      <div className="settings-section">
        <h3>LINE Notifications</h3>
        <p className="settings-description">
          Connect LINE Notify to receive stock alerts directly in your LINE app.
        </p>

        {lineConnected ? (
          <div className="line-connected">
            <div className="line-status">
              <span className="line-status-dot connected"></span>
              <span>LINE Notify is connected</span>
            </div>
            <button
              onClick={handleDisconnect}
              disabled={isSaving}
              className="btn-disconnect"
            >
              {isSaving ? 'Disconnecting...' : 'Disconnect'}
            </button>
          </div>
        ) : (
          <div className="line-setup">
            <div className="line-instructions">
              <h4>How to get your LINE Notify token:</h4>
              <ol>
                <li>Go to <a href="https://notify-bot.line.me/" target="_blank" rel="noopener noreferrer">LINE Notify</a></li>
                <li>Sign in with your LINE account</li>
                <li>Click "My page" in the menu</li>
                <li>Scroll down to "Generate token"</li>
                <li>Enter a token name (e.g., "Stock Tracker")</li>
                <li>Select "1-on-1 chat with LINE Notify"</li>
                <li>Click "Generate" and copy the token</li>
              </ol>
            </div>

            <div className="line-token-input">
              <label htmlFor="lineToken">LINE Notify Token</label>
              <input
                type="password"
                id="lineToken"
                value={lineToken}
                onChange={(e) => setLineToken(e.target.value)}
                placeholder="Paste your token here"
                disabled={isSaving || isTesting}
              />
            </div>

            {message && (
              <div className={`message ${message.type}`}>
                {message.text}
              </div>
            )}

            <div className="line-actions">
              <button
                onClick={handleTestToken}
                disabled={isSaving || isTesting || !lineToken.trim()}
                className="btn-test"
              >
                {isTesting ? 'Sending...' : 'Test Token'}
              </button>
              <button
                onClick={handleSaveToken}
                disabled={isSaving || isTesting || !lineToken.trim()}
                className="btn-connect"
              >
                {isSaving ? 'Connecting...' : 'Connect LINE Notify'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
