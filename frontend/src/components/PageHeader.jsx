import React, { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';
import SplitType from 'split-type';

/**
 * Editorial PageHeader — Danik Bartolini composition style.
 * Integrates cinematic SplitType text tumble for titles and GSAP layout fading
 * with strict checks for memory cleanup and reduced-motion states.
 */
export default function PageHeader({ title, description, actions, breadcrumbs, eyebrow, gradientTitle }) {
  const headerRef = useRef(null);

  useLayoutEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let splitTitle;

    if (!headerRef.current) return;

    const ctx = gsap.context(() => {
      const h1 = headerRef.current?.querySelector('.display-title');
      const desc = headerRef.current?.querySelector('.display-subtitle');
      
      const tl = gsap.timeline();

      // Title split and tumble
      if (!prefersReducedMotion && h1) {
        splitTitle = new SplitType(h1, { types: 'chars,words' });
        splitTitle.chars.forEach(c => {
          const wrap = document.createElement('span');
          wrap.style.cssText = 'display:inline-block;overflow:hidden;vertical-align:bottom;';
          c.parentNode.insertBefore(wrap, c);
          wrap.appendChild(c);
        });
        
        tl.from(splitTitle.chars, {
          yPercent: 110,
          opacity: 0,
          rotateX: -40,
          transformOrigin: '50% 100%',
          stagger: 0.025,
          duration: 0.72,
          ease: 'expo.out'
        });
      } else if (h1) {
        // Fallback for reduced motion
        tl.from(h1, { opacity: 0, duration: 0.5 });
      }

      // Subtitle fade-up
      if (desc) {
        tl.from(desc, {
          opacity: 0,
          y: !prefersReducedMotion ? 12 : 0,
          duration: 0.6,
          ease: 'power2.out'
        }, prefersReducedMotion ? "-=0" : "-=0.4");
      }
    }, headerRef.current);

    return () => {
      if (splitTitle) splitTitle.revert();
      ctx.revert();
    };
  }, [title, description]);

  return (
    <header ref={headerRef} style={{
      paddingBottom: 'var(--space-40)',
      marginBottom: 'var(--space-40)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-16)',
    }}>
      {/* Top row: breadcrumbs + actions */}
      {(breadcrumbs || actions) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {breadcrumbs && (
            <div style={{ fontSize: 'var(--font-meta)', color: 'var(--text-muted)', display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
              {breadcrumbs}
            </div>
          )}
          {actions && (
            <div style={{ display: 'flex', gap: 'var(--space-12)', alignItems: 'center', marginLeft: 'auto' }}>
              {actions}
            </div>
          )}
        </div>
      )}

      {/* Eyebrow */}
      {eyebrow && (
        <div className="mono-caps" style={{ color: 'var(--accent)', opacity: 0.8 }}>{eyebrow}</div>
      )}

      {/* Title */}
      <h1 className={`display-title${gradientTitle ? ' display-title--gradient' : ''}`}>{title}</h1>

      {/* Description */}
      {description && (
        <p className="display-subtitle">{description}</p>
      )}
    </header>
  );
}
