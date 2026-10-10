import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .db import Base, engine
from .routers import events, health, public, review


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scaffold-stage schema creation; replace with Alembic migrations before production.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="globalpeace.ai origin API", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def require_gateway_secret(request: Request, call_next):
    """Defense in depth behind the Tunnel: only the Workers gateway (which holds
    the shared secret) may call this origin. Health probes are exempt."""
    if settings.environment != "development" and request.url.path not in ("/healthz", "/readyz"):
        supplied = request.headers.get("x-gateway-secret", "")
        if not hmac.compare_digest(supplied, settings.gateway_shared_secret):
            return JSONResponse({"detail": "forbidden"}, status_code=403)
    return await call_next(request)


app.include_router(health.router)
app.include_router(events.router)
app.include_router(review.router)
app.include_router(public.router)
