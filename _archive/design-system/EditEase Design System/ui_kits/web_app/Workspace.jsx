/* global React */
const { useState } = React;

const Icon = ({ name, size = 18, color = 'currentColor', strokeWidth = 1.6 }) => {
  const paths = {
    'layout-dashboard': <><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></>,
    'check-square': <><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></>,
    'upload-cloud': <><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/><polyline points="16 16 12 12 8 16"/></>,
    'library': <><path d="M16 6l4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/></>,
    'wand': <><path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/><path d="M17.8 11.8 19 13"/><path d="M15 9h.01"/><path d="M17.8 6.2 19 5"/><path d="m3 21 9-9"/><path d="M12.2 6.2 11 5"/></>,
    'log-out': <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></>,
    'settings': <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    'zap': <><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></>,
    'scissors': <><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></>,
    'grid': <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></>,
    'shield': <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></>,
    'download': <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    'check': <polyline points="20 6 9 17 4 12"/>,
    'flag': <><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></>,
    'play': <polygon points="5 3 19 12 5 21 5 3"/>,
    'arrow-right': <><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>,
    'search': <><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
};

const Sidebar = ({ active, setActive }) => {
  const items = [
    { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
    { id: 'review', label: 'Review Queue', icon: 'check-square' },
    { id: 'uploads', label: 'Uploads', icon: 'upload-cloud' },
    { id: 'library', label: 'Organized Videos', icon: 'library' },
  ];
  return (
    <aside className="ws-sidebar">
      <a href="#" className="ws-logo">
        <span className="ws-logo-mark"><Icon name="wand" size={18} color="#58a6ff"/></span>
        <span className="ws-logo-copy"><b>EditEase</b><em>Review workspace</em></span>
      </a>
      <nav className="ws-nav">
        <div className="ws-section-label">Workspace</div>
        {items.map(it => (
          <button key={it.id} className={`ws-nav-item${active===it.id?' active':''}`} onClick={()=>setActive(it.id)}>
            <Icon name={it.icon}/> {it.label}
          </button>
        ))}
      </nav>
      <div className="ws-sb-footer">
        <div className="ws-account">
          <div className="ws-avatar">A</div>
          <div className="ws-account-copy"><b>Ash R.</b><em>admin</em></div>
        </div>
      </div>
    </aside>
  );
};

const Topbar = ({ title, subtitle }) => (
  <div className="ws-topbar">
    <div className="ws-tb-copy">
      <span className="ws-tb-eyebrow">Workspace</span>
      <span className="ws-tb-title">{title}</span>
      <span className="ws-tb-sub">{subtitle}</span>
    </div>
    <div className="ws-tb-actions">
      <button className="btn ghost"><Icon name="zap" size={14} color="#58a6ff"/> Tour Guide</button>
      <button className="btn ghost">Homepage</button>
      <span className="badge info">admin</span>
    </div>
  </div>
);

const Stat = ({ icon, label, value, sub, color }) => (
  <div className="stat-card" style={{'--strip': color}}>
    <div className="strip"/>
    <div className="stat-lbl"><Icon name={icon} size={14} color={color}/> {label}</div>
    <div className="stat-v" style={{color}}>{value}</div>
    <div className="stat-sub">{sub}</div>
  </div>
);

const DashboardView = () => (
  <>
    <div className="stat-grid">
      <Stat icon="scissors" label="Clips Extracted" value="2,914" sub="from 124 sources" color="#58a6ff"/>
      <Stat icon="check-square" label="Pending Review" value="86" sub="awaiting human signal" color="#d29922"/>
      <Stat icon="library" label="Organized" value="1,602" sub="+38 duplicates linked" color="#3fb950"/>
      <Stat icon="shield" label="Reviewers" value="7" sub="2 active right now" color="#a371f7"/>
    </div>
    <div className="panel-grid">
      <div className="panel">
        <div className="panel-head">
          <div><b>Recent activity</b><em>Latest pipeline events</em></div>
          <button className="btn-link">View all <Icon name="arrow-right" size={14}/></button>
        </div>
        <div className="activity">
          {[
            ['#3fb950','APPROVED','Drone_shot_002 → Establishing','2 min ago'],
            ['#58a6ff','PROCESSED','eva radu — 14 scenes','11 min ago'],
            ['#d29922','PENDING','WorldLink QA v3 — 6 uncertain','24 min ago'],
            ['#da3633','FLAGGED','Interview_06 scene 3','42 min ago'],
            ['#3fb950','APPROVED','b-roll_pack_03 → Product','1 h ago'],
          ].map((r,i)=>(
            <div className="activity-row" key={i}>
              <span className="dot" style={{background:r[0]}}/>
              <span className="tag" style={{color:r[0],borderColor:r[0]+'33',background:r[0]+'1a'}}>{r[1]}</span>
              <span className="msg">{r[2]}</span>
              <span className="when">{r[3]}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <div className="panel-head"><div><b>System</b><em>All services operational</em></div></div>
        <div className="sys-list">
          {[['Scene detector','Online','#3fb950'],['Embedding worker','Online','#3fb950'],['Export queue','Online','#3fb950'],['Object storage','Degraded','#d29922']].map((s,i)=>(
            <div className="sys-row" key={i}><span className="dot pulse" style={{background:s[2]}}/><span>{s[0]}</span><em style={{color:s[2]}}>{s[1]}</em></div>
          ))}
        </div>
      </div>
    </div>
  </>
);

const ReviewView = () => {
  const clips = [
    ['#1a2c1a','APPROVED','#3fb950'],['#1a2030','PENDING','#58a6ff'],['#2c1a1a','FLAGGED','#da3633'],
    ['#1a2c1a','APPROVED','#3fb950'],['#1a2030','PENDING','#58a6ff'],['#1a2c1a','APPROVED','#3fb950'],
    ['#2c1a1a','FLAGGED','#da3633'],['#1a2c1a','APPROVED','#3fb950'],
  ];
  return (
    <>
      <div className="filter-bar">
        <div className="search"><Icon name="search" size={14} color="#6e7681"/><input placeholder="Search by source, tag, scene…"/></div>
        <div className="chips">
          <button className="chip active">All</button>
          <button className="chip">Pending</button>
          <button className="chip">Flagged</button>
          <button className="chip">Approved</button>
        </div>
      </div>
      <div className="clip-grid">
        {clips.map((c,i)=>(
          <div className="clip" key={i} style={{background:c[0]}}>
            <div className="clip-bar"/>
            <div className="clip-actions">
              <button className="kbd kbd-good"><Icon name="check" size={12}/></button>
              <button className="kbd kbd-bad"><Icon name="flag" size={12}/></button>
            </div>
            <span className="clip-badge" style={{color:c[2],background:c[2]+'26'}}>{c[1]}</span>
            <span className="tc">00:0{i}:14</span>
          </div>
        ))}
      </div>
    </>
  );
};

const UploadsView = () => (
  <div className="dropzone">
    <div className="dz-icon"><Icon name="upload-cloud" size={32} color="#58a6ff"/></div>
    <h3>Drop your raw footage here</h3>
    <p>Any format — MOV, MP4, MXF, ProRes, DNxHR. We split scenes automatically.</p>
    <button className="btn primary">Browse files</button>
    <div className="dz-meta">No conversion needed · Max 50 GB / file · End-to-end encrypted</div>
  </div>
);

const LibraryView = () => {
  const folders = [
    ['Establishing','#58a6ff', 142],['Interviews','#a371f7', 87],['B-Roll','#3fb950', 311],
    ['Product','#d29922', 64],['Crowd / event','#58a6ff', 96],['Archive','#6e7681', 902],
  ];
  return (
    <div className="folders">
      {folders.map((f,i)=>(
        <div className="folder" key={i}>
          <div className="f-head">
            <span className="f-tag" style={{background:f[1]+'1a',color:f[1],borderColor:f[1]+'33'}}>● {f[0]}</span>
            <button className="btn-link"><Icon name="download" size={14}/></button>
          </div>
          <div className="f-thumbs">
            {[0,1,2,3].map(k=><div key={k} className="f-thumb" style={{background:`linear-gradient(135deg,${f[1]}33,#0d111799)`}}/>)}
          </div>
          <div className="f-meta">{f[2]} clips · ready for export</div>
        </div>
      ))}
    </div>
  );
};

const Workspace = () => {
  const [active, setActive] = useState('dashboard');
  const titles = {
    dashboard: ['Dashboard', 'Your creative hub. Track recent ingests and see what the system is organizing for you.'],
    review:    ['Review Queue', 'Quickly review and sort ambiguous clips so they land in the right folders.'],
    uploads:   ['Uploads', "Drop in your raw files. We'll split the scenes and sync them securely to the cloud."],
    library:   ['Organized Videos', 'Browse your auto-organized clips, grouped by label, ready for batch download.'],
  };
  return (
    <div className="ws-shell">
      <div className="ambient a"/><div className="ambient b"/>
      <Sidebar active={active} setActive={setActive}/>
      <div className="ws-main">
        <Topbar title={titles[active][0]} subtitle={titles[active][1]}/>
        <div className="ws-content">
          {active==='dashboard' && <DashboardView/>}
          {active==='review' && <ReviewView/>}
          {active==='uploads' && <UploadsView/>}
          {active==='library' && <LibraryView/>}
        </div>
      </div>
    </div>
  );
};

window.Workspace = Workspace;
window.Icon = Icon;
