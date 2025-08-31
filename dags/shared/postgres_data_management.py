import geopandas as gpd
import sqlalchemy
import os

def load_vector_to_postgis(vector_path: str, table_name: str, schema: str = "public"):
    if not vector_path or not os.path.exists(vector_path):
        raise FileNotFoundError(f"Vector file not found: {vector_path}")
    gdf = gpd.read_file(vector_path)

    db_url = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
    if not db_url:
        raise RuntimeError("Database URL not found in environment")

    engine = sqlalchemy.create_engine(db_url)
    gdf.to_postgis(table_name, engine, if_exists="replace", index=False, schema=schema)