import { useAuth0 } from '@auth0/auth0-react'
import { Navigate } from 'react-router-dom'

/**
 * Wraps routes that require authentication.
 * If not logged in, redirects to the landing page.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth0()

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#0A0A0B',
        color: '#8A8A93',
        fontFamily: "'JetBrains Mono', monospace",
        gap: '14px',
        flexDirection: 'column',
      }}>
        <div style={{
          width: 36,
          height: 36,
          border: '3px solid #2A2A2E',
          borderTopColor: '#FF9900',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <span>Verifying credentials...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/landing" replace />
  }

  return children
}
