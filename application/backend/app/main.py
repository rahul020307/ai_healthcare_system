from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.home import router as home_router
from .api.store import router as store_router
from .api.maps import router as maps_router
from .api.chat import router as chat_router
from .api.profile import router as profile_router
from .api.medicine import router as medicine_router
from .api.db import router as db_router

app = FastAPI(
    title="CuraAssist CareHub API",
    description="HIPAA Compliant AI Healthcare Backend Platform",
    version="2.4.0"
)

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


@app.get("/")
def root():
    return {
        "status": "online",
        "system": "CuraAssist CareHub API v2.4.0",
        "docsUrl": "/docs"
    }