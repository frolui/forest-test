from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .config import settings

engine = create_async_engine(settings.DB_DSN, pool_size=10, max_overflow=10)
Session = async_sessionmaker(engine, expire_on_commit=False)
