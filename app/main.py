from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.db import get_db

from app.routers import auth_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    await get_db()


app = FastAPI(
    title="MOHospitality",
    docs_url="/",
    lifespan=lifespan,
    description="Complete hospitality solutions",
    summary="QRCode food ordering, staff management, restaurant management and more...",
)


app.include_router(auth_router.router)
