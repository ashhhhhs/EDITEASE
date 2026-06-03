import React, { useLayoutEffect, useRef, useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import SplitType from 'split-type';
import Lenis from 'lenis';
import logoMark from './assets/logo-mark.svg';
import './landing.css';
import './landing-v2.css';

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  { num: '01', label: 'Upload', body: 'Drop any video format. No conversion needed.' },
  { num: '02', label: 'Analyze', body: 'Scene boundaries and tags detected automatically.' },
  { num: '03', label: 'Review', body: 'Visual clip grid. Approve, flag, or skip.' },
  { num: '04', label: 'Download', body: 'Batch download organized videos or structured datasets.' },
];

const PRODUCT_EVIDENCE = [
  {
    label: 'Scene detection',
    title: 'Cuts are split into reviewable clips.',
    detail: 'The pipeline writes scene entries with thumbnails, timing, labels, and confidence context for later review.',
  },
  {
    label: 'Review queue',
    title: 'Uncertain results stay visible.',
    detail: 'Reviewers can approve, flag, or skip clips from a visual grid instead of searching through raw footage.',
  },
  {
    label: 'Export',
    title: 'Outputs remain structured.',
    detail: 'Teams can download organized folders or use JSON and CSV manifests for downstream editing and datasets.',
  },
];
function useMouseTilt(strength = 1) {
  const ref = useRef(null);
  const target = useRef({ x: 0, y: 0 });
  const current = useRef({ x: 0, y: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      target.current.x = ((e.clientX - (r.left + r.width / 2)) / (window.innerWidth / 2)) * strength;
      target.current.y = ((e.clientY - (r.top + r.height / 2)) / (window.innerHeight / 2)) * strength;
    };
    const tick = () => {
      const k = 0.08;
      current.current.x += (target.current.x - current.current.x) * k;
      current.current.y += (target.current.y - current.current.y) * k;
      el.style.setProperty('--mx', current.current.x.toFixed(3));
      el.style.setProperty('--my', current.current.y.toFixed(3));
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener('mousemove', onMove);
    raf = requestAnimationFrame(tick);
    return () => { window.removeEventListener('mousemove', onMove); cancelAnimationFrame(raf); };
  }, [strength]);
  return ref;
}

function useIdleDrift(ref, period = 8000, amp = 1) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf;
    const t0 = performance.now();
    const tick = (t) => {
      const phase = ((t - t0) / period) * Math.PI * 2;
      el.style.setProperty('--idle-x', (Math.sin(phase) * amp).toFixed(3));
      el.style.setProperty('--idle-y', (Math.cos(phase * 0.7) * amp).toFixed(3));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [ref, period, amp]);
}

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('[data-reveal]');
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    els.forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);
}

/* Film reel SVG */
const FilmReel = ({ size = 120 }) => (
  <svg className="film-reel" viewBox="0 0 100 100" width={size} height={size} aria-hidden="true">
    <defs>
      <radialGradient id="reel-grad" cx="50%" cy="50%">
        <stop offset="0%" stopColor="#0d1117"/>
        <stop offset="60%" stopColor="#161b22"/>
        <stop offset="100%" stopColor="#0d1117"/>
      </radialGradient>
    </defs>
    <circle cx="50" cy="50" r="48" fill="url(#reel-grad)" stroke="rgba(255,255,255,.10)" />
    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,.05)" />
    <g className="reel-spin" style={{ transformOrigin: '50px 50px' }}>
      {[0, 60, 120, 180, 240, 300].map(a => (
        <g key={a} transform={`rotate(${a} 50 50)`}>
          <ellipse cx="50" cy="22" rx="9" ry="6" fill="rgba(13,17,23,.95)" stroke="rgba(255,255,255,.08)" />
        </g>
      ))}
      <circle cx="50" cy="50" r="6" fill="#58a6ff" stroke="rgba(255,255,255,.15)" />
    </g>
  </svg>
);

/* Hero workspace preview */
const HeroDiorama = () => {
  const stageRef = useMouseTilt(1);
  const idleRef = useRef(null);
  useIdleDrift(idleRef, 9000, 1);

  return (
    <div className="diorama" ref={stageRef}>
      <div className="diorama-spot" />
      <div className="diorama-stage" ref={idleRef}>
        <div className="layer plane-shadow" />
        <div className="layer plane-sidebar">
          <div className="ds-rail">
            <div className="ds-rail-dot active" />
            <div className="ds-rail-dot" />
            <div className="ds-rail-dot" />
            <div className="ds-rail-dot" />
          </div>
          <div className="ds-list">
            <div className="ds-row active"><i /><span /></div>
            <div className="ds-row"><i /><span /></div>
            <div className="ds-row"><i /><span /></div>
            <div className="ds-row"><i /><span /></div>
            <div className="ds-row short"><i /><span /></div>
          </div>
        </div>
        <div className="layer plane-canvas">
          <div className="dc-bar">
            <span className="dc-dot r" /><span className="dc-dot y" /><span className="dc-dot g" />
            <span className="dc-title">editease / scene-board · take 04</span>
            <span className="dc-rec"><span />REC</span>
          </div>
          <div className="dc-grid">
            <div className="dc-shot wide">
              <div className="dc-thumb tone-blue"><div className="dc-scan" /><div className="dc-noise" /></div>
              <div className="dc-meta">
                <span className="dc-tag tag-blue">DIALOGUE · 0:42</span>
                <strong>Interview close-up</strong>
              </div>
            </div>
            <div className="dc-shot">
              <div className="dc-thumb tone-amber"><div className="dc-scan d2" /></div>
              <div className="dc-meta">
                <span className="dc-tag tag-amber">MOTION · 0:18</span>
                <strong>Crowd energy</strong>
              </div>
            </div>
            <div className="dc-shot">
              <div className="dc-thumb tone-green"><div className="dc-scan d3" /></div>
              <div className="dc-meta">
                <span className="dc-tag tag-green">PRODUCT · 0:09</span>
                <strong>Detail shot</strong>
              </div>
            </div>
          </div>
        </div>
        <div className="layer plane-timeline">
          <div className="tl-head">
            <span className="tl-time">00:00:42:18</span>
            <div className="tl-controls"><span /><span className="play" /><span /></div>
            <span className="tl-rate">24 FPS</span>
          </div>
          <div className="tl-tracks">
            <div className="tl-track">
              <div className="tl-clip a" /><div className="tl-clip b" /><div className="tl-clip c" />
            </div>
            <div className="tl-track sub">
              <div className="tl-clip d" /><div className="tl-clip e" />
            </div>
          </div>
          <div className="tl-playhead" />
        </div>
        <div className="layer plane-tags">
          <div className="float-tag tag-blue">
            <span className="tag-dot" />
            <div><b>+ Speaker tag</b><em>auto-detected</em></div>
          </div>
          <div className="float-tag tag-purple">
            <span className="tag-dot" />
            <div><b>4 emotions</b><em>warmth · focus · joy · calm</em></div>
          </div>
          <div className="float-tag tag-green">
            <span className="tag-dot" />
            <div><b>Approved</b><em>ready for export</em></div>
          </div>
        </div>
        <div className="layer plane-reel">
          <FilmReel size={140} />
        </div>
      </div>
      <div className="diorama-floor" />
    </div>
  );
};

/* Capability card */
const CapCard3D = ({ c, i }) => {
  const ref = useRef(null);
  const onMove = useCallback((e) => {
    const el = ref.current; if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--cx', (((e.clientX - r.left) / r.width) - 0.5).toFixed(3));
    el.style.setProperty('--cy', (((e.clientY - r.top) / r.height) - 0.5).toFixed(3));
  }, []);
  const onLeave = useCallback(() => {
    const el = ref.current; if (!el) return;
    el.style.setProperty('--cx', '0'); el.style.setProperty('--cy', '0');
  }, []);
  const accents = ['blue', 'purple', 'green', 'blue'];
  return (
    <div
      ref={ref}
      className={`lp2-cap accent-${accents[i % 4]}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      data-reveal
      style={{ '--rd': `${i * 90}ms` }}
    >
      <div className="lp2-cap-glow" />
      <div className="lp2-cap-kicker mono-caps">{c.kicker}</div>
      <h3 className="lp2-cap-title">{c.title}</h3>
      <p className="lp2-cap-body">{c.desc}</p>
    </div>
  );
};

const CAPS_3D = [
  { kicker: 'Vision',   title: 'Scene-aware indexing',    desc: 'Every shot fingerprinted with composition, motion, and color tags. No manual timecoding.' },
  { kicker: 'Pipeline', title: '4-step ingest to export', desc: 'A single rail from raw upload to dataset, organized clips, or NLE handoff.' },
  { kicker: 'Roles',    title: 'Editor and admin', desc: 'Surface only what each role needs. Bulk-approve or moderate visually.' },
  { kicker: 'Export',   title: 'Structured downloads',    desc: 'JSON / CSV manifests or auto-organized folders — batch-ready in one click.' },
];

/* Main component */
export default function Landing() {
  const containerRef = useRef(null);
  const curtainRef = useRef(null);
  const deviceRef = useRef(null);
  const btnLaunchNavRef = useRef(null);
  const pageSpotRef = useRef(null);
  const [, setCurtainDone] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const isLoggedIn = !!localStorage.getItem('token');

  useReveal();

  /* scroll Y for diorama tilt */
  useEffect(() => {
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { setScrollY(window.scrollY); ticking = false; });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* page spotlight cursor */
  const onSpotMove = useCallback((e) => {
    pageSpotRef.current?.style.setProperty('--gx', `${e.clientX}px`);
    pageSpotRef.current?.style.setProperty('--gy', `${e.clientY}px`);
  }, []);

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Cursor parallax on the preview */
  const onMouseMove = useCallback(e => {
    if (!deviceRef.current || prefersReducedMotion) return;
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;
    const dx = (e.clientX - cx) * -0.015;
    const dy = (e.clientY - cy) * -0.015;
    gsap.to(deviceRef.current, { x: dx, y: dy, duration: 0.8, ease: 'power1.out' });
  }, [prefersReducedMotion]);

  const onMouseLeave = useCallback(() => {
    if (!deviceRef.current) return;
    gsap.to(deviceRef.current, { x: 0, y: 0, duration: 0.8, ease: 'power1.out' });
  }, []);

  /* Magnetic nav CTA */
  const onLaunchMove = useCallback(e => {
    if (prefersReducedMotion) return;
    const btn = btnLaunchNavRef.current;
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const dx = e.clientX - (rect.left + rect.width / 2);
    const dy = e.clientY - (rect.top + rect.height / 2);
    gsap.to(btn, { x: dx * 0.28, y: dy * 0.28, duration: 0.3, ease: 'power1.out' });
  }, [prefersReducedMotion]);

  const onLaunchLeave = useCallback(() => {
    gsap.to(btnLaunchNavRef.current, { x: 0, y: 0, duration: 0.5, ease: 'elastic.out(1,0.5)' });
  }, []);

  /* GSAP page setup */
  useLayoutEffect(() => {
    if (!containerRef.current) return;

    const lenis = new Lenis({
      duration: 1.2,
      easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    lenis.on('scroll', ScrollTrigger.update);
    const tickerRAF = (time) => lenis.raf(time * 1000);
    gsap.ticker.add(tickerRAF);
    gsap.ticker.lagSmoothing(0);

    const nav = containerRef.current.querySelector('.landing-nav');
    const onScroll = () => nav?.classList.toggle('scrolled', window.scrollY > 60);
    window.addEventListener('scroll', onScroll, { passive: true });

    let splitInstances = [];

    const ctx = gsap.context(() => {
      /* scroll progress bar */
      gsap.to('.scroll-progress', {
        scaleX: 1,
        ease: 'none',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top top',
          end: 'bottom bottom',
          scrub: true,
        },
      });

      /* Curtain lift into the hero entrance sequence */
      const tl = gsap.timeline({
        onComplete: () => setCurtainDone(true),
      });

      if (!prefersReducedMotion && curtainRef.current) {
        tl.to(curtainRef.current, {
          yPercent: -110,
          duration: 0.95,
          ease: 'power4.inOut',
        });
      } else {
        tl.set(curtainRef.current, { yPercent: -110 });
        setCurtainDone(true);
      }

      /* H1 per-character 3-D tumble */
      const h1 = document.querySelector('.display-h1');
      if (h1 && !prefersReducedMotion) {
        const split = new SplitType(h1, { types: 'chars,words' });
        splitInstances.push(split);
        split.chars.forEach(c => {
          const wrap = document.createElement('span');
          wrap.style.cssText = 'display:inline-block;overflow:hidden;vertical-align:bottom;';
          c.parentNode.insertBefore(wrap, c);
          wrap.appendChild(c);
        });
        tl.from(
          split.chars,
          {
            yPercent: 110,
            opacity: 0,
            rotateX: -40,
            transformOrigin: '50% 100%',
            stagger: 0.025,
            duration: 0.72,
            ease: 'expo.out',
          },
          '-=0.5',
        );
      }

      /* hero device entrance */
      if (deviceRef.current && !prefersReducedMotion) {
        tl.from(
          deviceRef.current,
          { scale: 0.92, opacity: 0, y: 40, duration: 1.1, ease: 'expo.out' },
          '-=0.7',
        );
      }

      /* general fade-ups */
      gsap.utils.toArray('.fade-up').forEach(el => {
        gsap.from(el, {
          y: 28,
          opacity: 0,
          duration: 0.75,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 90%' },
        });
      });

      /* steps with scrub progress bar */
      const stepsSection = document.querySelector('#how-it-works');
      if (stepsSection) {
        gsap.to('.steps-progress-bar', {
          scaleX: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: stepsSection,
            start: 'top 78%',
            end: 'bottom 60%',
            scrub: true,
          },
        });
      }

      gsap.utils.toArray('.step-item').forEach((el, i) => {
        gsap.from(el, {
          y: 24,
          opacity: 0,
          duration: 0.6,
          ease: 'power2.out',
          delay: i * 0.09,
          scrollTrigger: { trigger: el, start: 'top 88%' },
        });
      });

      /* footer headline word-by-word */
      const footerH2 = document.querySelector('.landing-footer .display-h2');
      if (footerH2 && !prefersReducedMotion) {
        const footerSplit = new SplitType(footerH2, { types: 'words' });
        splitInstances.push(footerSplit);
        footerSplit.words.forEach(w => {
          const wrap = document.createElement('span');
          wrap.style.cssText = 'display:inline-block;overflow:hidden;margin-right:0.25em;vertical-align:bottom;';
          w.parentNode.insertBefore(wrap, w);
          wrap.appendChild(w);
        });
        gsap.from(footerSplit.words, {
          y: 40,
          opacity: 0,
          stagger: 0.1,
          duration: 0.75,
          ease: 'power3.out',
          scrollTrigger: { trigger: footerH2, start: 'top 85%' },
        });
      }
    }, containerRef.current);

    return () => {
      gsap.ticker.remove(tickerRAF);
      lenis.destroy();
      window.removeEventListener('scroll', onScroll);
      ctx.revert();
      splitInstances.forEach(s => s.revert());
    };
  }, [prefersReducedMotion]);

  return (
    <div
      className="landing-page"
      ref={(el) => { containerRef.current = el; pageSpotRef.current = el; }}
      onMouseMove={(e) => { onMouseMove(e); onSpotMove(e); }}
      onMouseLeave={onMouseLeave}
      style={{ '--gx': '50vw', '--gy': '30vh' }}
    >
      {/* mouse spotlight */}
      <div className="lp2-spot" aria-hidden="true" />

      {/* scroll progress */}
      <div className="scroll-progress" aria-hidden="true" />

      {/* curtain */}
      <div className="landing-curtain" ref={curtainRef} aria-hidden="true" />

      {/* atmosphere */}
      <div className="landing-atmosphere landing-atmosphere-a" aria-hidden="true" />
      <div className="landing-atmosphere landing-atmosphere-b" aria-hidden="true" />
      <div className="landing-atmosphere landing-atmosphere-c" aria-hidden="true" />
      <div className="landing-grid-overlay" aria-hidden="true" />

      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-container landing-nav-inner">
          <Link to="/" className="landing-logo" aria-label="EditEase home">
            <img src={logoMark} alt="" width="34" height="34" className="landing-logo-mark" />
            <span className="landing-logo-text">EditEase</span>
          </Link>
          <div className="landing-links">
            <a href="#how-it-works" className="landing-nav-link">How it works</a>
            <a href="#capabilities" className="landing-nav-link">Capabilities</a>
            <Link
              to={isLoggedIn ? '/app/dashboard' : '/login'}
              className="btn-launch"
              ref={btnLaunchNavRef}
              onMouseMove={onLaunchMove}
              onMouseLeave={onLaunchLeave}
            >
              {isLoggedIn ? 'Open Workspace →' : 'Get Started →'}
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-section hero">
        <div className="landing-container hero-grid">
          <div className="hero-copy">
            <h1 className="display-h1" style={{ marginBottom: '2rem' }}>
              Stop sorting
              <br />
              footage manually.
            </h1>
            <p className="body-large fade-up hero-lead">
              Upload your videos. EditEase detects every scene, analyzes emotion,
              and gives you a review workspace in minutes.
            </p>
            <div className="fade-up hero-actions">
              <Link to={isLoggedIn ? '/app/dashboard' : '/login'} className="btn-launch btn-launch-hero">
                {isLoggedIn ? 'Open Workspace →' : 'Get Started →'}
              </Link>
              <a href="#how-it-works" className="btn-ghost">See how it works ↓</a>
            </div>
            <div className="hero-metrics fade-up">
              <div className="hero-metric-card">
                <span className="hero-metric-value">4-step</span>
                <span className="hero-metric-label">workflow from ingest to export</span>
              </div>
              <div className="hero-metric-card">
                <span className="hero-metric-value">Role-aware</span>
                <span className="hero-metric-label">review, admin, and editor surfaces</span>
              </div>
              <div className="hero-metric-card">
                <span className="hero-metric-value">Visual</span>
                <span className="hero-metric-label">clip-first moderation with instant context</span>
              </div>
            </div>
          </div>

          <div
            className="lp2-hero-stage fade-up"
            style={{ '--scroll-tilt': `${Math.min(scrollY * 0.04, 12)}deg` }}
          >
            <HeroDiorama />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="landing-section" id="how-it-works">
        <div className="landing-container">
          <div className="section-kicker fade-up">
            <div className="mono-caps">How it works</div>
            <p>One pipeline from raw footage to structured review-ready clips.</p>
          </div>
          <div className="lp2-steps">
            {STEPS.map((s, i) => (
              <div key={s.num} className="lp2-step" data-reveal style={{ '--rd': `${i * 90}ms` }}>
                <div className="lp2-step-num">{s.num}</div>
                <div className="lp2-step-label">{s.label}</div>
                <div className="lp2-step-body">{s.body}</div>
                <div className="lp2-step-bar"><div /></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="landing-section" id="capabilities">
        <div className="landing-container">
          <div className="section-kicker fade-up">
            <div className="mono-caps">What it does</div>
            <p>Built for teams that need visual intelligence, not a plain upload form.</p>
          </div>
          <div className="lp2-caps">
            {CAPS_3D.map((c, i) => <CapCard3D key={c.title} c={c} i={i} />)}
          </div>
        </div>
      </section>

      {/* Review workspace preview */}
      <section className="landing-section fade-up" style={{ paddingTop: 0 }}>
        <div className="landing-container">
          <div className="section-kicker section-kicker-centered">
            <div className="mono-caps">The review workspace</div>
            <p>Clip thumbnails, role-based controls, and a surface that feels purpose-built for footage.</p>
          </div>
          <div className="preview-window">
            <div className="preview-header">
              <div className="preview-dot" style={{ background: '#ff5f57' }} />
              <div className="preview-dot" style={{ background: '#febc2e' }} />
              <div className="preview-dot" style={{ background: '#28c840' }} />
              <div className="mono-caps" style={{ marginLeft: 'auto', fontSize: '0.82rem' }}>editease / review queue</div>
            </div>
            <div className="preview-body">
              <div className="preview-sidebar">
                <div className="preview-sidebar-logo" />
                {['Dashboard', 'Review Queue', 'Uploads', 'Organized Videos'].map((item, i) => (
                  <div key={item} className={`preview-nav-item ${i === 1 ? 'active' : ''}`}>{item}</div>
                ))}
              </div>
              <div className="preview-clips">
                {[
                  { status: 'APPROVED', shade: '1a2c1a' },
                  { status: 'PENDING', shade: '1a2030' },
                  { status: 'FLAGGED', shade: '2c1a1a' },
                  { status: 'APPROVED', shade: '1a2c1a' },
                  { status: 'PENDING', shade: '1a2030' },
                  { status: 'APPROVED', shade: '1a2c1a' },
                ].map((clip, i) => (
                  <div key={i} className="preview-clip-card" style={{ background: `#${clip.shade}` }}>
                    <div className="preview-clip-bar" />
                    <span className={`preview-clip-badge ${clip.status.toLowerCase()}`}>{clip.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product evidence */}
      <section className="landing-section social-proof">
        <div className="landing-container">
          <div className="section-kicker section-kicker-centered fade-up">
            <div className="mono-caps">Product evidence</div>
            <p>Grounded in the workflow EditEase already supports: ingest footage, review uncertain clips, and export usable structure.</p>
          </div>
          <div className="evidence-row">
            {PRODUCT_EVIDENCE.map((item, i) => (
              <div key={item.label} className="evidence-card fade-up" style={{ '--rd': `${i * 80}ms` }}>
                <div className="evidence-label">{item.label}</div>
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
                <div className="evidence-line" />
              </div>
            ))}
          </div>
          <div className="evidence-note fade-up">
            <span>Review roles</span>
            <span>Scene index JSON</span>
            <span>CSV manifests</span>
            <span>Organized folders</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-section landing-footer fade-up">
        <div className="landing-container landing-footer-inner">
          <div>
            <h2 className="display-h2" style={{ marginBottom: '1.5rem' }}>
              Stop sorting manually.
            </h2>
            <Link
              to={isLoggedIn ? '/app/dashboard' : '/login'}
              className="btn-launch"
              style={{ fontSize: '1rem', padding: '14px 28px' }}
            >
              {isLoggedIn ? 'Open Workspace →' : 'Get Started →'}
            </Link>
          </div>
          <div className="mono-caps footer-copyright">
            Copyright © {new Date().getFullYear()} EditEase. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
