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
values ('population_density',
        'France Population density',
        'Kontur Population dataset. Vector H3 hexagons with population counts at 400m resolution.',
        (select id from users where username = 'admin'),
        '["Wikidata. Hierarchical Administrative Subdivision codes to represent country subdivisions is available under the Creative Commons CC0 License: HASC - Wikidata", 
          "Facebook High Resolution Settlement data: Facebook Connectivity Lab and Center for International Earth Science Information Network - CIESIN - Columbia University. 2016. High Resolution Settlement Layer (HRSL). Source imagery for HRSL © 2016 DigitalGlobe. Licence - Creative Commons Attribution International", 
          "Global Human Settlement Layer: Dataset: Schiavina, Marcello; Freire, Sergio; MacManus, Kytt (2019): GHS population grid multitemporal (1975, 1990, 2000, 2015) R2019A. European Commission, Joint Research Centre (JRC) DOI: 10.2905/42E8BE89-54FF-464E-BE7B-BF9E64DA5218 PID: http://data.europa.eu/89h/0c6b9751-a71f-4062-830b-43c9f432370f Concept & Methodology: Freire, Sergio; MacManus, Kytt; Pesaresi, Martino; Doxsey-Whitfield, Erin; Mills, Jane (2016): Development of new open and free multi-temporal global population grids at 250 m resolution. Geospatial Data in a Changing World; Association of Geographic Information Laboratories in Europe (AGILE). AGILE 2016.", 
          "Copernicus Global Land Service: Land Cover 100m: Marcel Buchhorn, Bruno Smets, Luc Bertels, Bert De Roo, Myroslava Lesiv, Nandin-Erdene Tsendbazar, Martin Herold, Steffen Fritz. (2020). Copernicus Global Land Service: Land Cover 100m: collection 3: epoch 2019: Globe (Version V3.0.1) [Data set] licensed for reuse under CC BY 4.0. Zenodo.", 
          "Microsoft Buildings: (see the full list of locations in Methods). This data is licensed by Microsoft under the Open Data Commons Open Database License (ODbL).", 
          "Land Information New Zealand (LINZ) NZ Building Outlines: sourced from the LINZ Data Service licensed for reuse under CC BY 4.0.",
          "© OpenStreetMap contributors https://www.openstreetmap.org/copyright", 
          "© Kontur https://kontur.io/"]'::jsonb,
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
where layer_id in (select id from layers where public_id = 'population_density');

-- insert new bd foret data
insert into features (layer_id, source_id, properties, updated_at, geom)
select a.id                                         as layer_id,
       k.h3::text                                   as source_id,
       jsonb_build_object('population', population) as properties,
       now()                                        as updated_at,
       ST_Transform(k.geometry, 4326)               as geom
from france_population_h3 k, 
     (select id from layers where public_id = 'population_density') a;

update layers
set updated_at = now()
where public_id = 'population_density';

commit;
