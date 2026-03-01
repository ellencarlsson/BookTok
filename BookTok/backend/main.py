"""BookTok API — main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.collect import router as collect_router
from api.trending import router as trending_router

app = FastAPI(
    title="BookTok API",
    description="AI-powered community platform for BookTok book discovery",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(collect_router)
app.include_router(trending_router)
