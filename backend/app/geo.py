from fastapi import APIRouter, Query, Response, Depends
from .db import Session
from sqlalchemy import text
from .auth import get_current_user  # защита по cookie

router = APIRouter(prefix="", tags=["geo"])

@router.get("/forest.geojson")
async def forest_geojson(bbox: str = Query(..., description="xmin,ymin,xmax,ymax (EPSG:4326)"),
                         user=Depends(get_current_user)):
    xmin, ymin, xmax, ymax = map(float, bbox.split(","))
    sql = text("""
      WITH b AS (
        SELECT ST_Transform(ST_MakeEnvelope(:xmin,:ymin,:xmax,:ymax, 4326), 3857) AS g
      )
      SELECT jsonb_build_object(
        'type','FeatureCollection',
        'features', jsonb_agg(
          jsonb_build_object(
            'type','Feature',
            'geometry', ST_AsGeoJSON(ST_Intersection(f.geom,b.g))::jsonb,
            'properties', jsonb_build_object('id', f.id, 'species', f.species)
          )
        )
      ) AS fc
      FROM bdforet f, b
      WHERE f.geom && b.g
      LIMIT 5000;
    """)
    async with Session() as s:
        r = await s.execute(sql, {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax})
        fc = r.scalar() or {"type":"FeatureCollection","features":[]}
    return fc

@router.get("/tiles/forest/{z}/{x}/{y}.mvt")
async def forest_mvt(z: int, x: int, y: int, user=Depends(get_current_user)):
    sql = text("""
      WITH bounds AS (
        SELECT ST_TileEnvelope(:z,:x,:y) AS g
      ),
      mvtgeom AS (
        SELECT
          id, species,
          ST_AsMVTGeom(f.geom, bounds.g, 4096, 64, true) AS geom
        FROM bdforet f, bounds
        WHERE f.geom && bounds.g
      )
      SELECT ST_AsMVT(mvtgeom, 'layer0', 4096, 'geom') FROM mvtgeom;
    """)
    async with Session() as s:
        r = await s.execute(sql, {"z": z, "x": x, "y": y})
        data = r.scalar()
    return Response(content=bytes(data) if data else b"", media_type="application/vnd.mapbox-vector-tile")

@router.get("/layers/")
async def get_layers(user=Depends(get_current_user)):
    sql = text("""
        SELECT
            id,
            name,
            description,
            created_at,
            CASE
                WHEN bbox IS NOT NULL THEN ST_AsGeoJSON(bbox)::jsonb
                ELSE NULL
            END AS bbox
        FROM layers
        ORDER BY id
    """)
    async with Session() as s:
        result = await s.execute(sql)
        layers = [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "created_at": row.created_at.isoformat().replace("+00:00", "Z") if row.created_at else None,
                "bbox": row.bbox
            }
            for row in result.fetchall()
        ]
    return layers

@router.get("/tiles/layer/{layer_id}/{z}/{x}/{y}.mvt")
async def layer_mvt(
    layer_id: int,
    z: int,
    x: int,
    y: int,
    user=Depends(get_current_user)
):
    sql = text("""
        WITH bounds AS (
            SELECT ST_TileEnvelope(:z, :x, :y) AS g
        ),
        mvtgeom AS (
            SELECT
                id,
                properties,
                ST_AsMVTGeom(f.geom, bounds.g, 4096, 64, true) AS geom
            FROM features f, bounds
            WHERE f.layer_id = :layer_id
              AND f.geom && bounds.g
        )
        SELECT ST_AsMVT(mvtgeom, 'layer', 4096, 'geom') FROM mvtgeom;
    """)
    async with Session() as s:
        r = await s.execute(sql, {"layer_id": layer_id, "z": z, "x": x, "y": y})
        data = r.scalar()
    return Response(content=bytes(data) if data else b"", media_type="application/vnd.mapbox-vector-tile")
