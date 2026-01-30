import { Link } from 'react-router-dom'
import { Cpu } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
  showBack?: boolean
  backLabel?: string
  backTo?: string
}

export function Layout({ children, showBack = false, backLabel = 'Back to Home', backTo = '/' }: LayoutProps) {
  return (
    <div className="app-layout">
      <header className="df-header">
        <Link to="/" className="df-logo">
          <div className="df-logo-icon">
            <Cpu size={18} color="white" />
          </div>
          DF-InfoUI
        </Link>
        <nav className="df-nav">
          {showBack ? (
            <Link to={backTo}>{backLabel}</Link>
          ) : (
            <>
              <Link to="/#features">Features</Link>
              <Link to="/#docs">Documentation</Link>
              <Link to="/upload">Start Analysis</Link>
            </>
          )}
        </nav>
      </header>
      {children}
    </div>
  )
}
