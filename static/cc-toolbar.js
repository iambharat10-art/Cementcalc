// ═══════════════════════════════════════════════════════════
// CementCalc — Universal Save/Autosave/Print Toolbar
// Injected into every dashboard by main.py
// ═══════════════════════════════════════════════════════════

(function(){
  const AUTOSAVE_INTERVAL = 30000; // 30 seconds
  const DB_KEY = 'cc_' + location.pathname.replace(/[^a-z0-9]/gi,'_');

  // ── Create Toolbar ──
  const bar = document.createElement('div');
  bar.id = 'cc-toolbar';
  bar.innerHTML = `
    <div class="cct-inner">
      <button class="cct-btn" onclick="ccSave()" title="Save (Ctrl+S)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/></svg>
        Save
      </button>
      <button class="cct-btn" onclick="ccLoad()" title="Load Last Save">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 15v4c0 1.1.9 2 2 2h14a2 2 0 002-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
        Load
      </button>
      <button class="cct-btn" onclick="ccPrint()" title="Print (Ctrl+P)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        Print
      </button>
      <span class="cct-status" id="cct-status"></span>
      <label class="cct-auto" title="Auto-save every 30 seconds">
        <input type="checkbox" id="cct-autosave" checked onchange="ccToggleAuto(this.checked)">
        Auto
      </label>
    </div>
  `;

  // ── Styles ──
  const style = document.createElement('style');
  style.textContent = `
    #cc-toolbar{position:fixed;bottom:16px;left:16px;z-index:9998;font-family:'DM Sans',sans-serif}
    .cct-inner{display:flex;align-items:center;gap:6px;background:rgba(17,22,32,0.95);backdrop-filter:blur(12px);border:1px solid rgba(37,46,66,0.8);border-radius:10px;padding:6px 10px;box-shadow:0 8px 32px rgba(0,0,0,0.4)}
    .cct-btn{display:flex;align-items:center;gap:5px;padding:6px 12px;border-radius:7px;border:1px solid rgba(37,46,66,0.6);background:rgba(255,255,255,0.04);color:#9aa2c0;font-size:11.5px;font-weight:500;cursor:pointer;font-family:inherit;transition:all 0.2s;white-space:nowrap}
    .cct-btn:hover{background:rgba(255,255,255,0.08);color:#e8ecf4;border-color:rgba(59,130,246,0.3)}
    .cct-btn:active{transform:scale(0.97)}
    .cct-status{font-size:10px;color:#6b7394;font-family:'JetBrains Mono',monospace;padding:0 4px;min-width:40px;text-align:center}
    .cct-auto{display:flex;align-items:center;gap:4px;font-size:10.5px;color:#6b7394;cursor:pointer;padding:4px 8px;border-radius:5px}
    .cct-auto:hover{color:#9aa2c0}
    .cct-auto input{accent-color:#3b82f6;width:13px;height:13px}
    @media print{#cc-toolbar{display:none!important}}
    @media(max-width:600px){.cct-inner{flex-wrap:wrap;justify-content:center}}
  `;

  // ── Print Styles ──
  const printStyle = document.createElement('style');
  printStyle.textContent = `
    @media print {
      body{background:#fff!important;color:#000!important;font-size:11pt!important}
      *{color:#000!important;background:transparent!important;border-color:#ccc!important;box-shadow:none!important;text-shadow:none!important}
      .hdr,.tabs,#cc-toolbar,#cc-theme-picker,.btn-add,.btn-del,button,.btn-hdr,.btn,.btn-primary,.btn-outline,.tab{display:none!important}
      .panel{display:block!important;break-inside:avoid}
      .panel:not(.active){display:none!important}
      .card{border:1px solid #ddd!important;margin-bottom:12pt!important;page-break-inside:avoid}
      .card-t{font-size:13pt!important;font-weight:700!important;border-bottom:2px solid #333!important}
      .card-t::before{background:#333!important}
      .main{max-width:100%!important;padding:0!important}
      table{page-break-inside:avoid}
      table.dt th,table.feas th{background:#eee!important;color:#000!important}
      .m,.res-card{border:1px solid #ccc!important;padding:8pt!important}
      .m .vl,.res-card .vl{color:#000!important;font-size:14pt!important}
      .m .lb,.res-card .lb{color:#555!important}
      input,select{border:1px solid #aaa!important;padding:4pt!important}
      .layout{display:block!important}
      svg{max-width:100%!important}
      h1::after{content:" — CementCalc";font-size:10pt;font-weight:400;color:#666}
      @page{margin:15mm;size:A4}
    }
  `;

  document.head.appendChild(style);
  document.head.appendChild(printStyle);
  document.body.appendChild(bar);

  // ── Save All Inputs ──
  window.ccSave = function(){
    const data = {};
    document.querySelectorAll('input, select, textarea').forEach((el,i) => {
      const key = el.id || el.name || ('inp_'+i);
      if(el.type === 'checkbox') data[key] = el.checked;
      else data[key] = el.value;
    });
    data._timestamp = Date.now();
    data._path = location.pathname;
    try {
      localStorage.setItem(DB_KEY, JSON.stringify(data));
      ccStatus('Saved ✓', '#22c55e');
    } catch(e) {
      ccStatus('Error!', '#ef4444');
    }
  };

  // ── Load Saved Data ──
  window.ccLoad = function(){
    try {
      const raw = localStorage.getItem(DB_KEY);
      if(!raw){ ccStatus('No data', '#f59e0b'); return; }
      const data = JSON.parse(raw);
      let count = 0;
      document.querySelectorAll('input, select, textarea').forEach((el,i) => {
        const key = el.id || el.name || ('inp_'+i);
        if(key in data){
          if(el.type === 'checkbox') el.checked = !!data[key];
          else el.value = data[key];
          el.dispatchEvent(new Event('change', {bubbles:true}));
          el.dispatchEvent(new Event('input', {bubbles:true}));
          count++;
        }
      });
      const age = data._timestamp ? Math.round((Date.now()-data._timestamp)/60000) : '?';
      ccStatus(`Loaded (${age}m ago)`, '#22c55e');
    } catch(e) {
      ccStatus('Error!', '#ef4444');
    }
  };

  // ── Print ──
  window.ccPrint = function(){ window.print(); };

  // ── Autosave ──
  let autoTimer = null;
  window.ccToggleAuto = function(on){
    if(autoTimer) clearInterval(autoTimer);
    if(on){
      autoTimer = setInterval(()=>{
        ccSave();
        ccStatus('Auto ✓', '#6b7394');
      }, AUTOSAVE_INTERVAL);
    }
  };
  ccToggleAuto(true);

  // ── Status ──
  function ccStatus(msg, color){
    const el = document.getElementById('cct-status');
    if(el){ el.textContent = msg; el.style.color = color; }
    setTimeout(()=>{ if(el) el.textContent = ''; }, 3000);
  }

  // ── Keyboard Shortcuts ──
  document.addEventListener('keydown', function(e){
    if((e.ctrlKey || e.metaKey) && e.key === 's'){
      e.preventDefault();
      ccSave();
    }
  });

  // ── Auto-close theme picker when clicking on dashboard ──
  document.addEventListener('click', function(e){
    const panel = document.getElementById('cc-theme-panel');
    if(!panel || !panel.classList.contains('open')) return;
    const btn = document.getElementById('cc-theme-toggle');
    if(!panel.contains(e.target) && (!btn || !btn.contains(e.target))){
      panel.classList.remove('open');
    }
  });
})();
