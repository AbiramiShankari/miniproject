/**
 * PrepTalk – Shared Sidebar Navigation
 * Served from localhost:8000 — all paths are absolute.
 */

const NAV_HTML = `
<aside class="pt-sidebar" id="pt-sidebar" aria-label="Main navigation">
  <div class="pt-logo">
    <a href="/" class="pt-logo-link">🎓 PrepTalk</a>
  </div>

  <nav>
    <p class="pt-section">MAIN</p>
    <a class="pt-nav-item" href="/pages/dashboard.html"   data-page="dashboard">🏠 Dashboard</a>
    <a class="pt-nav-item" href="/pages/resume_ats.html"  data-page="resume_ats">📄 Resume &amp; ATS</a>
    <a class="pt-nav-item" href="/pages/role.html"        data-page="role">🎯 Select Role</a>

    <p class="pt-section">INTERVIEW</p>
    <a class="pt-nav-item" href="/pages/live_mock.html"   data-page="live_mock">🎙️ Live Mock Interview</a>
    <a class="pt-nav-item" href="/pages/ai_coach.html"    data-page="ai_coach">🤖 AI Coach</a>
    <a class="pt-nav-item" href="/pages/feedback.html"    data-page="feedback">📊 Feedback Report</a>

    <p class="pt-section">COMMUNICATION</p>
    <a class="pt-nav-item" href="/pages/comm_hub.html"    data-page="comm_hub">🗣️ Communication Hub</a>

    <p class="pt-section">PRACTICE</p>
    <a class="pt-nav-item" href="/pages/aptitude.html"    data-page="aptitude">🧠 Aptitude Tests</a>
    <a class="pt-nav-item" href="/pages/pyq_bank.html"    data-page="pyq_bank">🏢 Company PYQs</a>

    <p class="pt-section">MY PROGRESS</p>
    <a class="pt-nav-item" href="/pages/history.html"     data-page="history">📋 Session History</a>
    <a class="pt-nav-item" href="/pages/compare.html"     data-page="compare">⚖️ Compare Sessions</a>
    <a class="pt-nav-item" href="/pages/profile.html"     data-page="profile">👤 My Profile</a>
    <a class="pt-nav-item" href="/pages/settings.html"    data-page="settings">⚙️ Settings</a>
  </nav>

  <div class="pt-profile-mini" id="pt-profile-mini">
    <div class="pt-avatar">?</div>
    <div class="pt-uinfo">
      <div class="pt-uname" id="nav-uname">Guest</div>
      <div class="pt-uemail" id="nav-uemail">guest</div>
    </div>
  </div>

  <div class="pt-signout">
    <a href="/pages/login.html" class="pt-nav-item" id="pt-signout-btn" onclick="localStorage.removeItem('pt_user')">⬅️ Sign Out</a>
  </div>
</aside>`;

const NAV_CSS = `
  .pt-sidebar {
    width: 240px;
    min-height: 100vh;
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    padding: 1.25rem 0.75rem;
    position: sticky;
    top: 0;
    align-self: flex-start;
    flex-shrink: 0;
    overflow-y: auto;
  }
  .pt-logo { margin-bottom: 1.25rem; padding: 0 0.5rem; }
  .pt-logo-link {
    font-size: 1.3rem;
    font-weight: 800;
    color: #4f46e5;
    text-decoration: none;
    letter-spacing: -0.5px;
  }
  .pt-section {
    font-size: 0.68rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin: 0.85rem 0.5rem 0.25rem;
  }
  .pt-nav-item {
    display: block;
    padding: 0.55rem 0.75rem;
    border-radius: 8px;
    color: #475569;
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 1px;
    transition: background 0.15s, color 0.15s;
  }
  .pt-nav-item:hover  { background: #f1f5f9; color: #1e293b; }
  .pt-nav-item.pt-active { background: #ede9fe; color: #4f46e5; font-weight: 600; }

  /* Mini profile in sidebar */
  .pt-profile-mini {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem;
    background: #f8fafc;
    border-radius: 10px;
    margin-top: 1rem;
    cursor: pointer;
    text-decoration: none;
  }
  .pt-profile-mini:hover { background: #ede9fe; }
  .pt-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #fff;
    font-weight: 800;
    font-size: 0.9rem;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .pt-uname  { font-size: 0.82rem; font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
  .pt-uemail { font-size: 0.7rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }

  .pt-signout { padding-top: 0.5rem; border-top: 1px solid #e2e8f0; margin-top: 0.5rem; }

  /* Page shell */
  body.pt-page {
    display: flex;
    flex-direction: row;
    min-height: 100vh;
    margin: 0;
    background: #f8fafc;
    font-family: 'Inter', 'Segoe UI', sans-serif;
  }
  .pt-main {
    flex: 1;
    overflow-y: auto;
    min-height: 100vh;
  }
`;

(function () {
  const style = document.createElement('style');
  style.textContent = NAV_CSS;
  document.head.appendChild(style);

  const wrapper = document.createElement('div');
  wrapper.innerHTML = NAV_HTML;
  document.body.classList.add('pt-page');
  document.body.insertBefore(wrapper.firstElementChild, document.body.firstChild);

  const main = document.querySelector('.pt-main') || document.querySelector('main');
  if (main && !main.classList.contains('pt-main')) main.classList.add('pt-main');

  // Highlight active link
  const page = window.location.pathname.split('/').pop().replace('.html', '');
  document.querySelectorAll('.pt-nav-item[data-page]').forEach(link => {
    if (link.dataset.page === page) link.classList.add('pt-active');
  });

  // Show user info in sidebar
  try {
    const user = JSON.parse(localStorage.getItem('pt_user') || '{}');
    const name = user.name || 'Guest';
    const email = user.email || 'Not signed in';
    document.getElementById('nav-uname').innerText  = name;
    document.getElementById('nav-uemail').innerText = email;
    document.querySelector('.pt-avatar').innerText  = name[0]?.toUpperCase() || 'G';
  } catch(e) {}

  // Click mini profile to go to profile page
  document.getElementById('pt-profile-mini').onclick = () => {
    window.location.href = '/pages/profile.html';
  };

  // Record streak visit
  try {
    const s     = JSON.parse(localStorage.getItem('pt_streak') || '{"days":[],"current":0,"best":0}');
    const today = new Date().toISOString().split('T')[0];
    if (!s.days.includes(today)) {
      s.days.push(today);
      const yesterday = new Date(Date.now() - 864e5).toISOString().split('T')[0];
      s.current = s.days.includes(yesterday) ? s.current + 1 : 1;
      s.best    = Math.max(s.best, s.current);
      localStorage.setItem('pt_streak', JSON.stringify(s));
    }
  } catch(e) {}
})();
