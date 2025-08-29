CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO users (username, email, password_hash, is_active)
VALUES (
  'admin',
  'admin@example.com',
  crypt('AdminPass123!', gen_salt('bf', 12)),
  true
);

INSERT INTO layers (name, description)
VALUES ('Sample Layer', 'Demo features around Paris (WGS84)');

INSERT INTO features (layer_id, properties, geom)
VALUES (
  currval(pg_get_serial_sequence('layers','id')),
  jsonb_build_object('name','Zone A','kind','polygon'),
  ST_GeomFromText('POLYGON((
    2.3000 48.8500,
    2.3500 48.8500,
    2.3500 48.8800,
    2.3000 48.8800,
    2.3000 48.8500
  ))', 4326)
);

INSERT INTO features (layer_id, properties, geom)
VALUES (
  currval(pg_get_serial_sequence('layers','id')),
  jsonb_build_object('name','Zone B','kind','polygon'),
  ST_GeomFromText('POLYGON((
    2.3600 48.8550,
    2.3900 48.8550,
    2.3900 48.8750,
    2.3600 48.8750,
    2.3600 48.8550
  ))', 4326)
);

INSERT INTO features (layer_id, properties, geom)
VALUES (
  currval(pg_get_serial_sequence('layers','id')),
  jsonb_build_object('name','Trail 1','kind','line'),
  ST_GeomFromText('LINESTRING(
    2.2950 48.8600,
    2.3100 48.8650,
    2.3400 48.8600
  )', 4326)
);

INSERT INTO features (layer_id, properties, geom)
VALUES (
  currval(pg_get_serial_sequence('layers','id')),
  jsonb_build_object('name','POI 1','kind','point'),
  ST_GeomFromText('POINT(2.3330 48.8600)', 4326)
);

UPDATE layers l
SET bbox = (
  SELECT ST_Envelope(ST_Collect(f.geom))
  FROM features f
  WHERE f.layer_id = l.id
)
WHERE l.id = currval(pg_get_serial_sequence('layers','id'));

