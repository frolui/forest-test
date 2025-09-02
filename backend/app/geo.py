from fastapi import APIRouter, Response, Depends, Request, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import text, Integer, String, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from .deps import get_session, get_current_user
from .cache_mvt import redis, TTL, get_layer_version, tile_cache_key, MVT_SQL
import hashlib

router = APIRouter(prefix="", tags=["geo"])

class GeoJSONPolygon(BaseModel):
    type: str
    coordinates: list

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

@router.get("/layers/{layer_id}")
async def get_layer(
    layer_id: int,
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    """
    Fetch details of a specific layer by its ID.
    """
    stmt = text("SELECT * FROM layers WHERE id = :id").bindparams(
        bindparam("id", type_=Integer)
    )
    res = await db.execute(stmt, {"id": layer_id})
    row = res.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Layer not found")
    return dict(row)

@router.get("/layers/{layer_id}/features")
async def get_features(
    layer_id: int,
    filter: list[str] = Query(default=[],
                              description="Repeated parameter in the format key:value"),
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    """
    Fetch features from a specific layer as GeoJSON, filtered by key-value pairs in the `properties` JSONB field.
    """
    # Parse and validate filters
    if len(filter) > 20:
        raise HTTPException(400, "Too many filters")
    pairs: list[tuple[str, str]] = []
    for f in filter:
        if ":" not in f:
            raise HTTPException(400, f"Invalid filter format: {f!r}; expected key:value")
        key, value = f.split(":", 1)
        if len(value) > 200:
            raise HTTPException(400, "Filter value too long")
        pairs.append((key, value))

    # Dynamically build WHERE clause with bind parameters
    where_clauses = ["layer_id = :layer_id"]
    params = {"layer_id": layer_id}
    bind_params = [bindparam("layer_id", type_=Integer)]

    for i, (k, v) in enumerate(pairs):
        k_name, v_name = f"k{i}", f"v{i}"
        where_clauses.append(f"properties ->> :{k_name} = :{v_name}")
        params[k_name] = k
        params[v_name] = v
        bind_params.append(bindparam(k_name, type_=String))
        bind_params.append(bindparam(v_name, type_=String))

    sql = text(f"""
        SELECT jsonb_build_object(
            'type','FeatureCollection',
            'features', COALESCE(jsonb_agg(jsonb_build_object(
                'type','Feature',
                'geometry', ST_AsGeoJSON(geom)::jsonb,
                'properties', properties
            )), '[]'::jsonb)
        ) AS geojson
        FROM features
        WHERE {' AND '.join(where_clauses)}
    """).bindparams(*bind_params)

    result = await db.scalar(sql, params)
    return result or {"type": "FeatureCollection", "features": []}

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

@router.post("/get_analysis")
async def get_analysis(
    geom: GeoJSONPolygon,
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    sql = text("""
        WITH input AS (
            SELECT ST_SetSRID(ST_GeomFromGeoJSON((:gjson)::json), 4326) AS geom
        ),
        layers_ref AS (
            SELECT
                (SELECT id FROM layers WHERE public_id = 'population_density') AS population_layer_id,
                (SELECT id FROM layers WHERE public_id = 'bd_foret_v2') AS forest_layer_id
        ),
        population AS (
            SELECT COALESCE(SUM((f.properties->>'population')::bigint), 0) AS total_population
            FROM features f
            JOIN input i ON ST_Intersects(f.geom, i.geom)
            CROSS JOIN layers_ref l
            WHERE f.layer_id = l.population_layer_id
        ),
        forest_stat AS (
            SELECT COALESCE(JSONB_OBJECT_AGG(type, area_km2), '{}'::jsonb) AS tfv_area_map
            FROM (
                SELECT
                    LOWER(f.properties->>'tfv') AS type,
                    ROUND((SUM(ST_Area(f.geom::geography)) / 1000000.0)::numeric, 3) AS area_km2
                FROM features f
                JOIN input i ON ST_Intersects(f.geom, i.geom)
                CROSS JOIN layers_ref l
                WHERE f.layer_id = l.forest_layer_id
                GROUP BY 1
            ) s
        )
        SELECT
            p.total_population,
            fs.tfv_area_map AS statistics
        FROM population p
        CROSS JOIN forest_stat fs;
    """)
    res = await db.execute(sql, {"gjson": geom.model_dump_json()})
    row = res.mappings().one()
    return {
        "total_population": int(row["total_population"] or 0),
        "statistics": row.get("statistics") or {}
    }

