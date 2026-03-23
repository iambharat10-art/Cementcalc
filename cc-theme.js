/* ═══════════════════════════════════════════════════════════════
   CEMENTCALC UNIVERSAL THEME ENGINE v1.0
   20 Themes + 20 Fonts — Persists across all dashboards
═══════════════════════════════════════════════════════════════ */
(function(){

// ── 20 THEMES (10 dark, 10 light) ──
const THEMES = [
  // DARK THEMES
  { id:'midnight',    name:'Midnight',      dark:true, bg:'#0a0e17', bg2:'#0f1423', bg3:'#151c2e', bg4:'#1a2338', border:'#1e2d46', border2:'#2a3d5e', text:'#e8ecf4', text2:'#9aa2c0', text3:'#6b7394', accent:'#818cf8', accent2:'#a5b4fc', green:'#34d399', red:'#f87171', swatch:'linear-gradient(135deg,#0a0e17,#1e2d46)' },
  { id:'obsidian',    name:'Obsidian',      dark:true, bg:'#09090b', bg2:'#111113', bg3:'#18181b', bg4:'#1f1f23', border:'#27272a', border2:'#3f3f46', text:'#fafafa', text2:'#a1a1aa', text3:'#71717a', accent:'#f59e0b', accent2:'#fbbf24', green:'#22c55e', red:'#ef4444', swatch:'linear-gradient(135deg,#09090b,#27272a)' },
  { id:'ocean',       name:'Ocean',         dark:true, bg:'#0a1628', bg2:'#0f1d32', bg3:'#15263e', bg4:'#1b2f4a', border:'#1e3a5f', border2:'#285180', text:'#e0eaf6', text2:'#8fa8c8', text3:'#5e7d9e', accent:'#38bdf8', accent2:'#7dd3fc', green:'#2dd4bf', red:'#fb7185', swatch:'linear-gradient(135deg,#0a1628,#1e3a5f)' },
  { id:'forest',      name:'Forest',        dark:true, bg:'#071210', bg2:'#0c1a16', bg3:'#12231e', bg4:'#182c26', border:'#1a3a2e', border2:'#255040', text:'#e0f0e8', text2:'#8ab8a0', text3:'#5e8a72', accent:'#34d399', accent2:'#6ee7b7', green:'#34d399', red:'#f87171', swatch:'linear-gradient(135deg,#071210,#1a3a2e)' },
  { id:'ember',       name:'Ember',         dark:true, bg:'#120a07', bg2:'#1a120c', bg3:'#231a12', bg4:'#2c2218', border:'#3d2c18', border2:'#584020', text:'#f0e4d8', text2:'#c0a488', text3:'#8a7258', accent:'#fb923c', accent2:'#fdba74', green:'#4ade80', red:'#f87171', swatch:'linear-gradient(135deg,#120a07,#3d2c18)' },
  { id:'violet',      name:'Violet',        dark:true, bg:'#0e0a18', bg2:'#140f22', bg3:'#1a152e', bg4:'#211b3a', border:'#2a2050', border2:'#382c6a', text:'#e8e0f8', text2:'#a898c8', text3:'#7868a0', accent:'#a78bfa', accent2:'#c4b5fd', green:'#34d399', red:'#fb7185', swatch:'linear-gradient(135deg,#0e0a18,#2a2050)' },
  { id:'slate',       name:'Slate',         dark:true, bg:'#0f1114', bg2:'#15181d', bg3:'#1c2028', bg4:'#232833', border:'#2a3040', border2:'#363e52', text:'#e2e8f0', text2:'#94a3b8', text3:'#64748b', accent:'#94a3b8', accent2:'#cbd5e1', green:'#4ade80', red:'#f87171', swatch:'linear-gradient(135deg,#0f1114,#2a3040)' },
  { id:'rose',        name:'Rose',          dark:true, bg:'#120a0d', bg2:'#1a0f14', bg3:'#23141c', bg4:'#2c1924', border:'#3d1e30', border2:'#582840', text:'#f0e0e8', text2:'#c098a8', text3:'#8a6878', accent:'#f472b6', accent2:'#f9a8d4', green:'#34d399', red:'#fb7185', swatch:'linear-gradient(135deg,#120a0d,#3d1e30)' },
  { id:'gold',        name:'Gold',          dark:true, bg:'#100d06', bg2:'#18140b', bg3:'#201c10', bg4:'#282416', border:'#3a321c', border2:'#504424', text:'#f0e8d0', text2:'#c0a870', text3:'#8a7848', accent:'#c9a227', accent2:'#e8ba3c', green:'#34d399', red:'#f87171', swatch:'linear-gradient(135deg,#100d06,#3a321c)' },
  { id:'carbon',      name:'Carbon',        dark:true, bg:'#0c0c0c', bg2:'#141414', bg3:'#1c1c1c', bg4:'#242424', border:'#2c2c2c', border2:'#3c3c3c', text:'#ececec', text2:'#a0a0a0', text3:'#707070', accent:'#00d4aa', accent2:'#40f0c8', green:'#00d4aa', red:'#ff6b6b', swatch:'linear-gradient(135deg,#0c0c0c,#2c2c2c)' },

  // LIGHT THEMES
  { id:'paper',       name:'Paper',         dark:false, bg:'#fafaf8', bg2:'#f5f5f0', bg3:'#eeeee8', bg4:'#e6e6de', border:'#d8d8d0', border2:'#c8c8c0', text:'#1a1a18', text2:'#55554f', text3:'#888880', accent:'#2563eb', accent2:'#3b82f6', green:'#16a34a', red:'#dc2626', swatch:'linear-gradient(135deg,#fafaf8,#eeeee8)' },
  { id:'cloud',       name:'Cloud',         dark:false, bg:'#f8fafc', bg2:'#f1f5f9', bg3:'#e2e8f0', bg4:'#cbd5e1', border:'#cbd5e1', border2:'#94a3b8', text:'#0f172a', text2:'#475569', text3:'#64748b', accent:'#6366f1', accent2:'#818cf8', green:'#22c55e', red:'#ef4444', swatch:'linear-gradient(135deg,#f8fafc,#e2e8f0)' },
  { id:'sand',        name:'Sand',          dark:false, bg:'#fdf8f0', bg2:'#f8f0e4', bg3:'#f0e8d8', bg4:'#e8dcc8', border:'#d8ccb4', border2:'#c0b098', text:'#2a2418', text2:'#605438', text3:'#8a7a5c', accent:'#b45309', accent2:'#d97706', green:'#16a34a', red:'#dc2626', swatch:'linear-gradient(135deg,#fdf8f0,#f0e8d8)' },
  { id:'snow',        name:'Snow',          dark:false, bg:'#ffffff', bg2:'#f9fafb', bg3:'#f3f4f6', bg4:'#e5e7eb', border:'#e5e7eb', border2:'#d1d5db', text:'#111827', text2:'#4b5563', text3:'#6b7280', accent:'#7c3aed', accent2:'#8b5cf6', green:'#10b981', red:'#ef4444', swatch:'linear-gradient(135deg,#ffffff,#f3f4f6)' },
  { id:'mint',        name:'Mint',          dark:false, bg:'#f0fdf4', bg2:'#e8f8ee', bg3:'#dcf0e4', bg4:'#c8e8d4', border:'#b8dcc4', border2:'#90c8a8', text:'#052e16', text2:'#1a5c32', text3:'#388050', accent:'#059669', accent2:'#10b981', green:'#059669', red:'#dc2626', swatch:'linear-gradient(135deg,#f0fdf4,#dcf0e4)' },
  { id:'lavender',    name:'Lavender',      dark:false, bg:'#f5f3ff', bg2:'#ede9fe', bg3:'#ddd6fe', bg4:'#c4b5fd', border:'#c4b5fd', border2:'#a78bfa', text:'#1e1b4b', text2:'#4338ca', text3:'#6366f1', accent:'#7c3aed', accent2:'#8b5cf6', green:'#22c55e', red:'#ef4444', swatch:'linear-gradient(135deg,#f5f3ff,#ddd6fe)' },
  { id:'cream',       name:'Cream',         dark:false, bg:'#fefce8', bg2:'#fef9c3', bg3:'#fef08a', bg4:'#fde047', border:'#eab308', border2:'#ca8a04', text:'#1c1917', text2:'#57534e', text3:'#78716c', accent:'#d97706', accent2:'#f59e0b', green:'#16a34a', red:'#dc2626', swatch:'linear-gradient(135deg,#fefce8,#fef9c3)' },
  { id:'ice',         name:'Ice',           dark:false, bg:'#f0f9ff', bg2:'#e0f2fe', bg3:'#bae6fd', bg4:'#7dd3fc', border:'#7dd3fc', border2:'#38bdf8', text:'#0c4a6e', text2:'#0369a1', text3:'#0284c7', accent:'#0284c7', accent2:'#0ea5e9', green:'#22c55e', red:'#ef4444', swatch:'linear-gradient(135deg,#f0f9ff,#bae6fd)' },
  { id:'blush',       name:'Blush',         dark:false, bg:'#fff1f2', bg2:'#ffe4e6', bg3:'#fecdd3', bg4:'#fda4af', border:'#fda4af', border2:'#fb7185', text:'#1c1917', text2:'#6b5c5e', text3:'#8a7678', accent:'#e11d48', accent2:'#f43f5e', green:'#22c55e', red:'#e11d48', swatch:'linear-gradient(135deg,#fff1f2,#fecdd3)' },
  { id:'pearl',       name:'Pearl',         dark:false, bg:'#f8f8f6', bg2:'#f0f0ee', bg3:'#e4e4e0', bg4:'#d4d4d0', border:'#c4c4be', border2:'#a4a49e', text:'#1a1a18', text2:'#52524e', text3:'#78787a', accent:'#525252', accent2:'#737373', green:'#16a34a', red:'#dc2626', swatch:'linear-gradient(135deg,#f8f8f6,#e4e4e0)' },
];

// ── 20 FONTS ──
const FONTS = [
  { id:'system',      name:'System Default', family:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif', mono:'ui-monospace,SFMono-Regular,monospace' },
  { id:'inter',       name:'Inter',          family:'"Inter",sans-serif',              mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' },
  { id:'dm-sans',     name:'DM Sans',        family:'"DM Sans",sans-serif',            mono:'"DM Mono",monospace',         url:'https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap' },
  { id:'outfit',      name:'Outfit',         family:'"Outfit",sans-serif',             mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap' },
  { id:'poppins',     name:'Poppins',        family:'"Poppins",sans-serif',            mono:'"Fira Code",monospace',       url:'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap' },
  { id:'nunito',      name:'Nunito',         family:'"Nunito",sans-serif',             mono:'"Source Code Pro",monospace',  url:'https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;500;600;700&display=swap' },
  { id:'raleway',     name:'Raleway',        family:'"Raleway",sans-serif',            mono:'"IBM Plex Mono",monospace',   url:'https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap' },
  { id:'lato',        name:'Lato',           family:'"Lato",sans-serif',               mono:'"Roboto Mono",monospace',     url:'https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&display=swap' },
  { id:'rubik',       name:'Rubik',          family:'"Rubik",sans-serif',              mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap' },
  { id:'manrope',     name:'Manrope',        family:'"Manrope",sans-serif',            mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap' },
  { id:'space',       name:'Space Grotesk',  family:'"Space Grotesk",sans-serif',      mono:'"Space Mono",monospace',      url:'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap' },
  { id:'plus',        name:'Plus Jakarta',   family:'"Plus Jakarta Sans",sans-serif',  mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap' },
  { id:'work',        name:'Work Sans',      family:'"Work Sans",sans-serif',          mono:'"Fira Code",monospace',       url:'https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600;700&display=swap' },
  { id:'sora',        name:'Sora',           family:'"Sora",sans-serif',               mono:'"IBM Plex Mono",monospace',   url:'https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap' },
  { id:'barlow',      name:'Barlow',         family:'"Barlow",sans-serif',             mono:'"Roboto Mono",monospace',     url:'https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&display=swap' },
  { id:'mulish',      name:'Mulish',         family:'"Mulish",sans-serif',             mono:'"Source Code Pro",monospace',  url:'https://fonts.googleapis.com/css2?family=Mulish:wght@300;400;500;600;700&display=swap' },
  { id:'open',        name:'Open Sans',      family:'"Open Sans",sans-serif',          mono:'"Fira Code",monospace',       url:'https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&display=swap' },
  { id:'cabin',       name:'Cabin',          family:'"Cabin",sans-serif',              mono:'"Ubuntu Mono",monospace',     url:'https://fonts.googleapis.com/css2?family=Cabin:wght@400;500;600;700&display=swap' },
  { id:'karla',       name:'Karla',          family:'"Karla",sans-serif',              mono:'"JetBrains Mono",monospace',  url:'https://fonts.googleapis.com/css2?family=Karla:wght@300;400;500;600;700&display=swap' },
  { id:'ibm',         name:'IBM Plex',       family:'"IBM Plex Sans",sans-serif',      mono:'"IBM Plex Mono",monospace',   url:'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap' },
];

// ── STATE ──
let currentTheme = localStorage.getItem('cc_theme') || 'obsidian';
let currentFont = localStorage.getItem('cc_font') || 'system';
let panelOpen = false;

// ── APPLY THEME ──
function applyTheme(themeId) {
  const t = THEMES.find(x => x.id === themeId);
  if (!t) return;
  currentTheme = themeId;
  localStorage.setItem('cc_theme', themeId);

  const r = document.documentElement;
  const s = r.style;

  // ALL variable names used across ALL dashboards
  // Backgrounds
  s.setProperty('--bg', t.bg);
  s.setProperty('--bg2', t.bg2);
  s.setProperty('--bg3', t.bg3);
  s.setProperty('--bg4', t.bg4);
  s.setProperty('--bg5', t.bg4);
  s.setProperty('--surface', t.bg2);
  s.setProperty('--surface2', t.bg3);
  s.setProperty('--surface3', t.bg4);
  s.setProperty('--card', t.bg2);
  s.setProperty('--card2', t.bg3);
  s.setProperty('--cd', t.bg2);
  s.setProperty('--cd2', t.bg3);
  s.setProperty('--panel', t.bg2);

  // Borders
  s.setProperty('--border', t.border);
  s.setProperty('--border2', t.border2);
  s.setProperty('--brd', t.border);
  s.setProperty('--brd2', t.border2);
  s.setProperty('--brdH', t.border2);
  s.setProperty('--bd', t.border);
  s.setProperty('--bd2', t.border2);
  s.setProperty('--grid', t.border);
  s.setProperty('--dimLine', t.border2);

  // Text
  s.setProperty('--white', t.text);
  s.setProperty('--text', t.text);
  s.setProperty('--bt', t.text);
  s.setProperty('--slate', t.text2);
  s.setProperty('--text2', t.text2);
  s.setProperty('--tx', t.text2);
  s.setProperty('--slate2', t.text3);
  s.setProperty('--text3', t.text3);
  s.setProperty('--dm', t.text3);
  s.setProperty('--dimText', t.text2);
  s.setProperty('--muted', t.text3);

  // Accents
  s.setProperty('--accent', t.accent);
  s.setProperty('--accent2', t.accent2);
  s.setProperty('--accent3', t.accent2);
  s.setProperty('--accent-dim', t.accent + '18');
  s.setProperty('--accentDim', t.accent + '18');
  s.setProperty('--gold', t.accent);
  s.setProperty('--gold2', t.accent2);
  s.setProperty('--gold3', t.accent2);
  s.setProperty('--gold-dim', t.accent + '18');
  s.setProperty('--amber', t.accent);
  s.setProperty('--amber2', t.accent2);
  s.setProperty('--amber3', t.accent2);
  s.setProperty('--amber-dim', t.accent + '18');
  s.setProperty('--am', t.accent);
  s.setProperty('--am2', t.accent2);
  s.setProperty('--am3', t.accent2);
  s.setProperty('--amG', t.accent + '25');
  s.setProperty('--amD', t.accent + '50');
  s.setProperty('--accent-water', t.accent);
  s.setProperty('--accent-air', t.accent2);

  // Status colors
  s.setProperty('--green', t.green);
  s.setProperty('--green2', t.green);
  s.setProperty('--gn', t.green);
  s.setProperty('--gn2', t.green);
  s.setProperty('--green-dim', t.green + '18');
  s.setProperty('--greenBg', t.green + '12');
  s.setProperty('--greenBd', t.green + '38');
  s.setProperty('--red', t.red);
  s.setProperty('--red2', t.red);
  s.setProperty('--rd', t.red);
  s.setProperty('--rd2', t.red);
  s.setProperty('--red-dim', t.red + '18');
  s.setProperty('--redBg', t.red + '12');
  s.setProperty('--redBd', t.red + '38');
  s.setProperty('--amberBg', t.accent + '12');
  s.setProperty('--amberBd', t.accent + '38');

  // Additional colors
  s.setProperty('--cyan', t.accent2);
  s.setProperty('--cyan2', t.accent2);
  s.setProperty('--cy', t.accent2);
  s.setProperty('--cyan-dim', t.accent2 + '18');
  s.setProperty('--blue', t.accent);
  s.setProperty('--blue2', t.accent2);
  s.setProperty('--bl', t.accent);
  s.setProperty('--bl2', t.accent2);
  s.setProperty('--blue-dim', t.accent + '18');
  s.setProperty('--violet', t.accent);
  s.setProperty('--violet2', t.accent2);
  s.setProperty('--pu', t.accent);
  s.setProperty('--pk', t.accent2);
  s.setProperty('--teal', t.green);

  // Body bg
  document.body.style.background = t.bg;
  document.body.style.color = t.text;

  // Update theme picker UI
  updatePickerUI();

  // Update toggle button for light themes
  const btn = document.getElementById('cc-theme-toggle');
  if (btn) {
    btn.style.background = t.dark ? 'rgba(20,20,30,0.85)' : 'rgba(255,255,255,0.85)';
    btn.style.color = t.dark ? '#fff' : '#333';
    btn.style.borderColor = t.dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)';
  }

  // Update panel bg for light themes
  const panel = document.getElementById('cc-theme-panel');
  if (panel) {
    panel.style.background = t.dark ? 'rgba(16,18,28,0.92)' : 'rgba(255,255,255,0.95)';
    panel.style.borderColor = t.dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    panel.querySelectorAll('.cc-panel-title, .cc-panel-close').forEach(el => {
      el.style.color = t.dark ? '' : '#1a1a1a';
    });
    panel.querySelectorAll('.cc-section-label').forEach(el => {
      el.style.color = t.dark ? '' : 'rgba(0,0,0,0.4)';
    });
    panel.querySelectorAll('.cc-font-btn').forEach(el => {
      el.style.color = t.dark ? '' : '#333';
      el.style.borderColor = t.dark ? '' : 'rgba(0,0,0,0.1)';
    });
  }
}

// ── APPLY FONT ──
function applyFont(fontId) {
  const f = FONTS.find(x => x.id === fontId);
  if (!f) return;
  currentFont = fontId;
  localStorage.setItem('cc_font', fontId);

  // Load font if needed
  if (f.url && !document.querySelector(`link[data-font="${fontId}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = f.url;
    link.dataset.font = fontId;
    document.head.appendChild(link);
  }

  const s = document.documentElement.style;
  // Override ALL font variable names
  s.setProperty('--font-body', f.family);
  s.setProperty('--font-display', f.family);
  s.setProperty('--font-mono', f.mono);
  s.setProperty('--sans', f.family);
  s.setProperty('--mono', f.mono);
  s.setProperty('--sn', f.family);
  s.setProperty('--mo', f.mono);
  s.setProperty('--disp', f.family);
  s.setProperty('--display', f.family);

  document.body.style.fontFamily = f.family;

  updatePickerUI();
}

// ── UI ──
function updatePickerUI() {
  document.querySelectorAll('.cc-theme-swatch').forEach(el => {
    el.classList.toggle('active', el.dataset.theme === currentTheme);
  });
  document.querySelectorAll('.cc-font-btn').forEach(el => {
    el.classList.toggle('active', el.dataset.font === currentFont);
  });
}

function togglePanel() {
  panelOpen = !panelOpen;
  const panel = document.getElementById('cc-theme-panel');
  if (panel) panel.classList.toggle('open', panelOpen);
}

// ── BUILD UI ──
function buildPicker() {
  // Toggle button
  const btn = document.createElement('button');
  btn.id = 'cc-theme-toggle';
  btn.innerHTML = '🎨';
  btn.title = 'Theme & Font Settings';
  btn.onclick = togglePanel;
  document.body.appendChild(btn);

  // Panel
  const panel = document.createElement('div');
  panel.id = 'cc-theme-panel';

  let html = `
    <div class="cc-panel-header">
      <span class="cc-panel-title">Appearance</span>
      <button class="cc-panel-close" onclick="document.getElementById('cc-theme-panel').classList.remove('open')">✕</button>
    </div>
    <div class="cc-section-label">Dark Themes</div>
    <div class="cc-theme-grid">
  `;
  THEMES.filter(t => t.dark).forEach(t => {
    html += `<div class="cc-theme-swatch" data-theme="${t.id}" style="background:${t.swatch}" title="${t.name}" onclick="window._ccApplyTheme('${t.id}')"><span style="color:${t.text};mix-blend-mode:difference;font-size:8px;">${t.name.slice(0,3)}</span></div>`;
  });
  html += `</div><div class="cc-section-label">Light Themes</div><div class="cc-theme-grid">`;
  THEMES.filter(t => !t.dark).forEach(t => {
    html += `<div class="cc-theme-swatch" data-theme="${t.id}" style="background:${t.swatch};border:1px solid rgba(0,0,0,0.1);" title="${t.name}" onclick="window._ccApplyTheme('${t.id}')"><span style="color:${t.text};font-size:8px;">${t.name.slice(0,3)}</span></div>`;
  });
  html += `</div><div class="cc-section-label">Fonts</div><div class="cc-font-grid">`;
  FONTS.forEach(f => {
    html += `<div class="cc-font-btn" data-font="${f.id}" style="font-family:${f.family}" onclick="window._ccApplyFont('${f.id}')">${f.name}</div>`;
  });
  html += `</div>`;

  panel.innerHTML = html;
  document.body.appendChild(panel);
}

// ── INIT ──
window._ccApplyTheme = applyTheme;
window._ccApplyFont = applyFont;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  buildPicker();
  applyTheme(currentTheme);
  applyFont(currentFont);
}

})();
