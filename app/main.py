from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.db import get_db


@asynccontextmanager
async def lifespan(application: FastAPI):
    await get_db()

app = FastAPI(title='MOHospitality',
              docs_url='/',
              lifespan=lifespan,
              description='Complete hospitality solutions',
              summary='QRCode food ordering, staff management, restaurant management and more...'
              )
