import os
import hashlib
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

# TTL for tiles cache in seconds (default: 1 day)
TTL = int(os.getenv("CACHE_TTL_SECONDS", "86400"))

# Redis client instance for caching tiles
redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/1"),
                       decode_responses=False)

def _b2str(b) -> str:
    return b.decode("utf-8") if isinstance(b, (bytes, bytearray)) else str(b)

async def get_layer_version(db: AsyncSession, layer_id: int) -> int:    
    k = f"layer_ver:{layer_id}"
    v = await redis.get(k)
    if v is not None:
        return int(_b2str(v))

    v = await db.scalar(
        text("""
        SELECT COALESCE(
            extract(epoch FROM updated_at), 0
        )::bigint
        FROM layers
        WHERE id = :id
        """),
        {"id": layer_id},
    )
    ver = int(v or 0)
    await redis.setex(k, 3600, str(ver).encode())  # кэшируем версию на час
    return ver

def tile_cache_key(layer_id: int, ver: int, z: int, x: int, y: int) -> str:
    return f"mvt:{layer_id}:v{ver}:{z}:{x}:{y}"

MVT_SQL = text("""
WITH b AS (
    SELECT ST_TileEnvelope(:z, :x, :y) AS g
),
s AS (
    SELECT
        l.id,
        properties,
        geom_3857
    FROM
        features l,
        b
    WHERE
        l.geom_3857 && b.g
        AND layer_id = :layer_id
),
m AS (
    SELECT
        s.id,
        s.properties,
        ST_AsMVTGeom(
            s.geom_3857,
            b.g,
            4096,
            64,
            true
        ) AS geom
    FROM
        s,
        b
    WHERE
        s.geom_3857 && b.g
)
SELECT
    ST_AsMVT(
        m,
        'layer',
        4096,
        'geom'
    )
FROM
    m;
""")