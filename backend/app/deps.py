import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DB_DSN = os.getenv("DB_DSN")

engine = create_async_engine(DB_DSN, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# temporatily stub for get_current_user
async def get_current_user():
    return {"id": 1, "username": "admin"}
