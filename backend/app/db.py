from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from .config import get_settings
import os
from urllib.parse import urlparse, parse_qs
settings = get_settings()

# Parse sslmode from DATABASE_URL if present
connect_args = {}
url = settings.DATABASE_URL
if url and 'sslmode' in url:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    sslmode = qs.get('sslmode', [None])[0]
    # Remove sslmode from URL
    base_url = url.split('?')[0]
    url = base_url
    if sslmode and sslmode != 'disable':
        import ssl
        connect_args['ssl'] = ssl.create_default_context()

engine: AsyncEngine = create_async_engine(url, echo=False, connect_args=connect_args)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=__import__('sqlalchemy.ext.asyncio').ext.asyncio.AsyncSession, expire_on_commit=False
)

def get_session():
    async def _get():
        async with AsyncSessionLocal() as session:
            yield session
    return _get()