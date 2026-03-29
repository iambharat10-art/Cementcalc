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
    return {"pro_dashboards": [], "pricing": {"individual": 10, "organization": 50, "currency": "USD"}, "admin_emails": [SUPER_ADMIN]}

def save_admin_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def is_admin(request):
    user = get_user(request)
    if not user:
        return False
    config = load_admin_config()
    admin_list = config.get("admin_emails", [SUPER_ADMIN])
    return user.get("email", "").lower() in [e.lower().strip() for e in admin_list]

DASHBOARDS = [
    {
        "id": "belt-conveyor",
        "title": "Belt Conveyor Design",
        "subtitle": "CEMA / IS 11592 Standards",
        "description": "Complete belt conveyor design with motor sizing, idler selection, belt tension analysis, and auxiliary machinery calculations.",
        "file": "Belt_Conveyor.html",
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
        "restricted": True,
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
        "restricted": True,
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
        "restricted": True,
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
        "restricted": False,
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
        "restricted": False,
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

    if dash["restricted"] and STRIPE_ENABLED and not is_user_subscribed(request):
        return RedirectResponse(url="/pricing")

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
    pricing = config.get("pricing", {"individual": 10, "organization": 50, "currency": "USD"})
    admin_list = config.get("admin_emails", [SUPER_ADMIN])

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
    <div class="stat-card"><div class="lb">Free Dashboards</div><div class="vl">{len(DASHBOARDS)-len(pro_list)}</div></div>
</div>

<div class="card">
<div class="card-t">Dashboard Access Control</div>
<table><thead><tr><th>Dashboard</th><th>Category</th><th>Pro Status</th></tr></thead>
<tbody>{dash_rows}</tbody></table>
</div>

<div class="card">
<div class="card-t">Pricing</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
    <div><label style="font-size:11px;color:#9aa2c0;margin-bottom:4px;display:block">Individual ($/month)</label>
        <input class="inp" type="number" id="price_ind" value="{pricing.get('individual',10)}" step="1"></div>
    <div><label style="font-size:11px;color:#9aa2c0;margin-bottom:4px;display:block">Organization ($/month)</label>
        <input class="inp" type="number" id="price_org" value="{pricing.get('organization',50)}" step="1"></div>
    <div><label style="font-size:11px;color:#9aa2c0;margin-bottom:4px;display:block">Currency</label>
        <input class="inp" type="text" id="price_cur" value="{pricing.get('currency','USD')}"></div>
</div>
<button class="btn btn-pri" style="margin-top:12px" onclick="savePricing()">Save Pricing</button>
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
    const d={{individual:+document.getElementById('price_ind').value,organization:+document.getElementById('price_org').value,currency:document.getElementById('price_cur').value}};
    const r=await fetch('/admin/api/pricing',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});
    if(r.ok)showToast('Pricing saved ✓');
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
        "individual": data.get("individual", 10),
        "organization": data.get("organization", 50),
        "currency": data.get("currency", "USD"),
    }
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
{''.join(f'<a class="dash-item" href="/dashboard/{d["id"]}"><span class="ic">{d["icon"]}</span><span class="nm">{d["title"]}</span><span class="tag {"tag-pro" if d["id"] in pro_list else "tag-free"}">{"PRO" if d["id"] in pro_list else "FREE"}</span></a>' for d in DASHBOARDS)}
</div>
</div>

<div class="card">
<div class="card-t">Subscription</div>
<p style="font-size:13px;color:#9aa2c0">Current plan: <strong style="color:#22c55e">Free</strong></p>
<p style="font-size:12px;color:#6b7394;margin-top:8px">Pro plans coming soon — Individual: {pricing['currency']} {pricing['individual']}/mo | Organization: {pricing['currency']} {pricing['organization']}/mo</p>
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
