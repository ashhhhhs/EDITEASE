import React, { useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Wand2, AlertTriangle, CheckCircle, Scissors, Grid3X3, Shield } from 'lucide-react';
import gsap from 'gsap';
import logoMark from '../assets/logo-mark.svg';
import '../auth.css';

const DEFAULT_BULLETS = [
  { Icon: Scissors, color: '#58a6ff', label: 'Scene detection' },
  { Icon: Grid3X3,  color: '#3fb950', label: 'Batch review' },
  { Icon: Shield,   color: '#a371f7', label: 'Role-based access' },
];

export default function AuthShell({
  children,
  title,
  subtitle,
  icon: Icon = Wand2,
  iconClassName = '',
  maxWidth = 400,
  error,
  success,
  split = false,
  asideHeadline = 'Stop sorting footage manually.',
  asideLede = 'A clip-first review workspace for editors, reviewers, and post-production teams.',
  asideBullets = DEFAULT_BULLETS,
  asideEyebrow,
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
        clearProps: 'transform,opacity',
      });
      gsap.from('.auth-aside', {
        x: -20,
        opacity: 0,
        duration: 0.7,
        ease: 'power2.out',
        clearProps: 'transform,opacity',
      });
      gsap.from('.auth-aside-bullet', {
        x: -10,
        opacity: 0,
        duration: 0.4,
        stagger: 0.08,
        delay: 0.3,
        ease: 'power2.out',
        clearProps: 'transform,opacity',
      });
      gsap.from('.auth-brand', {
        opacity: 0,
        duration: 0.8,
        ease: 'power2.out',
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const cardHead = (title || subtitle) && (
    <div className="auth-card-head">
      <div className="auth-card-icon">
        {Icon && <Icon size={28} color="var(--accent)" className={iconClassName} />}
      </div>
      <h1 className="auth-card-title">{title}</h1>
      {subtitle && <p className="auth-card-subtitle">{subtitle}</p>}
    </div>
  );

  const statusBlocks = (
    <>
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
    </>
  );

  if (split) {
    return (
      <div className="auth-shell auth-shell-split" ref={containerRef}>
        <div className="auth-atmosphere-a" />
        <div className="auth-atmosphere-b" />

        <div className="auth-split">
          <aside className="auth-aside">
            <Link to="/" className="auth-aside-brand" aria-label="EditEase home">
              <img src={logoMark} alt="" width="36" height="36" />
              <span>EditEase</span>
            </Link>

            <div className="auth-aside-body">
              <h2 className="auth-aside-headline">{asideHeadline}</h2>
              <p className="auth-aside-lede">{asideLede}</p>
              <div className="auth-aside-bullets">
                {asideBullets.map((b, i) => (
                  <div key={i} className="auth-aside-bullet">
                    <b.Icon size={16} color={b.color} />
                    <span>{b.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="auth-aside-foot mono-caps">
              EDITEASE · review workspace
            </div>
          </aside>

          <div className="auth-card auth-card-split">
            {asideEyebrow && (
              <div className="auth-eyebrow mono-caps">{asideEyebrow}</div>
            )}
            {cardHead}
            {statusBlocks}
            {children}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell" ref={containerRef}>
      <div className="auth-atmosphere-a" />
      <div className="auth-atmosphere-b" />

      <Link to="/" className="auth-brand" aria-label="EditEase home">
        <img src={logoMark} alt="" className="auth-brand-mark" width="36" height="36" />
        <span className="auth-brand-text">EditEase</span>
      </Link>

      <div className="auth-content">
        <div className="auth-card" style={{ maxWidth: `${maxWidth}px` }}>
          {cardHead}
          {statusBlocks}
          {children}
        </div>
      </div>
    </div>
  );
}
