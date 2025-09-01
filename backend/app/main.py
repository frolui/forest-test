from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from app.auth import router as auth_router
from app.geo import router as geo_router

app = FastAPI(title="Forest API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(geo_router)
