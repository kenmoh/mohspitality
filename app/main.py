from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.database.db import AsyncSessionLocal
from app.config.config import redis_client

from app.routers import auth_router, qrcode_router, user_router
from app.services.profile_service import pre_create_permissions, setup_company_roles
from app.services.qrcode_service import initialize_qr_code_limits


@asynccontextmanager
async def lifespan(application: FastAPI):
    db = AsyncSessionLocal()
    try:
        await pre_create_permissions(db)
        await initialize_qr_code_limits(db)
        # await setup_company_roles(db)
        yield {"db": db, 'redis': redis_client}
    finally:
        await db.close()


app = FastAPI(
    title="MOHspitality",
    docs_url="/",
    lifespan=lifespan,
    description="Complete hospitality solutions",
    summary="QRCode food ordering, staff management, restaurant management and more...",
)
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(qrcode_router.router)
