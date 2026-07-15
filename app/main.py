from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.services.db import init_db, close_db
from app.services.model_loader import load_models
from app.routers import forecast, dispatch, chat, analytics, drivers, admin
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_models()
    yield
    close_db()


app = FastAPI(
    title="ArtiLogix API",
    description="Logistics Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Frontend (static UI) is served from a different origin/port during local
# dev (and possibly behind nginx in prod). Without this, the browser blocks
# every fetch()/EventSource call from the UI with a CORS error before it
# even reaches these routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(forecast.router, prefix="/predict", tags=["Forecast"])
app.include_router(dispatch.router, prefix="/predict", tags=["Dispatch"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(drivers.router, prefix="/api", tags=["Drivers"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ArtiLogix API"}

# Mount Frontend static files to serve them directly from the uvicorn server
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")