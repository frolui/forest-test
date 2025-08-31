-- remove old and load new bd foret data in one transaction
begin;
-- insert new bd foret layer if not exists or update
insert into layers (public_id,
                    name, 
                    description,
                    owner_id,
                    copyrights,
                    created_at,
                    bbox)
values ('bd_foret_v2',
        'BD Forêt® V2',
        'La BD Forêt® version 2 a été élaborée entre 2007 et 2018 par photo-interprétation d’images en infrarouge couleurs de la BD ORTHO®. Ses principales caractéristiques sont les suivantes : une nomenclature nationale de 32 postes qui repose sur une décomposition hiérarchique des critères, distinguant par exemple les peuplements purs des principales essences forestières de la forêt hexagonale ;   un type de formation végétale attribué à chaque plage cartographiée supérieure ou égale à 0.5 ha ; Réalisée par emprises départementales, la BD Forêt® version 2 est disponible sur la totalité du territoire hexagonal.',
        (select id from users where username = 'admin'),
        '["© IGN 2024, BD Forêt® V2"]'::jsonb,
        now(),
        null::geometry(Polygon, 4326)
)on conflict (public_id, owner_id) do update
set
    description = EXCLUDED.description,
    bbox        = COALESCE(EXCLUDED.bbox, layers.bbox),
    copyrights  = COALESCE(EXCLUDED.copyrights, layers.copyrights)
where (layers.description, layers.copyrights, layers.bbox)
      is distinct from (EXCLUDED.description, EXCLUDED.copyrights, EXCLUDED.bbox);

-- remove old bd foret data
delete
from features
where layer_id in (select id from layers where public_id = 'bd_foret_v2');

-- insert new bd foret data
insert into features (layer_id, source_id, properties, updated_at, geom)
select a.id                                     as layer_id,
       k."ID"::text                             as source_id,
       jsonb_build_object('resolution', "CODE_TFV",
       	                  'tfv', "TFV",
       	                  'tfv_g11', "TFV_G11",
       	                  'essence', "ESSENCE") as properties,
       now()                                    as updated_at,
       ST_Transform(k.geometry, 4326)           as geom
from bd_foret_formation_vegetale k, 
     (select id from layers where public_id = 'bd_foret_v2') a;

update layers
set updated_at = now()
where public_id = 'bd_foret_v2';

commit;
