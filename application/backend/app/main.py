from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.home import router as home_router

app = FastAPI(
    title="SmartCare API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home_router)


@app.get("/")
def root():
    return {
        "message": "SmartCare Backend Running"
    }