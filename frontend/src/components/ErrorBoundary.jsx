import React, { Component } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      errorInfo,
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by ErrorBoundary:', error, errorInfo);
    }

    // You could also log to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      const { error } = this.state;
      const errorMessage = error?.message || 'Something went wrong';

      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
          background: 'var(--bg-color)',
        }}>
          <div style={{
            maxWidth: '500px',
            width: '100%',
            padding: '40px',
            background: 'var(--surface-panel)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '16px',
            textAlign: 'center',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 24px',
              borderRadius: '50%',
              background: 'rgba(218, 54, 51, 0.1)',
              border: '2px solid rgba(218, 54, 51, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <AlertCircle size={32} style={{ color: 'var(--danger)' }} />
            </div>

            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              marginBottom: '12px',
              margin: '0 0 12px 0',
            }}>
              Oops! Something went wrong
            </h2>

            <p style={{
              fontSize: '1rem',
              color: 'var(--text-secondary)',
              marginBottom: '24px',
              lineHeight: '1.6',
            }}>
              {errorMessage}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details style={{
                textAlign: 'left',
                marginBottom: '24px',
                padding: '16px',
                background: 'var(--surface-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                fontSize: '0.875rem',
                color: 'var(--text-muted)',
              }}>
                <summary style={{
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                  fontWeight: '500',
                  marginBottom: '8px',
                }}>
                  Error Details
                </summary>
                <pre style={{
                  margin: '0',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: '0.75rem',
                }}>
                  {this.state.error && this.state.error.toString()}
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'center',
            }}>
              <button
                onClick={this.handleReset}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  background: 'var(--accent)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => {
                  e.target.style.background = 'var(--accent-hover)';
                }}
                onMouseOut={(e) => {
                  e.target.style.background = 'var(--accent)';
                }}
              >
                <RefreshCw size={16} />
                Try Again
              </button>

              <button
                onClick={this.handleGoHome}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  background: 'transparent',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => {
                  e.target.style.background = 'var(--hover-surface)';
                  e.target.style.borderColor = 'var(--border-default)';
                  e.target.style.color = 'var(--text-primary)';
                }}
                onMouseOut={(e) => {
                  e.target.style.background = 'transparent';
                  e.target.style.borderColor = 'var(--border-subtle)';
                  e.target.style.color = 'var(--text-secondary)';
                }}
              >
                <Home size={16} />
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;