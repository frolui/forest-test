-- remove old and load new lieux data in one transaction
begin;
-- insert new lieux layer if not exists or update
insert into layers (public_id,
                    name, 
                    description,
                    owner_id,
                    copyrights,
                    created_at,
                    bbox)
values ('lieux_administrative_d18',
        'Lieux departmant 18',
        'In French, lieux means places or locations.',
        (select id from users where username = 'admin'),
        '["@ National Commission for Information Technology and Civil Liberties https://cadastre.data.gouv.fr/ 2025"]'::jsonb,
        now(),
        null::geometry(Polygon, 4326)
)on conflict (public_id, owner_id) do update
set
    description = EXCLUDED.description,
    bbox        = COALESCE(EXCLUDED.bbox, layers.bbox),
    copyrights  = COALESCE(EXCLUDED.copyrights, layers.copyrights)
where (layers.description, layers.copyrights, layers.bbox)
      is distinct from (EXCLUDED.description, EXCLUDED.copyrights, EXCLUDED.bbox);

-- remove old lieux data
delete
from features
where layer_id in (select id from layers where public_id = 'lieux_administrative_d18');

-- insert new lieux data
insert into features (layer_id, properties, created_at, updated_at, geom)
select a.id                                     as layer_id,
       jsonb_build_object('nom', nom,
                          'commune', commune) as properties,
       k.created::timestamptz                   as created_at,
       k.updated::timestamptz                   as updated_at,
       ST_Transform(k.geometry, 4326)           as geom
from lieux k, 
     (select id from layers where public_id = 'lieux_administrative_d18') a;

update layers
set updated_at = now()
where public_id = 'lieux_administrative_d18';

commit;
