/* global React */
const { useEffect, useLayoutEffect, useRef, useState, useCallback } = React;

/* ──────────────────────────────────────────────────────────────
   Hooks
   ────────────────────────────────────────────────────────────── */

/** Damped mouse tracker. Returns a ref-attached element + a setter that
 *  applies the lerped offset (-1..1) to CSS variables on it each frame. */
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
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      // Use viewport so the diorama keeps responding even when cursor is outside it
      target.current.x = ((e.clientX - cx) / (window.innerWidth / 2)) * strength;
      target.current.y = ((e.clientY - cy) / (window.innerHeight / 2)) * strength;
    };
    const tick = () => {
      const k = 0.08; // ease toward target
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

/** Reveal-on-scroll: adds .in once intersected. */
function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('[data-reveal]');
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.18 });
    els.forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);
}

/** Continuous oscillation: writes sin/cos to a ref's CSS vars. */
function useIdleDrift(ref, period = 8000, amp = 1) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf, t0 = performance.now();
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

/** Hero text: split spans on first render so CSS can stagger them. */
function SplitText({ as: Tag = 'h1', text, className = '', delay = 0 }) {
  const lines = text.split('\n');
  let charIndex = 0;
  return (
    <Tag className={`split ${className}`} style={{ '--split-delay': `${delay}ms` }}>
      {lines.map((line, li) => (
        <span className="split-line" key={li}>
          {line.split(' ').map((word, wi, words) => (
            <React.Fragment key={wi}>
              <span className="split-word">
                {[...word].map((ch, ci) => {
                  const i = charIndex++;
                  return (
                    <span className="split-ch" key={ci} style={{ '--i': i }}>{ch}</span>
                  );
                })}
              </span>
              {wi < words.length - 1 && <span className="split-space">{'\u00A0'}</span>}
            </React.Fragment>
          ))}
        </span>
      ))}
    </Tag>
  );
}

/* ──────────────────────────────────────────────────────────────
   3D Editor Diorama — the centerpiece
   ────────────────────────────────────────────────────────────── */

const HeroDiorama = () => {
  const stageRef = useMouseTilt(1);
  const idleRef = useRef(null);
  useIdleDrift(idleRef, 9000, 1);

  return (
    <div className="diorama" ref={stageRef}>
      {/* mouse-following spotlight on the diorama plane */}
      <div className="diorama-spot" />

      {/* the 3D stack */}
      <div className="diorama-stage" ref={idleRef}>
        {/* back: shadow plane that catches light */}
        <div className="layer plane-shadow" />

        {/* sidebar floating left */}
        <div className="layer plane-sidebar">
          <div className="ds-rail">
            <div className="ds-rail-dot active" />
            <div className="ds-rail-dot" />
            <div className="ds-rail-dot" />
            <div className="ds-rail-dot" />
          </div>
          <div className="ds-list">
            <div className="ds-row active"><i /><span/></div>
            <div className="ds-row"><i /><span/></div>
            <div className="ds-row"><i /><span/></div>
            <div className="ds-row"><i /><span/></div>
            <div className="ds-row short"><i /><span/></div>
          </div>
        </div>

        {/* main canvas */}
        <div className="layer plane-canvas">
          <div className="dc-bar">
            <span className="dc-dot r"/><span className="dc-dot y"/><span className="dc-dot g"/>
            <span className="dc-title">editease / scene-board · take 04</span>
            <span className="dc-rec"><span/>REC</span>
          </div>
          <div className="dc-grid">
            <div className="dc-shot wide">
              <div className="dc-thumb tone-blue">
                <div className="dc-scan" />
                <div className="dc-noise" />
              </div>
              <div className="dc-meta">
                <span className="dc-tag tag-blue">DIALOGUE · 0:42</span>
                <strong>Interview close-up</strong>
              </div>
            </div>
            <div className="dc-shot">
              <div className="dc-thumb tone-amber"><div className="dc-scan d2"/></div>
              <div className="dc-meta">
                <span className="dc-tag tag-amber">MOTION · 0:18</span>
                <strong>Crowd energy</strong>
              </div>
            </div>
            <div className="dc-shot">
              <div className="dc-thumb tone-green"><div className="dc-scan d3"/></div>
              <div className="dc-meta">
                <span className="dc-tag tag-green">PRODUCT · 0:09</span>
                <strong>Detail shot</strong>
              </div>
            </div>
          </div>
        </div>

        {/* timeline floats forward */}
        <div className="layer plane-timeline">
          <div className="tl-head">
            <span className="tl-time">00:00:42:18</span>
            <div className="tl-controls">
              <span/><span className="play"/><span/>
            </div>
            <span className="tl-rate">24 FPS</span>
          </div>
          <div className="tl-tracks">
            <div className="tl-track">
              <div className="tl-clip a"/><div className="tl-clip b"/><div className="tl-clip c"/>
            </div>
            <div className="tl-track sub">
              <div className="tl-clip d"/><div className="tl-clip e"/>
            </div>
          </div>
          <div className="tl-playhead" />
        </div>

        {/* floating tag badges in front */}
        <div className="layer plane-tags">
          <div className="float-tag tag-blue">
            <span className="tag-dot"/>
            <div><b>+ Speaker tag</b><em>auto-detected</em></div>
          </div>
          <div className="float-tag tag-purple">
            <span className="tag-dot"/>
            <div><b>4 emotions</b><em>warmth · focus · joy · calm</em></div>
          </div>
          <div className="float-tag tag-green">
            <span className="tag-dot"/>
            <div><b>Approved</b><em>ready for export</em></div>
          </div>
        </div>

        {/* film reel orbiting at top right */}
        <div className="layer plane-reel">
          <FilmReel size={140} />
        </div>
      </div>

      {/* ground reflection */}
      <div className="diorama-floor" />
    </div>
  );
};

/* SVG film reel — continuously rotates */
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
          <ellipse cx="50" cy="22" rx="9" ry="6" fill="rgba(13,17,23,.95)" stroke="rgba(255,255,255,.08)"/>
        </g>
      ))}
      <circle cx="50" cy="50" r="6" fill="#58a6ff" stroke="rgba(255,255,255,.15)"/>
    </g>
  </svg>
);

/* ──────────────────────────────────────────────────────────────
   Steps — scroll reveal with 3D rotateY entry
   ────────────────────────────────────────────────────────────── */

const STEPS = [
  ['01', 'Upload', 'Drop any video format. No conversion. We chunk and stream straight to the analyzer.'],
  ['02', 'Analyze', 'Scene boundaries, emotion, and motion tags detected automatically with timecodes.'],
  ['03', 'Review', 'Visual clip-grid moderation. Approve, flag, or skip with one keystroke.'],
  ['04', 'Export', 'Batch download organized clips, datasets, or push direct to your NLE.'],
];

const StepCard = ({ s, i }) => (
  <div className="lp2-step" data-reveal style={{ '--rd': `${i * 90}ms` }}>
    <div className="lp2-step-num">{s[0]}</div>
    <div className="lp2-step-label">{s[1]}</div>
    <div className="lp2-step-body">{s[2]}</div>
    <div className="lp2-step-bar"><div/></div>
  </div>
);

/* ──────────────────────────────────────────────────────────────
   Capability cards — hover 3D tilt
   ────────────────────────────────────────────────────────────── */

const CAPS = [
  { kicker: 'Vision', title: 'Scene-aware indexing', body: 'Every shot fingerprinted with composition, motion, and color tags.', accent: 'blue' },
  { kicker: 'Pipeline', title: '4-step ingest to export', body: 'A single rail from raw upload to dataset, organized clips, or NLE handoff.', accent: 'purple' },
  { kicker: 'Roles', title: 'Reviewer, editor, admin', body: 'Surface only what each role needs. Bulk-approve or moderate visually.', accent: 'green' },
];

const CapCard = ({ c, i }) => {
  const ref = useRef(null);
  const onMove = useCallback((e) => {
    const el = ref.current; if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--cx', (((e.clientX - r.left) / r.width) - 0.5).toFixed(3));
    el.style.setProperty('--cy', (((e.clientY - r.top) / r.height) - 0.5).toFixed(3));
  }, []);
  const onLeave = useCallback(() => {
    const el = ref.current; if (!el) return;
    el.style.setProperty('--cx', 0); el.style.setProperty('--cy', 0);
  }, []);
  return (
    <div ref={ref} className={`lp2-cap accent-${c.accent}`} onMouseMove={onMove} onMouseLeave={onLeave}
         data-reveal style={{ '--rd': `${i * 90}ms` }}>
      <div className="lp2-cap-glow" />
      <div className="lp2-cap-kicker mono-caps">{c.kicker}</div>
      <h3 className="lp2-cap-title">{c.title}</h3>
      <p className="lp2-cap-body">{c.body}</p>
      <div className="lp2-cap-arrow">→</div>
    </div>
  );
};

/* ──────────────────────────────────────────────────────────────
   Main Landing
   ────────────────────────────────────────────────────────────── */

const Landing = () => {
  useReveal();

  // global mouse spotlight on the page background
  const pageRef = useRef(null);
  useEffect(() => {
    const el = pageRef.current; if (!el) return;
    const onMove = (e) => {
      el.style.setProperty('--gx', `${e.clientX}px`);
      el.style.setProperty('--gy', `${e.clientY}px`);
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  // scroll progress -> hero scene rotates slightly as you scroll past
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        setScrollY(window.scrollY);
        ticking = false;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="lp2" ref={pageRef} style={{ '--scroll': scrollY }}>
      {/* atmosphere — drifts and reacts to mouse */}
      <div className="lp2-atmos a"/><div className="lp2-atmos b"/><div className="lp2-atmos c"/>
      <div className="lp2-grid" />
      <div className="lp2-spot" />
      <div className="lp2-grain" />

      <nav className="lp2-nav">
        <a href="#" className="lp2-logo">
          <span className="lp2-logo-mark">
            <span/><span/><span/>
          </span>
          <span>EditEase</span>
        </a>
        <div className="lp2-links">
          <a href="#how" className="lp2-link">How it works</a>
          <a href="#caps" className="lp2-link">Capabilities</a>
          <a href="#" className="lp2-link">Docs</a>
          <a href="#" className="lp2-cta">Get started <span aria-hidden="true">→</span></a>
        </div>
      </nav>

      {/* HERO */}
      <section className="lp2-hero">
        <div className="lp2-hero-grid">
          <div className="lp2-hero-copy">
            <div className="lp2-badge"><span className="lp2-badge-dot"/> AI-Powered Scene Analysis</div>
            <SplitText as="h1" text={"Stop sorting\nfootage manually."} className="lp2-h1" />
            <p className="lp2-lede" data-reveal>
              Upload your videos. EditEase detects every scene, tags emotion and motion,
              and hands you a review workspace in minutes — not days.
            </p>
            <div className="lp2-actions" data-reveal style={{ '--rd': '120ms' }}>
              <a href="#" className="lp2-cta lg">Get started <span aria-hidden="true">→</span></a>
              <a href="#how" className="lp2-cta-ghost">See how it works <span aria-hidden="true">↓</span></a>
            </div>
            <div className="lp2-metrics" data-reveal style={{ '--rd': '180ms' }}>
              <div><b>4-step</b><em>ingest → analyze → review → export</em></div>
              <div><b>Role-aware</b><em>reviewer · editor · admin surfaces</em></div>
              <div><b>Visual</b><em>clip-first moderation w/ keyboard nav</em></div>
            </div>
          </div>

          <div className="lp2-hero-stage"
               style={{ '--scroll-tilt': `${Math.min(scrollY * 0.04, 12)}deg` }}>
            <HeroDiorama />
          </div>
        </div>

        <div className="lp2-hero-foot mono-caps" data-reveal>
          <span>Live demo · scroll to explore</span>
          <span className="lp2-hero-arrow">↓</span>
        </div>
      </section>

      {/* MARQUEE */}
      <div className="lp2-marquee" aria-hidden="true">
        <div className="lp2-marquee-track">
          {[...Array(4)].map((_, i) => (
            <span key={i}>
              SCENE DETECTION · BATCH REVIEW · AUTO-ORGANIZE · EMOTION TAGS · EXPORT PIPELINE · ROLE ACCESS · 
            </span>
          ))}
        </div>
      </div>

      {/* HOW IT WORKS */}
      <section className="lp2-section" id="how">
        <div className="lp2-kicker" data-reveal>
          <div className="mono-caps">How it works</div>
          <h2 className="lp2-h2">One pipeline from raw footage<br/>to structured, review-ready clips.</h2>
        </div>
        <div className="lp2-steps">
          {STEPS.map((s, i) => <StepCard key={s[0]} s={s} i={i} />)}
        </div>
      </section>

      {/* CAPABILITIES */}
      <section className="lp2-section" id="caps">
        <div className="lp2-kicker" data-reveal>
          <div className="mono-caps">Capabilities</div>
          <h2 className="lp2-h2">Built for teams that<br/>move on tight schedules.</h2>
        </div>
        <div className="lp2-caps">
          {CAPS.map((c, i) => <CapCard key={c.title} c={c} i={i} />)}
        </div>
      </section>

      {/* CTA */}
      <section className="lp2-cta-band" data-reveal>
        <div className="lp2-cta-glow" />
        <SplitText as="h2" text={"Your edit suite,\nbut faster."} className="lp2-cta-h" />
        <a href="#" className="lp2-cta lg">Start free · 14 days <span aria-hidden="true">→</span></a>
        <div className="lp2-cta-foot mono-caps">No card required · 5 GB included</div>
      </section>

      <footer className="lp2-foot">
        <span className="lp2-logo">
          <span className="lp2-logo-mark"><span/><span/><span/></span>
          EditEase
        </span>
        <span className="mono-caps">© 2026 · Built for post-production teams</span>
      </footer>
    </div>
  );
};

window.Landing = Landing;
