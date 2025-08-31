CREATE EXTENSION IF NOT EXISTS h3;
CREATE EXTENSION IF NOT EXISTS postgis_raster CASCADE;
CREATE EXTENSION IF NOT EXISTS h3_postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    id           SERIAL PRIMARY KEY,
    username     CITEXT UNIQUE NOT NULL,
    email        CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT now(),
    last_login   TIMESTAMPTZ,
    map_state    jsonb
);

DROP TABLE IF EXISTS layers CASCADE;
CREATE TABLE layers (
    id          SERIAL PRIMARY KEY,
    public_id   varchar(50) NOT NULL DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    copyrights  jsonb,
    owner_id    INTEGER REFERENCES users(id) ON DELETE SET NULL NOT NULL,
    is_default   BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    bbox        geometry(Polygon, 4326),
    UNIQUE (public_id, owner_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_layers_public_id_owner_id ON layers(public_id, owner_id);
CREATE INDEX IF NOT EXISTS idx_layers_bbox ON layers USING GIST (bbox);

DROP TABLE IF EXISTS features CASCADE;
CREATE TABLE features (
    id          SERIAL PRIMARY KEY,
    source_id   text,
    layer_id    INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
    properties  JSONB NOT NULL DEFAULT '{}'::jsonb,
    geom        geometry(Geometry, 4326) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    geom_3857   geometry(Geometry, 3857)
        GENERATED ALWAYS AS (ST_Transform(geom, 3857)) STORED,
    unique(layer_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_features_layer_id ON features(layer_id);
CREATE INDEX IF NOT EXISTS idx_features_geom ON features USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_features_geom_3857 ON features USING GIST (geom_3857);
CREATE INDEX IF NOT EXISTS idx_features_props ON features USING GIN (properties jsonb_path_ops);
