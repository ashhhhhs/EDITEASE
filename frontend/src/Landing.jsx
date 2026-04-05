import React, { useLayoutEffect, useRef, useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Scissors, Grid3X3, Download, Shield } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import SplitType from 'split-type';
import Lenis from 'lenis';
import './landing.css';

gsap.registerPlugin(ScrollTrigger);

const CAPABILITIES = [
  {
    title: 'Scene detection',
    desc: 'Automatically splits continuous footage into distinct, reviewable scenes based on visual cuts. No manual timecoding.',
    accent: 'var(--accent)',
    Icon: Scissors,
  },
  {
    title: 'Batch review',
    desc: 'Approve, flag, or mark uncertain across thousands of clips in one grid. Keyboard-friendly. Role-aware.',
    accent: 'var(--success)',
    Icon: Grid3X3,
  },
  {
    title: 'Structured organization',
    desc: 'Generate JSON or CSV manifests, or simply let the system automatically organize your assets into labeled folders, ready for batch download.',
    accent: 'var(--warning)',
    Icon: Download,
  },
  {
    title: 'Role-based access',
    desc: 'Separate upload, review, and admin permissions. Reviewers see what they need. Nothing more.',
    accent: '#a371f7',
    Icon: Shield,
  },
];

const STEPS = [
  { num: '01', label: 'Upload', body: 'Drop any video format. No conversion needed.' },
  { num: '02', label: 'Analyze', body: 'Scene boundaries and tags detected automatically.' },
  { num: '03', label: 'Review', body: 'Visual clip grid. Approve, flag, or skip.' },
  { num: '04', label: 'Download', body: 'Batch download organized videos or structured datasets.' },
];

const TESTIMONIALS = [
  {
    quote: 'Cut our clip-sorting time by 70%. The scene detection is frighteningly accurate.',
    name: 'A. Reza',
    role: 'Post-production Lead',
    hue: 210,
  },
  {
    quote: 'Role-aware review means our clients only see what is relevant. Game changer.',
    name: 'S. Müller',
    role: 'Director, KG Studio',
    hue: 280,
  },
  {
    quote: 'The organized video pipeline saved us an entire editing day on our last project.',
    name: 'J. Park',
    role: 'Freelance Cinematographer',
    hue: 150,
  },
];

const heroFrameAssets = [
  new URL('../../thumbnails/Drone_shot_202512101744_ddeo6/Drone_shot_202512101744_ddeo6_scene_001.jpg', import.meta.url).href,
  new URL('../../thumbnails/eva radu/eva radu_scene_003.jpg', import.meta.url).href,
  new URL('../../thumbnails/WorldLink X KG QA video 3/WorldLink X KG QA video 3_scene_010.jpg', import.meta.url).href,
];

const HERO_FRAMES = [
  { title: 'Interview close-up', tag: 'Human / dialogue', tone: 'rgba(88, 166, 255, 0.75)', image: heroFrameAssets[1] },
  { title: 'Crowd energy', tag: 'Motion / event', tone: 'rgba(210, 153, 34, 0.75)', image: heroFrameAssets[2] },
  { title: 'Product detail', tag: 'Clean / exportable', tone: 'rgba(35, 134, 54, 0.8)', image: heroFrameAssets[0] },
];

/* ─── Particle canvas ─────────────────────────────────────────── */
function ParticleCanvas() {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    const particles = [];
    const N = 56;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < N; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.4 + 0.4,
        dx: (Math.random() - 0.5) * 0.28,
        dy: (Math.random() - 0.5) * 0.28,
        o: Math.random() * 0.5 + 0.15,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(88,166,255,${p.o})`;
        ctx.fill();
      });
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);
  return (
    <canvas
      ref={canvasRef}
      className="hero-particle-canvas"
      aria-hidden="true"
    />
  );
}

/* ─── Capability panel (GSAP cross-fade) ─────────────────────── */
function CapPanel({ cap }) {
  const innerRef = useRef(null);

  useEffect(() => {
    if (!innerRef.current) return;
    gsap.fromTo(
      innerRef.current,
      { opacity: 0, y: -10 },
      { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' },
    );
  }, [cap]);

  return (
    <div className="cap-panel" style={{ '--cap-accent': cap.accent }}>
      <div ref={innerRef} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="cap-panel-icon-wrap">
          <cap.Icon size={28} className="cap-panel-icon" />
          <div className="cap-panel-icon-ring" />
        </div>
        <div className="cap-panel-title">{cap.title}</div>
        <div className="cap-panel-desc">{cap.desc}</div>
        <div className="cap-panel-bar" />
      </div>
    </div>
  );
}

/* ─── Main component ──────────────────────────────────────────── */
export default function Landing() {
  const containerRef = useRef(null);
  const curtainRef = useRef(null);
  const deviceRef = useRef(null);
  const btnLaunchNavRef = useRef(null);
  const [activeCapIdx, setActiveCapIdx] = useState(0);
  const [activeHeroFrame, setActiveHeroFrame] = useState(0);
  const [curtainDone, setCurtainDone] = useState(false);
  const isLoggedIn = !!localStorage.getItem('token');

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── auto-cycle hero frames ── */
  useEffect(() => {
    const id = setInterval(() => {
      setActiveHeroFrame(f => (f + 1) % HERO_FRAMES.length);
    }, 3200);
    return () => clearInterval(id);
  }, []);

  /* ── cursor parallax on device ── */
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

  /* ── magnetic nav CTA ── */
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

  /* ── main GSAP context ── */
  useLayoutEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    lenis.on('scroll', ScrollTrigger.update);
    const tickerRAF = (time) => lenis.raf(time * 1000);
    gsap.ticker.add(tickerRAF);
    gsap.ticker.lagSmoothing(0);

    const nav = containerRef.current?.querySelector('.landing-nav');
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

      /* curtain lift → hero entrance sequence */
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
    }, containerRef);

    return () => {
      gsap.ticker.remove(tickerRAF);
      lenis.destroy();
      window.removeEventListener('scroll', onScroll);
      ctx.revert();
      splitInstances.forEach(s => s.revert());
    };
  }, [prefersReducedMotion]);

  const activeCap = CAPABILITIES[activeCapIdx];

  /* hero frame reorder so active is span-2 */
  const orderedFrames = [
    HERO_FRAMES[activeHeroFrame],
    ...HERO_FRAMES.filter((_, i) => i !== activeHeroFrame),
  ];

  return (
    <div
      className="landing-page"
      ref={containerRef}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
    >
      {/* scroll progress */}
      <div className="scroll-progress" aria-hidden="true" />

      {/* curtain */}
      <div className="landing-curtain" ref={curtainRef} aria-hidden="true" />

      {/* atmosphere */}
      <div className="landing-atmosphere landing-atmosphere-a" aria-hidden="true" />
      <div className="landing-atmosphere landing-atmosphere-b" aria-hidden="true" />
      <div className="landing-atmosphere landing-atmosphere-c" aria-hidden="true" />
      <div className="landing-grid-overlay" aria-hidden="true" />

      {/* ── nav ── */}
      <nav className="landing-nav">
        <div className="landing-container landing-nav-inner">
          <Link to="/" className="landing-logo">EditEase</Link>
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

      {/* ── hero ── */}
      <section className="landing-section hero">
        <div className="landing-container hero-grid">
          <div className="hero-copy">
            <ParticleCanvas />
            <div className="mono-caps fade-up hero-badge">
              <span className="hero-badge-dot" />
              AI-Powered Scene Analysis
            </div>
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

          <div className="hero-visual fade-up" aria-hidden="true">
            <div className="hero-visual-glow" />
            <div className="hero-device" ref={deviceRef}>
              <div className="hero-device-topbar">
                <div className="hero-device-dots">
                  <span className="preview-dot" style={{ background: '#ff5f57' }} />
                  <span className="preview-dot" style={{ background: '#febc2e' }} />
                  <span className="preview-dot" style={{ background: '#28c840' }} />
                </div>
                <div className="hero-device-title">
                  editease / live scene board<span className="typing-cursor">|</span>
                </div>
              </div>
              <div className="hero-device-screen">
                <div className="hero-device-scanline" aria-hidden="true" />
                <div className="hero-device-sidebar">
                  <div className="hero-device-sidebar-mark" />
                  <span className="hero-device-sidebar-line active" />
                  <span className="hero-device-sidebar-line" />
                  <span className="hero-device-sidebar-line" />
                  <span className="hero-device-sidebar-line short" />
                </div>
                <div className="hero-shot-grid">
                  {orderedFrames.map((frame, idx) => (
                    <article
                      key={frame.title}
                      className={`hero-shot-card ${idx === 0 ? 'hero-shot-card-wide' : ''}`}
                      style={{ '--frame-tone': frame.tone, '--frame-image': `url("${frame.image}")` }}
                    >
                      <div className="hero-shot-image" />
                      <div className="hero-shot-overlay" />
                      <div className="hero-shot-meta">
                        <span className="hero-shot-tag">{frame.tag}</span>
                        <strong>{frame.title}</strong>
                      </div>
                    </article>
                  ))}
                </div>
                <div className="hero-timeline">
                  <div className="hero-timeline-track" />
                  <div className="hero-timeline-progress" />
                  <div className="hero-timeline-marker marker-a" />
                  <div className="hero-timeline-marker marker-b" />
                  <div className="hero-timeline-marker marker-c" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── how it works ── */}
      <section className="landing-section" id="how-it-works">
        <div className="landing-container">
          <div className="section-kicker fade-up">
            <div className="mono-caps">How it works</div>
            <p>One pipeline from raw footage to structured review-ready clips.</p>
          </div>
          <div className="steps-progress-bar" />
          <div className="steps-grid">
            {STEPS.map(s => (
              <div key={s.num} className="step-item">
                <div className="step-num">{s.num}</div>
                <div className="step-label">{s.label}</div>
                <div className="step-body">{s.body}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── capabilities ── */}
      <section className="landing-section" id="capabilities">
        <div className="landing-container">
          <div className="section-kicker fade-up">
            <div className="mono-caps">What it does</div>
            <p>Built for teams that need visual intelligence, not a plain upload form.</p>
          </div>
          <div className="capabilities-grid">
            <div className="cap-list">
              {CAPABILITIES.map((cap, idx) => (
                <button
                  key={cap.title}
                  className={`cap-item ${idx === activeCapIdx ? 'active' : ''}`}
                  onMouseEnter={() => setActiveCapIdx(idx)}
                  onClick={() => setActiveCapIdx(idx)}
                  style={{ '--cap-accent': cap.accent }}
                >
                  <cap.Icon size={22} className="cap-icon" />
                  <span className="cap-title">{cap.title}</span>
                </button>
              ))}
            </div>
            <CapPanel cap={activeCap} />
          </div>
        </div>
      </section>

      {/* ── review workspace preview ── */}
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
              <div className="mono-caps" style={{ marginLeft: 'auto', fontSize: '0.6rem' }}>editease / review queue</div>
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

      {/* ── testimonials ── */}
      <section className="landing-section social-proof">
        <div className="landing-container">
          <div className="mono-caps fade-up" style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
            Trusted for real footage workflows
          </div>
          <div className="testimonial-row">
            {TESTIMONIALS.map((t, i) => (
              <div key={i} className="testimonial-card fade-up">
                <div className="testimonial-stars" aria-label="5 stars">
                  {Array.from({ length: 5 }).map((_, s) => (
                    <span key={s} className="testimonial-star">★</span>
                  ))}
                </div>
                <p className="testimonial-quote">"{t.quote}"</p>
                <div className="testimonial-author">
                  <div
                    className="testimonial-avatar"
                    style={{ background: `linear-gradient(135deg, hsl(${t.hue},60%,22%), hsl(${t.hue + 30},60%,14%))` }}
                  >
                    <span>{t.name[0]}</span>
                  </div>
                  <div>
                    <div className="testimonial-name">{t.name}</div>
                    <div className="testimonial-role">{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── marquee ── */}
      <section className="marquee-wrapper" aria-hidden="true">
        <div className="marquee-track">
          <span className="marquee-content">
            SCENE DETECTION · BATCH REVIEW · AUTO-ORGANIZE · EMOTION TAGS · EXPORT PIPELINE · ROLE ACCESS ·&nbsp;
          </span>
          <span className="marquee-content" aria-hidden="true">
            SCENE DETECTION · BATCH REVIEW · AUTO-ORGANIZE · EMOTION TAGS · EXPORT PIPELINE · ROLE ACCESS ·&nbsp;
          </span>
        </div>
      </section>

      {/* ── footer ── */}
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
          <div className="footer-meta">
            <div className="mono-caps" style={{ marginBottom: 8 }}>System Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--success)', fontWeight: 600, fontSize: '0.875rem' }}>
              <span className="pulse-dot" style={{ background: 'var(--success)' }} />
              Online
            </div>
            <div className="mono-caps" style={{ marginTop: 24, color: 'var(--text-muted)' }}>
              © {new Date().getFullYear()} EditEase
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
