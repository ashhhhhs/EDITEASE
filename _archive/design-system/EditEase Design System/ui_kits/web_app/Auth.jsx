/* global React */
const Auth = ({ onSignIn }) => (
  <div className="auth-shell">
    <div className="atmosphere a"/><div className="atmosphere b"/>
    <div className="auth-split">
      <div className="auth-aside">
        <div className="auth-logo">
          <span className="ws-logo-mark"><Icon name="wand" size={18} color="#58a6ff"/></span>
          <b>EditEase</b>
        </div>
        <h2 className="auth-headline">Stop sorting footage manually.</h2>
        <p className="auth-lede">A clip-first review workspace for editors, reviewers, and post-production teams.</p>
        <div className="auth-bullets">
          <div><Icon name="scissors" size={16} color="#58a6ff"/> Scene detection</div>
          <div><Icon name="grid" size={16} color="#3fb950"/> Batch review</div>
          <div><Icon name="shield" size={16} color="#a371f7"/> Role-based access</div>
        </div>
      </div>
      <div className="auth-card">
        <div className="auth-eyebrow mono-caps">Sign in</div>
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-sub">Pick up where you left off in the review queue.</p>
        <div className="field"><label>Email</label><input defaultValue="ash@editease.dev"/></div>
        <div className="field"><label>Password</label><input type="password" defaultValue="••••••••"/></div>
        <div className="field-row"><label className="checky"><input type="checkbox" defaultChecked/> Remember me</label><a href="#" className="link">Forgot?</a></div>
        <button className="btn primary block" onClick={onSignIn}>Sign in →</button>
        <div className="divider"><span>or</span></div>
        <button className="btn block ghost-bordered">Continue with Google</button>
        <div className="auth-foot">No account? <a href="#" className="link">Create one</a></div>
      </div>
    </div>
  </div>
);

window.Auth = Auth;
