"""
CementCalc — FastAPI Backend
Serves dashboards with Google OAuth for restricted access.
Includes SEO (sitemap, robots.txt, meta tags) and payment-ready structure.
"""

import os
import json
import secrets
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION — Edit this to add/remove dashboards
# ═══════════════════════════════════════════════════════════════

SITE_URL = os.getenv("SITE_URL", "https://cementcalc.onrender.com")
STRIPE_ENABLED = os.getenv("STRIPE_ENABLED", "false").lower() == "true"
MONTHLY_PRICE = os.getenv("MONTHLY_PRICE", "$10")
SUPER_ADMIN = os.getenv("SUPER_ADMIN", "iambharat10@gmail.com")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", SUPER_ADMIN).split(",")

# ── Admin Config (JSON file, no database needed) ──
CONFIG_FILE = Path(__file__).parent / "admin_config.json"

def load_admin_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            pass
    return {
        "pro_dashboards": [],
        "pricing": {
            "individual": 999, "individual_currency": "INR",
            "org_base": 9999, "org_base_users": 50,
            "org_extra": 5000, "org_extra_users": 25,
            "currency": "INR"
        },
        "admin_emails": [SUPER_ADMIN],
        "free_emails": [],
        "organizations": {}
    }

def save_admin_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def is_admin(request):
    user = get_user(request)
    if not user:
        return False
    config = load_admin_config()
    admin_list = config.get("admin_emails", [SUPER_ADMIN])
    return user.get("email", "").lower() in [e.lower().strip() for e in admin_list]

def has_pro_access(request):
    """Check if user has pro access: admin, free-lifetime, or org member"""
    user = get_user(request)
    if not user:
        return False
    email = user.get("email", "").lower().strip()
    config = load_admin_config()
    # Admins always have access
    admin_list = [e.lower().strip() for e in config.get("admin_emails", [SUPER_ADMIN])]
    if email in admin_list:
        return True
    # Free lifetime emails
    free_list = [e.lower().strip() for e in config.get("free_emails", [])]
    if email in free_list:
        return True
    # Organization members
    for org_id, org in config.get("organizations", {}).items():
        org_emails = [e.lower().strip() for e in org.get("members", [])]
        hod_emails = [e.lower().strip() for e in org.get("hods", [])]
        if email in org_emails or email in hod_emails or email == org.get("admin_email", "").lower().strip():
            if org.get("active", False):
                return True
    # TODO: Check Stripe subscription when enabled
    return False

DASHBOARDS = [
    {
        "id": "belt-conveyor",
        "title": "Belt Conveyor Design",
        "subtitle": "CEMA / IS 11592 Standards",
        "description": "Complete belt conveyor design with motor sizing, idler selection, belt tension analysis, and auxiliary machinery calculations.",
        "file": "Belt Conveyor.html",
        "icon": "⚙️",
        "category": "Material Handling",
        "restricted": False,
        "color": "#00b4d8",
        "keywords": "belt conveyor design, CEMA calculator, IS 11592, conveyor motor sizing, belt tension, idler selection",
    },
    {
        "id": "cement-plant-sizing",
        "title": "Cement Plant Equipment Sizing",
        "subtitle": "Full Plant Design Suite",
        "description": "Comprehensive equipment sizing for crushers, raw mills, kilns, cement mills, and all major cement plant equipment.",
        "file": "Cement_Plant_sizing_dashboard.html",
        "icon": "🏭",
        "category": "Plant Design",
        "restricted": False,
        "color": "#c9a227",
        "keywords": "cement plant equipment sizing, crusher sizing, raw mill design, kiln sizing, cement mill calculator",
    },
    {
        "id": "grinding-bond-index",
        "title": "Grinding & Bond Index Calculator",
        "subtitle": "Bond Work Index Method",
        "description": "Bond work index calculations for ball mills and VRMs with power consumption estimation and mill sizing.",
        "file": "grinding-bond-index-calculator.html",
        "icon": "🔬",
        "category": "Grinding",
        "restricted": True,
        "color": "#f59e0b",
        "keywords": "bond work index calculator, ball mill sizing, VRM power consumption, grinding energy, bond index",
    },
    {
        "id": "kiln-heat-balance",
        "title": "Kiln Heat Balance",
        "subtitle": "Thermal Analysis",
        "description": "Complete rotary kiln heat balance with heat input/output analysis, radiation losses, and thermal efficiency calculations.",
        "file": "kiln-heat-balance.html",
        "icon": "🔥",
        "category": "Pyroprocessing",
        "restricted": False,
        "color": "#ef4444",
        "keywords": "kiln heat balance, rotary kiln thermal analysis, heat loss calculation, kiln efficiency, pyroprocessing",
    },
    {
        "id": "pipe-sizing",
        "title": "Pipe Sizing Calculator",
        "subtitle": "Fluid & Gas Systems",
        "description": "Pipe diameter selection for water, air, and slurry systems with pressure drop calculations and velocity checks.",
        "file": "Pipe_Sizing_calculator.html",
        "icon": "🔧",
        "category": "Utilities",
        "restricted": False,
        "color": "#06b6d4",
        "keywords": "pipe sizing calculator, pressure drop calculation, pipe diameter selection, fluid velocity, slurry pipe design",
    },
    {
        "id": "project-management",
        "title": "Project Management Dashboard",
        "subtitle": "Cement Plant PM Tool",
        "description": "Track drawings, submittals, RFIs, and project milestones for cement plant construction projects.",
        "file": "Project_Management_Dashboard.html",
        "icon": "📋",
        "category": "Management",
        "restricted": False,
        "color": "#3b82f6",
        "keywords": "cement plant project management, construction tracking, drawing register, RFI tracker, submittal log",
    },
    {
        "id": "raw-mix-design",
        "title": "Raw Mix Design Calculator",
        "subtitle": "Duda Reference Method",
        "description": "Raw mix proportioning using standard cement chemistry with LSF, SM, AM modulus targets and optimization.",
        "file": "Raw_Mix_Design_Calculator_Duda.html",
        "icon": "⚗️",
        "category": "Process Chemistry",
        "restricted": False,
        "color": "#a78bfa",
        "keywords": "raw mix design, cement chemistry, LSF calculator, silica modulus, alumina modulus, Duda method",
    },
    {
        "id": "silo-hopper",
        "title": "Silo & Hopper Calculator",
        "subtitle": "Storage Design",
        "description": "Silo and hopper capacity calculations with geometry optimization, structural loads, and discharge flow analysis.",
        "file": "Silo_and_Hopper_dashboard.html",
        "icon": "🏗️",
        "category": "Storage",
        "restricted": True,
        "color": "#4478ff",
        "keywords": "silo capacity calculator, hopper design, storage bin sizing, discharge flow, bulk material storage",
    },
    {
        "id": "stockpile",
        "title": "Stockpile Calculator",
        "subtitle": "Capacity & Geometry",
        "description": "Limestone and material stockpile volume calculations with conical, trapezoidal, and longitudinal pile geometries.",
        "file": "Stockpile_dashboard.html",
        "icon": "⛰️",
        "category": "Storage",
        "restricted": False,
        "color": "#e88b2e",
        "keywords": "stockpile volume calculator, limestone stockpile, conical pile, longitudinal stockpile, material storage",
    },
    {
        "id": "silo-sizing",
        "title": "Silo Sizing Calculator",
        "subtitle": "Inverted Cone & Flat Bottom",
        "description": "Silo capacity and geometry sizing for inverted cone and flat bottom silos with reverse calculation for optimal diameter selection.",
        "file": "Silo_Sizing_Calculator.html",
        "icon": "🏗️",
        "category": "Storage",
        "restricted": False,
        "color": "#d97706",
        "keywords": "silo sizing calculator, inverted cone silo, flat bottom silo, silo diameter, silo capacity, cement silo design",
    },
    {
        "id": "bagfilter-dedusting",
        "title": "Bagfilter & Dedusting Calculator",
        "subtitle": "Nuisance Filter Sizing",
        "description": "Bagfilter sizing for up to 6 venting points with pipe sizing, fan selection, Nm3/m3 converter, and standard motor selection for cement plant dedusting.",
        "file": "Bagfilter_Dedusting_Calculator.html",
        "icon": "🌬️",
        "category": "Utilities",
        "restricted": False,
        "color": "#06b6d4",
        "keywords": "bagfilter calculator, dedusting, nuisance filter, bag filter sizing, fan selection, pipe sizing, cement plant dust collection",
    },
    {
        "id": "compressor-power",
        "title": "Compressor Power & Temperature",
        "subtitle": "Isentropic Compression",
        "description": "Compressor power calculation and discharge temperature for isentropic and real compression with scenario comparison and full thermodynamic workthrough.",
        "file": "Compressor_Power_Temperature.html",
        "icon": "🔧",
        "category": "Utilities",
        "restricted": False,
        "color": "#8b5cf6",
        "keywords": "compressor power calculator, discharge temperature, isentropic compression, compression ratio, air compressor sizing",
    },
    {
        "id": "vrm-heat-balance",
        "title": "VRM Heat & Mass Balance",
        "subtitle": "Vertical Roller Mill Analysis",
        "description": "Complete VRM heat and mass balance for raw mill, coal mill, and cement mill with drying capacity analysis.",
        "file": "vrm_heat_balance.html",
        "icon": "🌀",
        "category": "Grinding",
        "restricted": True,
        "color": "#10b981",
        "keywords": "VRM heat balance, vertical roller mill, mass balance, drying capacity, raw mill heat balance",
    },
]

# ═══════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(title="CementCalc", version="1.1.0")

SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

oauth = OAuth()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def get_user(request: Request) -> Optional[dict]:
    return request.session.get("user")

def get_dashboard_by_id(dashboard_id: str) -> Optional[dict]:
    for d in DASHBOARDS:
        if d["id"] == dashboard_id:
            return d
    return None

def is_user_subscribed(request: Request) -> bool:
    """Check subscription. During testing, all logged-in users have access.
    When STRIPE_ENABLED=true, this will check Stripe subscription status."""
    if not STRIPE_ENABLED:
        return True
    # FUTURE: Check Stripe subscription here
    return True


# ═══════════════════════════════════════════════════════════════
# SEO ROUTES — robots.txt and sitemap.xml
# ═══════════════════════════════════════════════════════════════

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return f"""User-agent: *
Allow: /
Allow: /tool/
Disallow: /login
Disallow: /logout
Disallow: /auth/
Disallow: /api/
Disallow: /dashboard/

Sitemap: {SITE_URL}/sitemap.xml
"""

@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    today = datetime.now().strftime("%Y-%m-%d")
    urls = []
    urls.append(f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""")

    urls.append(f"""  <url>
    <loc>{SITE_URL}/pricing</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>""")

    for dash in DASHBOARDS:
        priority = "0.9" if not dash["restricted"] else "0.7"
        urls.append(f"""  <url>
    <loc>{SITE_URL}/tool/{dash['id']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{priority}</priority>
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


# ═══════════════════════════════════════════════════════════════
# SEO PAGES — Google-indexable page per dashboard
# ═══════════════════════════════════════════════════════════════

@app.get("/tool/{dashboard_id}", response_class=HTMLResponse)
async def dashboard_seo_page(request: Request, dashboard_id: str):
    dash = get_dashboard_by_id(dashboard_id)
    if not dash:
        raise HTTPException(status_code=404, detail="Tool not found")
    user = get_user(request)
    return templates.TemplateResponse("tool_seo.html", {
        "request": request,
        "dash": dash,
        "user": user,
        "site_url": SITE_URL,
        "all_dashboards": DASHBOARDS,
        "stripe_enabled": STRIPE_ENABLED,
        "monthly_price": MONTHLY_PRICE,
    })


# ═══════════════════════════════════════════════════════════════
# SUBSCRIPTION POPUP PAGE
# ═══════════════════════════════════════════════════════════════

def render_subscription_page(dash, user, pricing):
    ind_price = pricing.get("individual", 999)
    org_base = pricing.get("org_base", 9999)
    org_users = pricing.get("org_base_users", 50)
    org_extra = pricing.get("org_extra", 5000)
    org_extra_u = pricing.get("org_extra_users", 25)
    cur = pricing.get("currency", "INR")

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Upgrade to Pro — CementCalc</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0b0e14;color:#e8ecf4;font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}}
.overlay{{position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:0}}
.popup{{position:relative;z-index:1;background:#111620;border:1px solid #252e42;border-radius:16px;max-width:780px;width:100%;padding:32px;box-shadow:0 24px 80px rgba(0,0,0,0.6)}}
.popup-hdr{{text-align:center;margin-bottom:28px}}.popup-hdr h1{{font-size:22px;font-weight:800;margin-bottom:6px}}.popup-hdr p{{font-size:13px;color:#6b7394}}
.lock-icon{{font-size:48px;margin-bottom:12px;display:block}}
.plans{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
@media(max-width:600px){{.plans{{grid-template-columns:1fr}}}}
.plan{{background:#171d2a;border:1px solid #252e42;border-radius:12px;padding:24px;transition:border-color 0.2s;position:relative}}
.plan:hover{{border-color:#8b5cf6}}.plan.featured{{border-color:#8b5cf6;background:#1a1f30}}
.plan.featured::after{{content:'POPULAR';position:absolute;top:-10px;right:16px;background:#8b5cf6;color:#fff;font-size:9px;font-weight:800;padding:3px 10px;border-radius:4px;letter-spacing:0.5px}}
.plan-name{{font-size:15px;font-weight:700;margin-bottom:4px}}.plan-price{{font-size:32px;font-weight:800;color:#a78bfa;font-family:'JetBrains Mono',monospace;margin-bottom:2px}}
.plan-price .cur{{font-size:14px;font-weight:500;color:#6b7394}}.plan-price .per{{font-size:12px;font-weight:400;color:#6b7394}}
.plan-detail{{font-size:12px;color:#9aa2c0;margin-bottom:16px;line-height:1.6}}
.plan-feat{{font-size:12px;color:#6b7394;margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.plan-feat::before{{content:'✓';color:#22c55e;font-weight:700;font-size:13px}}
.btn-sub{{width:100%;padding:12px;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:12px;transition:all 0.2s}}
.btn-ind{{background:#8b5cf6;color:#fff}}.btn-ind:hover{{filter:brightness(1.15);transform:translateY(-1px)}}
.btn-org{{background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);color:#a78bfa}}.btn-org:hover{{background:rgba(139,92,246,0.25)}}
.back{{display:inline-flex;align-items:center;gap:6px;color:#6b7394;text-decoration:none;font-size:13px;margin-top:16px;text-align:center}}.back:hover{{color:#9aa2c0}}
.dash-info{{text-align:center;margin-bottom:20px;padding:12px;background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);border-radius:8px}}
.dash-info span{{font-size:24px;display:block;margin-bottom:4px}}.dash-info strong{{color:#a78bfa;font-size:14px}}
</style></head><body>
<div class="overlay"></div>
<div class="popup">
<div class="popup-hdr">
    <span class="lock-icon">🔒</span>
    <h1>This Dashboard Requires Pro Access</h1>
    <p>Upgrade to unlock all professional engineering tools</p>
</div>
<div class="dash-info"><span>{dash['icon']}</span><strong>{dash['title']}</strong><br><span style="font-size:11px;color:#6b7394">{dash.get('description','')[:80]}</span></div>
<div class="plans">
    <div class="plan featured">
        <div class="plan-name">Individual Pro</div>
        <div class="plan-price"><span class="cur">{cur}</span> {ind_price}<span class="per">/month</span></div>
        <div class="plan-detail">For individual engineers and consultants</div>
        <div class="plan-feat">All Pro dashboards included</div>
        <div class="plan-feat">Save & load sessions</div>
        <div class="plan-feat">Export to CSV</div>
        <div class="plan-feat">Priority updates</div>
        <button class="btn-sub btn-ind" onclick="subscribe('individual')">Subscribe — {cur} {ind_price}/mo</button>
    </div>
    <div class="plan">
        <div class="plan-name">Organization</div>
        <div class="plan-price"><span class="cur">{cur}</span> {org_base}<span class="per">/month</span></div>
        <div class="plan-detail">{org_users} users included · +{cur} {org_extra} per {org_extra_u} additional users</div>
        <div class="plan-feat">All Pro dashboards for team</div>
        <div class="plan-feat">Department HOD management</div>
        <div class="plan-feat">Employee access control</div>
        <div class="plan-feat">Organization dashboard</div>
        <div class="plan-feat">Dedicated support</div>
        <button class="btn-sub btn-org" onclick="subscribe('organization')">Contact Sales</button>
    </div>
</div>
<div style="text-align:center">
    <a class="back" href="/">← Back to Dashboard List</a>
    <span style="color:#252e42;margin:0 12px">|</span>
    <a class="back" href="/user">My Account</a>
</div>
</div>
<script>
function subscribe(plan){{
    if(plan==='individual'){{
        // Stripe checkout will go here when enabled
        alert('Payment integration coming soon!\\n\\nPlan: Individual Pro\\nPrice: {cur} {ind_price}/month\\n\\nContact: iambharat10@gmail.com');
    }} else {{
        alert('Organization Plan\\n\\n{org_users} users: {cur} {org_base}/month\\nAdditional {org_extra_u} users: +{cur} {org_extra}/month\\n\\nContact: iambharat10@gmail.com');
    }}
}}
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# MAIN ROUTES
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    user = get_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dashboards": DASHBOARDS,
        "user": user,
        "stripe_enabled": STRIPE_ENABLED,
        "monthly_price": MONTHLY_PRICE,
    })

@app.get("/dashboard/{dashboard_id}", response_class=HTMLResponse)
async def serve_dashboard(request: Request, dashboard_id: str):
    dash = get_dashboard_by_id(dashboard_id)
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    user = get_user(request)

    if dash["restricted"] and not user:
        request.session["redirect_after_login"] = f"/dashboard/{dashboard_id}"
        return RedirectResponse(url="/login")

    if dash["restricted"] and not has_pro_access(request):
        # Show subscription popup instead of redirect
        config = load_admin_config()
        pricing = config.get("pricing", {})
        return HTMLResponse(content=render_subscription_page(dash, user, pricing))

    file_path = BASE_DIR / "static" / "dashboards" / dash["file"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard file not found")

    html_content = file_path.read_text(encoding="utf-8")

    # Inject universal theme system into <head>
    theme_inject = """
    <link rel="stylesheet" href="/static/cc-theme.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    """

    # Inject nav bar + theme JS before </body>
    nav_and_theme = f"""
    <div id="cc-nav" style="
        position:fixed; top:0; left:0; right:0; z-index:9999;
        background:rgba(10,14,23,0.8);
        backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
        border-bottom:1px solid rgba(255,255,255,0.06);
        padding:8px 20px; display:flex; align-items:center; gap:14px;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        box-shadow:0 4px 24px rgba(0,0,0,0.3);
    ">
        <a href="/" style="
            color:#94a3b8; text-decoration:none; font-size:13px;
            display:flex; align-items:center; gap:6px;
            padding:6px 14px; border-radius:8px;
            background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.08);
            transition:all 0.2s;
        " onmouseover="this.style.background='rgba(255,255,255,0.1)';this.style.color='#e2e8f0'"
           onmouseout="this.style.background='rgba(255,255,255,0.05)';this.style.color='#94a3b8'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            Home
        </a>
        <span style="color:rgba(255,255,255,0.8); font-size:14px; font-weight:500;">{dash['title']}</span>
        {"<a href='/user' style='margin-left:auto;font-size:11px;color:rgba(255,255,255,0.5);text-decoration:none;padding:4px 10px;border-radius:6px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);'>" + user['name'] + "</a>" if user else "<a href='/login' style='margin-left:auto;font-size:11px;color:rgba(59,130,246,0.8);text-decoration:none;'>Sign in</a>"}
    </div>
    <div style="height:46px;"></div>
    <script src="/static/cc-theme.js"></script>
    """

    # Inject theme CSS in <head>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{theme_inject}</head>", 1)

    # Inject nav bar after <body>
    html_content = html_content.replace("<body>", f"<body>{nav_and_theme}", 1)

    # Inject save/autosave/print toolbar before </body>
    toolbar_inject = '<script src="/static/cc-toolbar.js"></script>'
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{toolbar_inject}</body>", 1)
    if "<body " in html_content and nav_and_theme not in html_content:
        import re
        html_content = re.sub(r"(<body[^>]*>)", rf"\1{nav_and_theme}", html_content, count=1)

    return HTMLResponse(content=html_content)


# ═══════════════════════════════════════════════════════════════
# PRICING PAGE
# ═══════════════════════════════════════════════════════════════

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    user = get_user(request)
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "user": user,
        "dashboards": DASHBOARDS,
        "monthly_price": MONTHLY_PRICE,
        "stripe_enabled": STRIPE_ENABLED,
    })


# ═══════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════

@app.get("/login")
async def login(request: Request):
    if not GOOGLE_CLIENT_ID:
        return HTMLResponse(
            "<h2 style='font-family:sans-serif;padding:40px;'>"
            "Google OAuth not configured.</h2>"
        )
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if user_info:
            request.session["user"] = {
                "name": user_info.get("name", "User"),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
            }
    except Exception as e:
        print(f"Auth error: {e}")
        return RedirectResponse(url="/")
    redirect_to = request.session.pop("redirect_after_login", "/")
    return RedirectResponse(url=redirect_to)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/api/dashboards")
async def list_dashboards(request: Request):
    user = get_user(request)
    return JSONResponse([{
        "id": d["id"], "title": d["title"], "subtitle": d["subtitle"],
        "description": d["description"], "icon": d["icon"], "category": d["category"],
        "restricted": d["restricted"], "accessible": not d["restricted"] or user is not None,
        "color": d["color"],
    } for d in DASHBOARDS])


# ═══════════════════════════════════════════════════════════════
# ADMIN PANEL (No database — uses JSON config file)
# ═══════════════════════════════════════════════════════════════

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    user = get_user(request)
    if not user:
        request.session["redirect_after_login"] = "/admin"
        return RedirectResponse(url="/login")
    if not is_admin(request):
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:40px;color:#ef4444;'>Access Denied. You are not an admin.</h2>", status_code=403)

    config = load_admin_config()
    pro_list = config.get("pro_dashboards", [])
    pricing = config.get("pricing", {})
    admin_list = config.get("admin_emails", [SUPER_ADMIN])
    free_emails = config.get("free_emails", [])
    organizations = config.get("organizations", {})

    dash_rows = ""
    for d in DASHBOARDS:
        is_pro = d["id"] in pro_list
        dash_rows += f"""<tr>
            <td style="padding:10px 14px;font-weight:500">{d['icon']} {d['title']}</td>
            <td style="padding:10px 14px">{d['category']}</td>
            <td style="padding:10px 14px;text-align:center">
                <label style="cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px">
                    <input type="checkbox" name="pro_{d['id']}" {'checked' if is_pro else ''}
                        style="width:18px;height:18px;accent-color:#8b5cf6;cursor:pointer"
                        onchange="togglePro('{d['id']}',this.checked)">
                    <span style="font-size:11px;color:{'#a78bfa' if is_pro else '#6b7394'};font-weight:600">
                        {'PRO' if is_pro else 'FREE'}
                    </span>
                </label>
            </td>
        </tr>"""

    def render_admin_row(e):
        if e.lower().strip() == SUPER_ADMIN.lower():
            badge = '<span style="color:#22c55e;font-size:10px;font-weight:700">SUPER</span>'
        else:
            badge = f'<button onclick="removeAdmin(\'{e}\')" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;padding:3px 10px;border-radius:5px;font-size:10px;cursor:pointer">Remove</button>'
        return f'<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(255,255,255,0.03);border-radius:8px;margin-bottom:6px"><span style="flex:1;font-family:monospace;font-size:13px">{e}</span>{badge}</div>'

    admin_rows = "\n".join([render_admin_row(e) for e in admin_list])

    def render_free_row(e):
        return f'<div style="display:flex;align-items:center;gap:8px;padding:6px 12px;background:rgba(34,197,94,0.04);border:1px solid rgba(34,197,94,0.1);border-radius:8px;margin-bottom:5px"><span style="flex:1;font-family:monospace;font-size:12px;color:#86efac">{e}</span><button onclick="removeFree(\'{e}\')" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#ef4444;padding:2px 8px;border-radius:4px;font-size:10px;cursor:pointer">✕</button></div>'

    free_rows = "\n".join([render_free_row(e) for e in free_emails]) if free_emails else '<div style="font-size:12px;color:#334155;font-style:italic;padding:8px">No free emails added yet</div>'

    def render_org_row(org_id, org):
        name = org.get("name", "Unnamed")
        admin_email = org.get("admin_email", "")
        members = org.get("members", [])
        hods = org.get("hods", [])
        active = org.get("active", False)
        max_u = org.get("max_users", 50)
        status_color = "#22c55e" if active else "#ef4444"
        status_text = "ACTIVE" if active else "INACTIVE"
        return f'<div style="background:rgba(139,92,246,0.04);border:1px solid rgba(139,92,246,0.15);border-radius:10px;padding:14px;margin-bottom:8px"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px"><strong style="font-size:13px">{name}</strong><div style="display:flex;gap:6px;align-items:center"><span style="font-size:10px;font-weight:700;color:{status_color};background:rgba(34,197,94,0.1) if active else rgba(239,68,68,0.1);padding:2px 8px;border-radius:4px">{status_text}</span><button onclick="removeOrg(\'{org_id}\')" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#ef4444;padding:2px 8px;border-radius:4px;font-size:10px;cursor:pointer">Delete</button></div></div><div style="font-size:11px;color:#6b7394">Admin: {admin_email} · {len(members)+len(hods)} of {max_u} users · HODs: {len(hods)}</div></div>'

    org_rows = "\n".join([render_org_row(k, v) for k, v in organizations.items()]) if organizations else '<div style="font-size:12px;color:#334155;font-style:italic;padding:8px">No organizations added yet</div>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Admin Panel — CementCalc</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0b0e14;color:#e8ecf4;font-family:'DM Sans',sans-serif;font-size:14px;min-height:100vh}}
.hdr{{background:rgba(11,14,20,0.9);border-bottom:1px solid #252e42;padding:16px 28px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100}}
.hdr h1{{font-size:18px;font-weight:700}}.hdr p{{font-size:11px;color:#6b7394}}
.main{{max-width:900px;margin:0 auto;padding:24px 28px}}
.card{{background:#111620;border:1px solid #252e42;border-radius:12px;padding:20px;margin-bottom:16px}}
.card-t{{font-size:14px;font-weight:600;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #252e42;display:flex;align-items:center;gap:8px}}
.card-t::before{{content:'';width:3px;height:16px;background:#8b5cf6;border-radius:2px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 14px;font-size:10px;color:#a78bfa;text-transform:uppercase;letter-spacing:0.8px;border-bottom:2px solid #2f3b55;background:#171d2a}}
td{{border-bottom:1px solid #252e42}}
.inp{{width:100%;padding:9px 12px;background:#0b0e14;border:1px solid #252e42;border-radius:8px;color:#e8ecf4;font-family:'JetBrains Mono',monospace;font-size:13px;outline:none}}
.inp:focus{{border-color:#8b5cf6}}
.btn{{padding:9px 20px;border-radius:8px;font-size:13px;font-weight:600;border:none;cursor:pointer;font-family:inherit}}
.btn-pri{{background:#8b5cf6;color:#fff}}.btn-pri:hover{{filter:brightness(1.1)}}
.btn-out{{background:transparent;border:1px solid #252e42;color:#9aa2c0}}.btn-out:hover{{border-color:#8b5cf6;color:#a78bfa}}
.stat{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.stat-card{{background:#171d2a;border:1px solid #252e42;border-radius:10px;padding:16px}}
.stat-card .lb{{font-size:10px;color:#9aa2c0;text-transform:uppercase;margin-bottom:4px}}
.stat-card .vl{{font-size:24px;font-weight:700;color:#a78bfa;font-family:'JetBrains Mono',monospace}}
.toast{{position:fixed;top:20px;right:20px;background:#22c55e;color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:600;display:none;z-index:9999}}
</style></head><body>
<div class="hdr">
    <a href="/" style="color:#94a3b8;text-decoration:none;font-size:13px;padding:6px 14px;border-radius:8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08)">← Home</a>
    <div><h1>Admin Panel</h1><p>Logged in as {user['email']}</p></div>
    <a href="/logout" style="margin-left:auto;color:#ef4444;font-size:12px;text-decoration:none">Logout</a>
</div>
<div class="main">
<div class="stat">
    <div class="stat-card"><div class="lb">Total Dashboards</div><div class="vl">{len(DASHBOARDS)}</div></div>
    <div class="stat-card"><div class="lb">Pro Dashboards</div><div class="vl">{len(pro_list)}</div></div>
    <div class="stat-card"><div class="lb">Free Lifetime Users</div><div class="vl">{len(free_emails)}/20</div></div>
</div>

<div class="card">
<div class="card-t">Dashboard Access Control</div>
<table><thead><tr><th>Dashboard</th><th>Category</th><th>Pro Status</th></tr></thead>
<tbody>{dash_rows}</tbody></table>
</div>

<div class="card">
<div class="card-t">Pricing</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
    <div><label style="font-size:11px;color:#9aa2c0;margin-bottom:4px;display:block">Individual Pro (/month)</label>
        <input class="inp" type="number" id="price_ind" value="{pricing.get('individual',999)}" step="1"></div>
    <div><label style="font-size:11px;color:#9aa2c0;margin-bottom:4px;display:block">Currency</label>
        <input class="inp" type="text" id="price_cur" value="{pricing.get('currency','INR')}"></div>
</div>
<div style="font-size:12px;font-weight:600;color:#a78bfa;margin:16px 0 8px">Organization Pricing</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px">
    <div><label style="font-size:10px;color:#6b7394;margin-bottom:4px;display:block">Base Price (/mo)</label>
        <input class="inp" type="number" id="org_base" value="{pricing.get('org_base',9999)}" step="1"></div>
    <div><label style="font-size:10px;color:#6b7394;margin-bottom:4px;display:block">Base Users</label>
        <input class="inp" type="number" id="org_base_u" value="{pricing.get('org_base_users',50)}" step="1"></div>
    <div><label style="font-size:10px;color:#6b7394;margin-bottom:4px;display:block">Extra Price</label>
        <input class="inp" type="number" id="org_extra" value="{pricing.get('org_extra',5000)}" step="1"></div>
    <div><label style="font-size:10px;color:#6b7394;margin-bottom:4px;display:block">Extra Users Per</label>
        <input class="inp" type="number" id="org_extra_u" value="{pricing.get('org_extra_users',25)}" step="1"></div>
</div>
<button class="btn btn-pri" style="margin-top:12px" onclick="savePricing()">Save Pricing</button>
</div>

<div class="card">
<div class="card-t">🎟️ Free Lifetime Access ({len(free_emails)}/20)</div>
<p style="font-size:12px;color:#6b7394;margin-bottom:12px">These email IDs get permanent Pro access without payment. Maximum 20.</p>
{free_rows}
<div style="display:flex;gap:8px;margin-top:10px">
    <input class="inp" type="email" id="newFree" placeholder="email@example.com" style="flex:1">
    <button class="btn btn-pri" onclick="addFree()" {'disabled style="opacity:0.4"' if len(free_emails) >= 20 else ''}>+ Add Free User</button>
</div>
</div>

<div class="card">
<div class="card-t">🏢 Organizations</div>
<p style="font-size:12px;color:#6b7394;margin-bottom:12px">Manage organization subscriptions. Org admins can add HODs, HODs can add employees.</p>
{org_rows}
<div style="background:#171d2a;border:1px solid #252e42;border-radius:10px;padding:16px;margin-top:10px">
    <div style="font-size:12px;font-weight:600;color:#a78bfa;margin-bottom:10px">Add Organization</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <input class="inp" type="text" id="newOrgName" placeholder="Organization name">
        <input class="inp" type="email" id="newOrgEmail" placeholder="Admin email">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <input class="inp" type="number" id="newOrgMaxUsers" placeholder="Max users" value="50">
        <select class="inp" id="newOrgActive" style="font-family:inherit"><option value="true">Active</option><option value="false">Inactive</option></select>
    </div>
    <button class="btn btn-pri" onclick="addOrg()">+ Create Organization</button>
</div>
</div>

<div class="card">
<div class="card-t">Admin Users</div>
<p style="font-size:12px;color:#6b7394;margin-bottom:12px">Only the Super Admin ({SUPER_ADMIN}) can add/remove admins.</p>
{admin_rows}
<div style="display:flex;gap:8px;margin-top:12px">
    <input class="inp" type="email" id="newAdmin" placeholder="email@example.com" style="flex:1">
    <button class="btn btn-pri" onclick="addAdmin()">+ Add Admin</button>
</div>
</div>
</div>

<div class="toast" id="toast"></div>

<script>
function showToast(msg){{const t=document.getElementById('toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',3000)}}
async function togglePro(id,on){{
    const r=await fetch('/admin/api/toggle-pro',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{dashboard_id:id,is_pro:on}})}});
    if(r.ok)showToast('Updated ✓');else showToast('Error!');
    setTimeout(()=>location.reload(),500);
}}
async function savePricing(){{
    const d={{individual:+document.getElementById('price_ind').value,currency:document.getElementById('price_cur').value,org_base:+document.getElementById('org_base').value,org_base_users:+document.getElementById('org_base_u').value,org_extra:+document.getElementById('org_extra').value,org_extra_users:+document.getElementById('org_extra_u').value}};
    const r=await fetch('/admin/api/pricing',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});
    if(r.ok)showToast('Pricing saved ✓');
}}
async function addFree(){{
    const email=document.getElementById('newFree').value;
    if(!email)return;
    const r=await fetch('/admin/api/free-emails',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,action:'add'}})}});
    if(r.ok){{showToast('Free user added ✓');setTimeout(()=>location.reload(),500)}}else{{const d=await r.json();showToast(d.detail||'Error')}}
}}
async function removeFree(email){{
    if(!confirm('Remove free access for '+email+'?'))return;
    const r=await fetch('/admin/api/free-emails',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,action:'remove'}})}});
    if(r.ok){{showToast('Removed');setTimeout(()=>location.reload(),500)}}
}}
async function addOrg(){{
    const name=document.getElementById('newOrgName').value;
    const email=document.getElementById('newOrgEmail').value;
    const maxUsers=+document.getElementById('newOrgMaxUsers').value||50;
    const active=document.getElementById('newOrgActive').value==='true';
    if(!name||!email){{showToast('Name and email required');return}}
    const r=await fetch('/admin/api/organizations',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name,admin_email:email,max_users:maxUsers,active,action:'add'}})}});
    if(r.ok){{showToast('Organization created ✓');setTimeout(()=>location.reload(),500)}}else{{const d=await r.json();showToast(d.detail||'Error')}}
}}
async function removeOrg(orgId){{
    if(!confirm('Delete this organization?'))return;
    const r=await fetch('/admin/api/organizations',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{org_id:orgId,action:'remove'}})}});
    if(r.ok){{showToast('Deleted');setTimeout(()=>location.reload(),500)}}
}}
async function addAdmin(){{
    const email=document.getElementById('newAdmin').value;
    if(!email)return;
    const r=await fetch('/admin/api/admins',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,action:'add'}})}});
    if(r.ok){{showToast('Admin added ✓');setTimeout(()=>location.reload(),500)}}else{{const d=await r.json();showToast(d.detail||'Error')}}
}}
async function removeAdmin(email){{
    if(!confirm('Remove '+email+'?'))return;
    const r=await fetch('/admin/api/admins',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,action:'remove'}})}});
    if(r.ok){{showToast('Removed');setTimeout(()=>location.reload(),500)}}else{{const d=await r.json();showToast(d.detail||'Error')}}
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


# ── Admin API endpoints ──

@app.post("/admin/api/toggle-pro")
async def admin_toggle_pro(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Not admin")
    data = await request.json()
    config = load_admin_config()
    pro = config.get("pro_dashboards", [])
    did = data.get("dashboard_id")
    if data.get("is_pro"):
        if did not in pro:
            pro.append(did)
    else:
        pro = [x for x in pro if x != did]
    config["pro_dashboards"] = pro
    # Also update the DASHBOARDS list in memory
    for d in DASHBOARDS:
        d["restricted"] = d["id"] in pro
    save_admin_config(config)
    return JSONResponse({"ok": True})


@app.post("/admin/api/pricing")
async def admin_set_pricing(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Not admin")
    data = await request.json()
    config = load_admin_config()
    config["pricing"] = {
        "individual": data.get("individual", 999),
        "currency": data.get("currency", "INR"),
        "org_base": data.get("org_base", 9999),
        "org_base_users": data.get("org_base_users", 50),
        "org_extra": data.get("org_extra", 5000),
        "org_extra_users": data.get("org_extra_users", 25),
    }
    save_admin_config(config)
    return JSONResponse({"ok": True})


@app.post("/admin/api/free-emails")
async def admin_manage_free_emails(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Not admin")
    data = await request.json()
    config = load_admin_config()
    free_list = config.get("free_emails", [])
    email = data.get("email", "").strip().lower()
    action = data.get("action")

    if action == "add":
        if len(free_list) >= 20:
            raise HTTPException(status_code=400, detail="Maximum 20 free emails allowed")
        if email and email not in [e.lower() for e in free_list]:
            free_list.append(email)
    elif action == "remove":
        free_list = [e for e in free_list if e.lower() != email]

    config["free_emails"] = free_list
    save_admin_config(config)
    return JSONResponse({"ok": True})


@app.post("/admin/api/organizations")
async def admin_manage_organizations(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Not admin")
    data = await request.json()
    config = load_admin_config()
    orgs = config.get("organizations", {})
    action = data.get("action")

    if action == "add":
        org_id = secrets.token_hex(6)
        orgs[org_id] = {
            "name": data.get("name", ""),
            "admin_email": data.get("admin_email", "").strip().lower(),
            "max_users": data.get("max_users", 50),
            "active": data.get("active", True),
            "hods": [],
            "members": [],
            "departments": [],
        }
    elif action == "remove":
        org_id = data.get("org_id", "")
        if org_id in orgs:
            del orgs[org_id]
    elif action == "add_hod":
        org_id = data.get("org_id", "")
        hod_email = data.get("email", "").strip().lower()
        dept = data.get("department", "")
        if org_id in orgs and hod_email:
            if hod_email not in orgs[org_id].get("hods", []):
                orgs[org_id].setdefault("hods", []).append(hod_email)
                orgs[org_id].setdefault("hod_depts", {})[hod_email] = dept
    elif action == "add_member":
        org_id = data.get("org_id", "")
        member_email = data.get("email", "").strip().lower()
        if org_id in orgs and member_email:
            total = len(orgs[org_id].get("members", [])) + len(orgs[org_id].get("hods", []))
            if total >= orgs[org_id].get("max_users", 50):
                raise HTTPException(status_code=400, detail="Organization user limit reached")
            if member_email not in orgs[org_id].get("members", []):
                orgs[org_id].setdefault("members", []).append(member_email)

    config["organizations"] = orgs
    save_admin_config(config)
    return JSONResponse({"ok": True})


@app.post("/admin/api/admins")
async def admin_manage_admins(request: Request):
    user = get_user(request)
    if not user or user.get("email", "").lower() != SUPER_ADMIN.lower():
        raise HTTPException(status_code=403, detail="Only Super Admin can manage admins")
    data = await request.json()
    config = load_admin_config()
    admins = config.get("admin_emails", [SUPER_ADMIN])
    email = data.get("email", "").strip().lower()
    action = data.get("action")

    if action == "add" and email and email not in [a.lower() for a in admins]:
        admins.append(email)
    elif action == "remove" and email != SUPER_ADMIN.lower():
        admins = [a for a in admins if a.lower() != email]
    else:
        raise HTTPException(status_code=400, detail="Cannot remove Super Admin")

    config["admin_emails"] = admins
    save_admin_config(config)
    return JSONResponse({"ok": True})


# ═══════════════════════════════════════════════════════════════
# USER DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.get("/user", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    user = get_user(request)
    if not user:
        request.session["redirect_after_login"] = "/user"
        return RedirectResponse(url="/login")

    config = load_admin_config()
    pro_list = config.get("pro_dashboards", [])
    pricing = config.get("pricing", {"individual": 10, "organization": 50, "currency": "USD"})
    user_is_admin = is_admin(request)
    user_has_pro = has_pro_access(request)
    user_email = user.get("email", "").lower()
    is_free_user = user_email in [e.lower().strip() for e in config.get("free_emails", [])]
    if user_has_pro:
        if user_is_admin:
            pro_reason = "(Admin)"
        elif is_free_user:
            pro_reason = "(Free Lifetime)"
        else:
            pro_reason = "(Organization)"
        sub_html = f'<p style="font-size:13px;color:#a78bfa">Current access: <strong style="color:#22c55e">PRO ✓</strong> {pro_reason}</p>'
    else:
        sub_html = '<p style="font-size:13px;color:#9aa2c0">Current plan: <strong style="color:#6b7394">Free</strong></p><p style="font-size:12px;color:#6b7394;margin-top:8px">Upgrade to Pro for full access to all engineering dashboards.</p><a href="/pricing" style="display:inline-block;margin-top:10px;padding:8px 20px;background:#8b5cf6;color:#fff;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600">Upgrade to Pro</a>'

    # Pre-compute dashboard list (can't use list comp inside f-string in Python 3.11)
    dash_links = ""
    for d in DASHBOARDS:
        tag_cls = "tag-pro" if d["id"] in pro_list else "tag-free"
        tag_txt = "PRO" if d["id"] in pro_list else "FREE"
        dash_links += f'<a class="dash-item" href="/dashboard/{d["id"]}"><span class="ic">{d["icon"]}</span><span class="nm">{d["title"]}</span><span class="tag {tag_cls}">{tag_txt}</span></a>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>My Dashboard — CementCalc</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0b0e14;color:#e8ecf4;font-family:'DM Sans',sans-serif;font-size:14px}}
.hdr{{background:rgba(11,14,20,0.9);border-bottom:1px solid #252e42;padding:16px 28px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100}}
.hdr h1{{font-size:18px;font-weight:700}}.hdr p{{font-size:11px;color:#6b7394}}
.main{{max-width:800px;margin:0 auto;padding:24px 28px}}
.card{{background:#111620;border:1px solid #252e42;border-radius:12px;padding:20px;margin-bottom:16px}}
.card-t{{font-size:14px;font-weight:600;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #252e42;display:flex;align-items:center;gap:8px}}
.card-t::before{{content:'';width:3px;height:16px;background:#3b82f6;border-radius:2px}}
.profile{{display:flex;align-items:center;gap:16px;margin-bottom:16px}}
.avatar{{width:60px;height:60px;border-radius:50%;border:2px solid #3b82f6}}
.badge{{padding:3px 10px;border-radius:5px;font-size:10px;font-weight:700}}
.badge-admin{{background:rgba(139,92,246,0.15);color:#a78bfa;border:1px solid rgba(139,92,246,0.3)}}
.badge-user{{background:rgba(59,130,246,0.15);color:#60a5fa;border:1px solid rgba(59,130,246,0.3)}}
.dash-list{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
.dash-item{{background:#171d2a;border:1px solid #252e42;border-radius:8px;padding:12px;display:flex;align-items:center;gap:10px;text-decoration:none;transition:border-color 0.2s}}
.dash-item:hover{{border-color:#3b82f6}}
.dash-item .ic{{font-size:20px}}.dash-item .nm{{color:#e8ecf4;font-size:12px;font-weight:500}}
.dash-item .tag{{font-size:9px;font-weight:700;padding:2px 6px;border-radius:3px;margin-left:auto}}
.tag-free{{background:rgba(34,197,94,0.15);color:#22c55e}}.tag-pro{{background:rgba(245,158,11,0.15);color:#f59e0b}}
</style></head><body>
<div class="hdr">
    <a href="/" style="color:#94a3b8;text-decoration:none;font-size:13px;padding:6px 14px;border-radius:8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08)">← Home</a>
    <div><h1>My Dashboard</h1><p>Account Settings & Access</p></div>
    {'<a href="/admin" style="margin-left:auto;color:#a78bfa;font-size:12px;text-decoration:none;padding:6px 14px;border-radius:8px;background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.2)">Admin Panel →</a>' if user_is_admin else ''}
    <a href="/logout" style="{'margin-left:auto' if not user_is_admin else 'margin-left:8px'};color:#ef4444;font-size:12px;text-decoration:none">Logout</a>
</div>
<div class="main">
<div class="card">
<div class="card-t">Profile</div>
<div class="profile">
    <img class="avatar" src="{user.get('picture','')}" alt="" onerror="this.style.display='none'">
    <div>
        <div style="font-size:16px;font-weight:600">{user['name']}</div>
        <div style="font-size:12px;color:#6b7394;margin-top:2px">{user['email']}</div>
        <span class="badge {'badge-admin' if user_is_admin else 'badge-user'}">{'Admin' if user_is_admin else 'User'}</span>
    </div>
</div>
<p style="font-size:12px;color:#6b7394">Signed in via Google. Password management is handled by Google.</p>
</div>

<div class="card">
<div class="card-t">Available Dashboards</div>
<div class="dash-list">
{dash_links}
</div>
</div>

<div class="card">
<div class="card-t">Subscription</div>
{sub_html}
</div>

<div class="card">
<div class="card-t">Saved Sessions (localStorage)</div>
<p style="font-size:12px;color:#6b7394;margin-bottom:12px">Your dashboard inputs are saved locally in your browser. Use the Save/Load buttons on each dashboard.</p>
<button onclick="clearAllSessions()" style="padding:8px 16px;border-radius:8px;font-size:12px;font-weight:600;border:1px solid rgba(239,68,68,0.3);background:rgba(239,68,68,0.1);color:#ef4444;cursor:pointer;font-family:inherit">Clear All Saved Data</button>
</div>
</div>
<script>
function clearAllSessions(){{if(!confirm('Clear all saved dashboard data?'))return;const keys=Object.keys(localStorage).filter(k=>k.startsWith('cc_'));keys.forEach(k=>localStorage.removeItem(k));alert('Cleared '+keys.length+' saved sessions.')}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


# ═══════════════════════════════════════════════════════════════
# Apply admin config on startup
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def apply_admin_config():
    config = load_admin_config()
    pro_list = config.get("pro_dashboards", [])
    for d in DASHBOARDS:
        if d["id"] in pro_list:
            d["restricted"] = True


# ═══════════════════════════════════════════════════════════════
# HOW TO ENABLE PAYMENTS (FUTURE):
# ═══════════════════════════════════════════════════════════════
# 1. Create a Stripe account at https://stripe.com
# 2. Create a product + monthly price in Stripe Dashboard
# 3. Add env vars on Render:
#      STRIPE_ENABLED=true
#      MONTHLY_PRICE=$10
# 4. Restricted dashboards will require login + active subscription
# 5. Users see a pricing page with a Subscribe button
#
# HOW TO CHANGE FREE → PAID:
#   Use the Admin Panel at /admin to toggle dashboards
# ═══════════════════════════════════════════════════════════════
