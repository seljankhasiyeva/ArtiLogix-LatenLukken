from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.services.db import init_db, close_db
from app.routers import forecast, dispatch, chat, analytics
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()


app = FastAPI(
    title="ArtiLogix API",
    description="Logistics Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(forecast.router, prefix="/predict", tags=["Forecast"])
app.include_router(dispatch.router, prefix="/predict", tags=["Dispatch"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ArtiLogix API"}