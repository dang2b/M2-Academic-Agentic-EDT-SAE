"""FastAPI entry point: builds the app and mounts the routers. Interactive docs: /docs"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import health, roles

app = FastAPI(title="SAE EDT - Groupe 3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(roles.router)
