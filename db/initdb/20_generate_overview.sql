drop procedure if exists generate_overviews;
create or replace procedure generate_overviews(table_h3 text,
                                               item_count text[],
                                               method text[],
                                               start_resolution integer default 8)
    language plpgsql
as
$$
declare
    res         integer := start_resolution;
    item_list   text;
    column_list text;
begin
    select string_agg(format('%1$s(%2$I)', func, col), ',')
    into item_list
    from unnest(method, item_count) t(func, col);
    select string_agg(format('%1$s', col), ',')
    into column_list
    from unnest(item_count) t(col);

    begin
        while res > 0
            loop
                execute 'insert into ' || table_h3 || ' (h3, ' || column_list || ', resolution) ' ||
                        'select h3_cell_to_parent(h3) as h3, ' || item_list || ', ' || (res - 1)::text || ' as resolution '
                            'from ' || table_h3 ||
                        ' where
                        resolution = ' || res::text || '
                             group by 1 ';
                res = res - 1;
            end loop;
    end;
end;
$$;
