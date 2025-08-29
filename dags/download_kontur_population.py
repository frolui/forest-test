from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import gzip
import geopandas as gpd
import sqlalchemy

def download_population_data():
    # URL of the population data
    url = "https://geodata-eu-central-1-kontur-public.s3.amazonaws.com/kontur_datasets/kontur_population_MM_20220630.gpkg.gz"
    
    # Download the file
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Save the gzipped file
    with open('/opt/airflow/data/kontur_population_MM_20220630.gpkg.gz', 'wb') as f:
        f.write(response.content)

def unzip_gz_file():
    with gzip.open('/opt/airflow/data/kontur_population_MM_20220630.gpkg.gz', 'rb') as f_in:
        with open('/opt/airflow/data/kontur_population_MM_20220630.gpkg', 'wb') as f_out:
            f_out.write(f_in.read())

def load_population_to_postgres():
    # Read the GeoPackage file using GeoPandas
    gdf = gpd.read_file('/opt/airflow/data/kontur_population_MM_20220630.gpkg')

    # Database connection string from docker-compose
    db_url = 'postgresql://airflow:airflow@postgres:5432/airflow'
    engine = sqlalchemy.create_engine(db_url)

    # Write to PostgreSQL, table 'population', geometry column 'geom'
    gdf.to_postgis('population', engine, if_exists='replace', index=False, schema='public')

default_args = {
    'start_date': datetime(2025, 1, 2),
}

with DAG(
    'download_kontur_population',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    
    download_task = PythonOperator(
        task_id='download_population_data',
        python_callable=download_population_data
    )

    unzip_task = PythonOperator(
        task_id='unzip_gz_file',
        python_callable=unzip_gz_file
    )

    load_task = PythonOperator(
        task_id='load_population_to_postgres',
        python_callable=load_population_to_postgres
    )

# Define task dependencies
    download_task >> unzip_task >> load_task