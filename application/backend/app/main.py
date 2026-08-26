from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.home import router as home_router
from .api.store import router as store_router
from .api.maps import router as maps_router
from .api.chat import router as chat_router
from .api.profile import router as profile_router
from .api.medicine import router as medicine_router
from .api.db import router as db_router
from .api.auth import router as auth_router
from .database.sql_db import init_db

app = FastAPI(
    title="CuraAssist CareHub API",
    description="HIPAA Compliant AI Healthcare Backend Platform",
    version="2.4.0"
)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("[Startup] SQL Database initialized and ready.")
    except Exception as e:
        print("[Startup] SQL Database init note:", e)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home_router)
app.include_router(store_router)
app.include_router(maps_router)
app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(medicine_router)
app.include_router(db_router)
app.include_router(auth_router)


from fastapi.responses import FileResponse
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
public_dir = root_dir / "public"
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/")
@app.get("/index.html")
def serve_index():
    index_file = public_dir / "index.html"
    if not index_file.exists():
        index_file = root_dir / "index.html"
    if not index_file.exists():
        index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "online",
        "system": "CuraAssist CareHub API v2.4.0",
        "docsUrl": "/docs"
    }

@app.get("/app.js")
def serve_app_js():
    f = frontend_dir / "app.js"
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    return {"detail": "Not Found"}

@app.get("/data.js")
def serve_data_js():
    f = frontend_dir / "data.js"
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    return {"detail": "Not Found"}

@app.get("/styles.css")
def serve_styles_css():
    f = public_dir / "styles.css"
    if not f.exists():
        f = root_dir / "styles.css"
    if not f.exists():
        f = frontend_dir / "styles.css"
    if f.exists():
        return FileResponse(f, media_type="text/css")
    return {"detail": "Not Found"}

@app.get("/api/status")
def api_status():
    return {
        "status": "online",
        "system": "CuraAssist CareHub API v2.4.0",
        "docsUrl": "/docs"
    }