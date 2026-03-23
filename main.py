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
        {"<span style='margin-left:auto;font-size:11px;color:rgba(255,255,255,0.35);'>" + user['name'] + "</span>" if user else ""}
    </div>
    <div style="height:46px;"></div>
    <script src="/static/cc-theme.js"></script>
    """

    # Inject theme CSS in <head>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{theme_inject}</head>", 1)

    # Inject nav bar after <body>
    html_content = html_content.replace("<body>", f"<body>{nav_and_theme}", 1)
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
#   Change "restricted": False  →  "restricted": True
#   in the DASHBOARDS list above. That's it!
# ═══════════════════════════════════════════════════════════════
