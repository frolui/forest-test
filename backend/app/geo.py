from fastapi import APIRouter, Response, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from .deps import get_session, get_current_user
from .cache_mvt import redis, TTL, get_layer_version, tile_cache_key, MVT_SQL
import hashlib

router = APIRouter(prefix="", tags=["geo"])

@router.get("/layers/")
async def get_layers(
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    sql = text("""
        SELECT
            id, name, description, created_at,
            CASE WHEN bbox IS NOT NULL THEN ST_AsGeoJSON(bbox)::jsonb ELSE NULL END AS bbox
        FROM layers
        ORDER BY id
    """)
    result = await db.execute(sql)
    rows = result.fetchall()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "created_at": r.created_at.isoformat().replace("+00:00", "Z") if r.created_at else None,
            "bbox": r.bbox,
        }
        for r in rows
    ]

@router.get("/tiles/layer/{layer_id}/{z}/{x}/{y}.mvt")
async def layer_mvt(
    layer_id: int, z: int, x: int, y: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    ver = await get_layer_version(db, layer_id)
    key = tile_cache_key(layer_id, ver, z, x, y)

    cached = await redis.get(key)
    if cached:
        etag = hashlib.md5(cached).hexdigest()
        return Response(cached, media_type="application/vnd.mapbox-vector-tile",
                        headers={"Cache-Control": f"public, max-age={TTL}", "ETag": etag})

    data = await db.scalar(MVT_SQL, {"layer_id": layer_id, "z": z, "x": x, "y": y})
    payload = bytes(data or b"")
    if payload:
        await redis.setex(key, TTL, payload)
    etag = hashlib.md5(payload).hexdigest()
    return Response(payload, media_type="application/vnd.mapbox-vector-tile",
                    headers={"Cache-Control": f"public, max-age={TTL}", "ETag": etag})
