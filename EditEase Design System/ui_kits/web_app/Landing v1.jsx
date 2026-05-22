/* global React */
const Landing = () => (
  <div className="landing">
    <div className="atmosphere a"/><div className="atmosphere b"/><div className="atmosphere c"/>
    <div className="grid-overlay"/>

    <nav className="lp-nav">
      <a href="#" className="lp-logo">EditEase</a>
      <div className="lp-links">
        <a href="#" className="lp-nav-link">How it works</a>
        <a href="#" className="lp-nav-link">Capabilities</a>
        <a href="#" className="btn-launch">Get Started →</a>
      </div>
    </nav>

    <section className="hero">
      <div className="hero-grid">
        <div className="hero-copy">
          <div className="hero-badge mono-caps"><span className="hero-dot"/> AI-Powered Scene Analysis</div>
          <h1 className="display-h1">Stop sorting<br/>footage manually.</h1>
          <p className="body-large">Upload your videos. EditEase detects every scene, analyzes emotion, and gives you a review workspace in minutes.</p>
          <div className="hero-actions">
            <a href="#" className="btn-launch lg">Get Started →</a>
            <a href="#" className="btn-ghost">See how it works ↓</a>
          </div>
          <div className="hero-metrics">
            <div className="hero-metric"><b>4-step</b><em>workflow from ingest to export</em></div>
            <div className="hero-metric"><b>Role-aware</b><em>review, admin, editor surfaces</em></div>
            <div className="hero-metric"><b>Visual</b><em>clip-first moderation w/ context</em></div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-glow"/>
          <div className="hero-device">
            <div className="hero-bar">
              <span className="dot" style={{background:'#ff5f57'}}/><span className="dot" style={{background:'#febc2e'}}/><span className="dot" style={{background:'#28c840'}}/>
              <span className="hero-bar-title">editease / live scene board</span>
            </div>
            <div className="hero-screen">
              <div className="hero-sb"><span/><span className="ln active"/><span className="ln"/><span className="ln"/><span className="ln short"/></div>
              <div className="hero-shots">
                <div className="shot wide" style={{'--tone':'rgba(88,166,255,.75)','--bg':'#1a2c1a'}}><span className="shot-tag">Human / dialogue</span><strong>Interview close-up</strong></div>
                <div className="shot" style={{'--tone':'rgba(210,153,34,.75)','--bg':'#2c2419'}}><span className="shot-tag">Motion / event</span><strong>Crowd energy</strong></div>
                <div className="shot" style={{'--tone':'rgba(35,134,54,.8)','--bg':'#1a2030'}}><span className="shot-tag">Clean / exportable</span><strong>Product detail</strong></div>
              </div>
              <div className="hero-tl"><div className="tl-track"/><div className="tl-prog"/><span className="tl-mk a"/><span className="tl-mk b"/><span className="tl-mk c"/></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section className="lp-section">
      <div className="kicker"><div className="mono-caps">How it works</div><p>One pipeline from raw footage to structured review-ready clips.</p></div>
      <div className="steps">
        {[['01','Upload','Drop any video format. No conversion needed.'],
          ['02','Analyze','Scene boundaries and tags detected automatically.'],
          ['03','Review','Visual clip grid. Approve, flag, or skip.'],
          ['04','Download','Batch download organized videos or structured datasets.']].map(s=>(
          <div key={s[0]} className="step"><div className="step-num">{s[0]}</div><div className="step-label">{s[1]}</div><div className="step-body">{s[2]}</div></div>
        ))}
      </div>
    </section>

    <section className="marquee" aria-hidden="true">
      <div className="marquee-track">
        <span>SCENE DETECTION · BATCH REVIEW · AUTO-ORGANIZE · EMOTION TAGS · EXPORT PIPELINE · ROLE ACCESS · </span>
        <span>SCENE DETECTION · BATCH REVIEW · AUTO-ORGANIZE · EMOTION TAGS · EXPORT PIPELINE · ROLE ACCESS · </span>
      </div>
    </section>
  </div>
);

window.Landing = Landing;
