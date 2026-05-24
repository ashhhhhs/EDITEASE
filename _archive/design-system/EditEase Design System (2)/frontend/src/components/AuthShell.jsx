import React, { useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Wand2, AlertTriangle, CheckCircle } from 'lucide-react';
import gsap from 'gsap';
import '../auth.css';

export default function AuthShell({ 
  children, 
  title, 
  subtitle, 
  icon: Icon = Wand2, 
  iconClassName = '',
  maxWidth = 400,
  error,
  success
}) {
  const containerRef = useRef(null);
  
  useLayoutEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from('.auth-card', {
        y: 20,
        opacity: 0,
        duration: 0.6,
        ease: 'power2.out',
        clearProps: 'transform,opacity' // prevents sticking inline transforms without erasing maxWidth
      });
      // Optionally animate brand
      gsap.from('.auth-brand', {
        opacity: 0,
        duration: 0.8,
        ease: 'power2.out'
      });
    }, containerRef);
    
    return () => ctx.revert();
  }, []);

  return (
    <div className="auth-shell" ref={containerRef}>
      <div className="auth-atmosphere-a" />
      <div className="auth-atmosphere-b" />

      <Link to="/" className="auth-brand">
        <div className="auth-brand-icon">
          <Wand2 size={18} color="var(--accent)" />
        </div>
        <span>EditEase</span>
      </Link>

      <div className="auth-content">
        <div className="auth-card" style={{ maxWidth: `${maxWidth}px` }}>
          
          {(title || subtitle) && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-16)', marginBottom: 'var(--space-32)', textAlign: 'center' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(88, 166, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(88, 166, 255, 0.2)' }}>
                {Icon && <Icon size={32} color="var(--accent)" className={iconClassName} />}
              </div>
              <h1 style={{ margin: 0, fontSize: 'var(--font-title-section)', fontWeight: 600 }}>{title}</h1>
              {subtitle && <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '15px' }}>{subtitle}</p>}
            </div>
          )}

          {error && (
            <div className="auth-status-card auth-status-error">
              <AlertTriangle size={18} style={{ flexShrink: 0 }} /> <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="auth-status-card auth-status-success">
              <CheckCircle size={18} style={{ flexShrink: 0 }} /> <span>{success}</span>
            </div>
          )}

          {children}
        </div>
      </div>
    </div>
  );
}
