drop table if exists formation_vegetale;
create table formation_vegetale as (
    select 
        "ID" as id,
        "CODE_TFV" as code_tfv,
        "TFV" as tfv,
        "TFV_G11" as tfv_g11,
        "ESSENCE" as essence,
        st_transform(geometry, 4326) as geom
    from 
        bd_foret_formation_vegetale
);

create index formation_vegetale_gix on formation_vegetale using gist(geom);

drop table if exists formation_vegetale_h3;
create table formation_vegetale_h3 as (
    select id,
           h3
           code_tfv,
           tfv,
           tfv_g11,
           essence,
           ST_Transform(h3_cell_to_boundary_geometry(h3), 3857) as geom,
           ST_Area(h3_cell_to_boundary_geography(h3))           as area
    from (select id,
                 code_tfv,
                 tfv,
                 tfv_g11,
                 essence,
                 h3_polygon_to_cells(ST_Subdivide(geom, 5), 13) as h3
          from formation_vegetale) as foo
);