from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings


def _psycopg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg" + url[len("postgresql"):]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg" + url[len("postgresql+psycopg2"):]
    return url


_db_url = _psycopg_url(settings.DATABASE_URL)

# Async engine — FastAPI
async_engine = create_async_engine(_db_url, echo=settings.DEBUG, pool_size=20, max_overflow=40)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Sync engine — Celery tasks
engine = create_engine(_db_url, echo=settings.DEBUG, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
