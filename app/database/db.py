from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)

session = AsyncSessionLocal()


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
