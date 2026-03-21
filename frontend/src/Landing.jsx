import React, { useEffect, useRef, useState, useLayoutEffect } from 'react';
import { Link } from 'react-router-dom';
import { Wand2, Play, Grid, Zap, Scissors, Shield } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import SplitType from 'split-type';
import Lenis from 'lenis';
import './landing.css';

gsap.registerPlugin(ScrollTrigger);

export default function Landing() {
  const containerRef = useRef(null);
  const [activeCapability, setActiveCapability] = useState(0);

  const capabilities = [
    { title: 'Scene-aware segmentation', icon: Scissors, desc: 'Automatically splice continuous footage into distinct, reviewable scenes based on visual cuts.', previewColor: 'var(--accent)' },
    { title: 'Dataset Review Workflow', icon: Grid, desc: 'Batch-edit tags, flags, and emotional metadata. Built for handling thousands of clips without clicking into each one.', previewColor: 'var(--success)' },
    { title: 'Structured Exports', icon: Zap, desc: 'Generate manifest files mapping clips to transcripts. Ready for your NLE or dataset training.', previewColor: 'var(--warning)' },
    { title: 'Role-based Access', icon: Shield, desc: 'Isolate reviewer decisions from editor actions. Control who uploads, who tags, and who exports.', previewColor: 'var(--danger)' }
  ];

  useLayoutEffect(() => {
    // 1. Scoped Smooth Scroll (Lenis)
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 1,
    });
    
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    const rafId = requestAnimationFrame(raf);

    // 2. GSAP Text Reveals
    const ctx = gsap.context(() => {
      // Split display text into lines
      const splitTargets = document.querySelectorAll('.split-reveal');
      splitTargets.forEach((target) => {
        const text = new SplitType(target, { types: 'lines' });
        
        // Wrap each line in an overflow:hidden mask
        text.lines.forEach(line => {
          const wrapper = document.createElement('div');
          wrapper.style.overflow = 'hidden';
          wrapper.style.display = 'inline-block';
          wrapper.style.verticalAlign = 'bottom';
          line.parentNode.insertBefore(wrapper, line);
          wrapper.appendChild(line);
        });

        // ScrollTrigger animation
        gsap.from(text.lines, {
          yPercent: 120,
          opacity: 0,
          stagger: 0.1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: target,
            start: 'top 85%',
          }
        });
      });

      // Quick fade up for simple elements
      const fadeTargets = gsap.utils.toArray('.fade-up');
      fadeTargets.forEach((target) => {
        gsap.from(target, {
          y: 30,
          opacity: 0,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: target,
            start: 'top 90%',
          }
        });
      });
    }, containerRef); // Scope selections to this container

    return () => {
      // Cleanup on unmount to prevent bleeding into AppShell
      cancelAnimationFrame(rafId);
      lenis.destroy();
      ctx.revert();
    };
  }, []);

  return (
    <div className="landing-page" ref={containerRef}>
      
      {/* ── Navigation ── */}
      <nav className="landing-nav">
        <div className="landing-container landing-nav-inner">
          <Link to="/" className="landing-logo">
            <Wand2 size={24} color="var(--accent)" />
            <span>EditEase</span>
          </Link>
          <div className="landing-links">
            <a href="#features" className="landing-nav-link link-draw" style={{ display: 'none' /* hidden on mobile, handle later */ }}>Features</a>
            <a href="#workflow" className="landing-nav-link link-draw" style={{ display: 'none' }}>Workflow</a>
            <Link to="/app/dashboard" className="btn-launch">
              Launch App <Play size={14} fill="currentColor" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero Section ── */}
      <section className="landing-section hero">
        <div className="landing-container" style={{ position: 'relative', zIndex: 10 }}>
          <div className="mono-caps fade-up" style={{ marginBottom: 'var(--space-24)' }}>[ System Version: 1.0.0 — Montreal, QC ]</div>
          <h1 className="display-h1 split-reveal" style={{ marginBottom: 'var(--space-32)' }}>
            EditEase brings structure<br/>to raw footage.
          </h1>
          <p className="body-large fade-up" style={{ maxWidth: '600px', marginBottom: 'var(--space-48)', animationDelay: '0.2s' }}>
            Upload clips, detect scenes, review faster, and export with less manual sorting. A cinematic workspace for professional video teams.
          </p>
          <div className="fade-up" style={{ display: 'flex', gap: 'var(--space-16)', animationDelay: '0.3s' }}>
            <Link to="/app/dashboard" className="btn btn-primary" style={{ padding: 'var(--space-16) var(--space-32)', fontSize: '1rem' }}>
              Open Workspace
            </Link>
          </div>
        </div>
      </section>

      {/* ── Workspace Preview (Act II) ── */}
      <section className="landing-section fade-up" style={{ paddingTop: 0 }}>
        <div className="landing-container">
          <div className="preview-window">
            <div className="preview-header">
              <div className="preview-dot" style={{ background: 'var(--danger)' }}></div>
              <div className="preview-dot" style={{ background: 'var(--warning)' }}></div>
              <div className="preview-dot" style={{ background: 'var(--success)' }}></div>
              <div className="mono-caps" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>app.editease.com/review</div>
            </div>
            {/* We'll use a mocked CSS layout representing the app shell, or later an image. For now, a stylized wireframe block */}
            <div className="preview-body" style={{ display: 'flex' }}>
              <div style={{ width: '240px', borderRight: '1px solid var(--border-subtle)', padding: 'var(--space-24)' }}>
                <div style={{ width: '80%', height: '24px', background: 'var(--surface-elevated)', borderRadius: '4px', marginBottom: 'var(--space-32)' }}></div>
                <div style={{ width: '100%', height: '16px', background: 'var(--surface-elevated)', borderRadius: '4px', marginBottom: 'var(--space-16)', opacity: 0.5 }}></div>
                <div style={{ width: '90%', height: '16px', background: 'var(--surface-elevated)', borderRadius: '4px', marginBottom: 'var(--space-16)', opacity: 0.5 }}></div>
                <div style={{ width: '95%', height: '16px', background: 'var(--surface-elevated)', borderRadius: '4px', marginBottom: 'var(--space-16)', opacity: 0.5 }}></div>
              </div>
              <div style={{ flex: 1, padding: 'var(--space-40)', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-16)' }}>
                 {/* Fake clip cards */}
                 {[1,2,3,4,5,6].map(i => (
                    <div key={i} style={{ aspectRatio: '16/9', background: 'var(--surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}></div>
                 ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Marquee ── */}
      <section className="marquee-wrapper">
         <div className="marquee-content">
            INTERVIEWS · TESTIMONIALS · PODCASTS · COURSES · TALKING-HEAD VIDEOS · DOCUMENTARY SELECTS · BATCH EXPORTS · 
            INTERVIEWS · TESTIMONIALS · PODCASTS · COURSES · TALKING-HEAD VIDEOS · DOCUMENTARY SELECTS · BATCH EXPORTS · 
         </div>
      </section>

      {/* ── Workflow & Capabilities ── */}
      <section className="landing-section" id="capabilities">
        <div className="landing-container">
           <div className="mono-caps fade-up" style={{ marginBottom: 'var(--space-40)' }}>[ Core Capabilities ]</div>
           
           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-64)' }}>
             {/* Left List */}
             <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }} className="fade-up">
               {capabilities.map((item, idx) => (
                  <div 
                    key={idx} 
                    onMouseEnter={() => setActiveCapability(idx)}
                    style={{ 
                      display: 'flex', flexDirection: 'column', gap: 'var(--space-12)',
                      padding: 'var(--space-32) 0',
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      opacity: activeCapability === idx ? 1 : 0.4,
                      transition: 'opacity 0.3s ease'
                    }}>
                    <h3 className="display-h3" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-16)' }}>
                      <item.icon size={32} color={activeCapability === idx ? "var(--accent)" : "currentColor"} style={{ transition: 'color 0.3s' }} />
                      {item.title}
                    </h3>
                  </div>
               ))}
             </div>
             
             {/* Right Pinned Preview */}
             <div className="fade-up" style={{ position: 'sticky', top: 'var(--space-64)', height: '400px', display: 'flex', alignItems: 'center' }}>
               <div style={{ 
                 width: '100%', height: '100%', 
                 background: 'var(--surface-elevated)', 
                 borderRadius: 'var(--radius-lg)',
                 border: '1px solid var(--border-subtle)',
                 display: 'flex', flexDirection: 'column',
                 overflow: 'hidden',
                 boxShadow: `0 0 80px ${capabilities[activeCapability].previewColor}22`,
                 transition: 'box-shadow 0.5s ease'
               }}>
                 <div style={{ padding: 'var(--space-24)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600 }}>{capabilities[activeCapability].title}</div>
                 </div>
                 <div style={{ padding: 'var(--space-24)', color: 'var(--text-secondary)', lineHeight: 1.6, flex: 1 }}>
                    {capabilities[activeCapability].desc}
                 </div>
                 {/* Fake abstract visual block representing capability */}
                 <div style={{ height: '40%', background: `linear-gradient(to right, transparent, ${capabilities[activeCapability].previewColor}22)`, borderTop: `1px solid ${capabilities[activeCapability].previewColor}44` }}></div>
               </div>
             </div>
           </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-section fade-up" style={{ borderTop: '1px solid var(--border-strong)', paddingBottom: 'var(--space-64)', paddingTop: 'var(--space-64)' }}>
        <div className="landing-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 'var(--space-32)' }}>
          <div>
            <h2 className="display-h2" style={{ marginBottom: 'var(--space-24)' }}>Ready to sort.</h2>
            <Link to="/app/dashboard" className="btn btn-primary" style={{ padding: 'var(--space-16) var(--space-32)', fontSize: '1rem' }}>
              Sign In To Workspace
            </Link>
          </div>
          
          <div style={{ textAlign: 'right' }}>
            <div className="mono-caps" style={{ marginBottom: 'var(--space-8)' }}>System Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)', justifyContent: 'flex-end', color: 'var(--success)', fontWeight: 600 }}>
               <span className="pulse-dot" style={{ background: 'var(--success)' }}></span> Online
            </div>
            <div className="mono-caps" style={{ marginTop: 'var(--space-24)', color: 'var(--text-muted)' }}>
              © {new Date().getFullYear()} EditEase
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
