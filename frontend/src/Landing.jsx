import React, { useLayoutEffect, useRef, useState } from 'react';
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
    title: 'Structured exports',
    desc: 'Generate JSON or CSV manifests that map clips to scenes and tags. Ingest directly into your NLE or training pipeline.',
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
  { num: '04', label: 'Export', body: 'Structured manifest ready for your NLE or dataset.' },
];

const heroFrameAssets = [
  new URL('../../thumbnails/Drone_shot_202512101744_ddeo6/Drone_shot_202512101744_ddeo6_scene_001.jpg', import.meta.url).href,
  new URL('../../thumbnails/eva radu/eva radu_scene_003.jpg', import.meta.url).href,
  new URL('../../thumbnails/WorldLink X KG QA video 3/WorldLink X KG QA video 3_scene_010.jpg', import.meta.url).href,
];

const HERO_FRAMES = [
  {
    title: 'Interview close-up',
    tag: 'Human / dialogue',
    tone: 'rgba(88, 166, 255, 0.75)',
    image: heroFrameAssets[1],
  },
  {
    title: 'Crowd energy',
    tag: 'Motion / event',
    tone: 'rgba(210, 153, 34, 0.75)',
    image: heroFrameAssets[2],
  },
  {
    title: 'Product detail',
    tag: 'Clean / exportable',
    tone: 'rgba(35, 134, 54, 0.8)',
    image: heroFrameAssets[0],
  },
];

export default function Landing() {
  const containerRef = useRef(null);
  const [activeCapIdx, setActiveCapIdx] = useState(0);
  const isLoggedIn = !!localStorage.getItem('token');

  useLayoutEffect(() => {
    let rafId;
    const lenis = new Lenis({
      duration: 1.2,
      easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    function raf(time) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    const nav = containerRef.current?.querySelector('.landing-nav');
    const onScroll = () => nav?.classList.toggle('scrolled', window.scrollY > 60);
    window.addEventListener('scroll', onScroll, { passive: true });

    const ctx = gsap.context(() => {
      document.querySelectorAll('.split-reveal').forEach(target => {
        const st = new SplitType(target, { types: 'lines' });
        st.lines.forEach(line => {
          const wrap = document.createElement('div');
          wrap.style.cssText = 'overflow:hidden;display:block;';
          line.parentNode.insertBefore(wrap, line);
          wrap.appendChild(line);
        });
        gsap.from(st.lines, {
          yPercent: 110,
          opacity: 0,
          stagger: 0.08,
          duration: 0.85,
          ease: 'power3.out',
        });
      });

      gsap.utils.toArray('.fade-up').forEach(el => {
        gsap.from(el, {
          y: 28,
          opacity: 0,
          duration: 0.75,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 90%' },
        });
      });

      gsap.utils.toArray('.step-item').forEach((el, i) => {
        gsap.from(el, {
          y: 20,
          opacity: 0,
          duration: 0.6,
          ease: 'power2.out',
          delay: i * 0.09,
          scrollTrigger: { trigger: el, start: 'top 88%' },
        });
      });
    }, containerRef);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
      window.removeEventListener('scroll', onScroll);
      ctx.revert();
    };
  }, []);

  const activeCap = CAPABILITIES[activeCapIdx];

  return (
    <div className="landing-page" ref={containerRef}>
      <div className="landing-atmosphere landing-atmosphere-a" aria-hidden="true" />
      <div className="landing-atmosphere landing-atmosphere-b" aria-hidden="true" />
      <div className="landing-grid-overlay" aria-hidden="true" />

      <nav className="landing-nav">
        <div className="landing-container landing-nav-inner">
          <Link to="/" className="landing-logo">EditEase</Link>
          <div className="landing-links">
            <a href="#how-it-works" className="landing-nav-link">How it works</a>
            <a href="#capabilities" className="landing-nav-link">Capabilities</a>
            <Link to={isLoggedIn ? '/app/dashboard' : '/login'} className="btn-launch">
              {isLoggedIn ? 'Open Workspace ->' : 'Get Started ->'}
            </Link>
          </div>
        </div>
      </nav>

      <section className="landing-section hero">
        <div className="landing-container hero-grid">
          <div className="hero-copy">
            <div className="mono-caps fade-up" style={{ marginBottom: '1.5rem' }}>
              AI-Powered Scene Analysis
            </div>
            <h1 className="display-h1 split-reveal" style={{ marginBottom: '2rem' }}>
              Stop sorting
              <br />
              footage manually.
            </h1>
            <p className="body-large fade-up hero-lead">
              Upload your videos. EditEase detects every scene, analyzes emotion,
              and gives you a review workspace in minutes.
            </p>
            <div className="fade-up hero-actions">
              <Link to={isLoggedIn ? '/app/dashboard' : '/login'} className="btn-launch">
                {isLoggedIn ? 'Open Workspace ->' : 'Get Started ->'}
              </Link>
              <a href="#how-it-works" className="btn-ghost">See how it works -></a>
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
            <div className="hero-device">
              <div className="hero-device-topbar">
                <div className="hero-device-dots">
                  <span className="preview-dot" style={{ background: '#ff5f57' }} />
                  <span className="preview-dot" style={{ background: '#febc2e' }} />
                  <span className="preview-dot" style={{ background: '#28c840' }} />
                </div>
                <div className="hero-device-title">editease / live scene board</div>
              </div>
              <div className="hero-device-screen">
                <div className="hero-device-sidebar">
                  <div className="hero-device-sidebar-mark" />
                  <span className="hero-device-sidebar-line active" />
                  <span className="hero-device-sidebar-line" />
                  <span className="hero-device-sidebar-line" />
                  <span className="hero-device-sidebar-line short" />
                </div>
                <div className="hero-shot-grid">
                  {HERO_FRAMES.map((frame, idx) => (
                    <article
                      key={frame.title}
                      className={`hero-shot-card hero-shot-card-${idx + 1}`}
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

      <section className="landing-section" id="how-it-works">
        <div className="landing-container">
          <div className="section-kicker fade-up">
            <div className="mono-caps">How it works</div>
            <p>One pipeline from raw footage to structured review-ready clips.</p>
          </div>
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

            <div className="cap-panel" style={{ '--cap-accent': activeCap.accent }}>
              <activeCap.Icon size={28} className="cap-panel-icon" />
              <div className="cap-panel-title">{activeCap.title}</div>
              <div className="cap-panel-desc">{activeCap.desc}</div>
              <div className="cap-panel-bar" />
            </div>
          </div>
        </div>
      </section>

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
                {['Dashboard', 'Review Queue', 'Uploads', 'Exports'].map((item, i) => (
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

      <footer className="landing-section landing-footer fade-up">
        <div className="landing-container landing-footer-inner">
          <div>
            <h2 className="display-h2" style={{ marginBottom: '1.5rem' }}>
              Stop sorting manually.
            </h2>
            <Link to={isLoggedIn ? '/app/dashboard' : '/login'} className="btn-launch" style={{ fontSize: '1rem', padding: '14px 28px' }}>
              {isLoggedIn ? 'Open Workspace ->' : 'Get Started ->'}
            </Link>
          </div>
          <div className="footer-meta">
            <div className="mono-caps" style={{ marginBottom: 8 }}>System Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--success)', fontWeight: 600, fontSize: '0.875rem' }}>
              <span className="pulse-dot" style={{ background: 'var(--success)' }} /> Online
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
