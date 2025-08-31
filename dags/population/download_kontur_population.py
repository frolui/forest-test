from airflow import DAG
from airflow.operators.python import PythonOperator
from dags.shared.postgres_data_management import load_vector_to_postgis
from dags.shared.files_management import download_file, delete_file
from datetime import datetime
import gzip
import os

# Task: unzip .gz file
def unzip_gz_file(source_path: str, destination_path: str) -> str:
    with gzip.open(source_path, 'rb') as f_in:
        with open(destination_path, 'wb') as f_out:
            f_out.write(f_in.read())
    return os.path.abspath(destination_path)

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
        python_callable=download_file,
        op_kwargs={
            'url': 'https://geodata-eu-central-1-kontur-public.s3.amazonaws.com/kontur_datasets/kontur_population_FR_20231101.gpkg.gz',
            'destination_path': '/opt/airflow/data/kontur_population_FR_20231101.gpkg.gz'
        },
        do_xcom_push=True,
    )

    unzip_task = PythonOperator(
        task_id='unzip_gz_file',
        python_callable=unzip_gz_file,
        op_kwargs={
            'source_path': "{{ ti.xcom_pull(task_ids='download_population_data') }}",
            'destination_path': '/opt/airflow/data/kontur_population_FR_20231101.gpkg'
        },
        do_xcom_push=True,
    )

    load_task = PythonOperator(
        task_id="load_population",
        python_callable=load_vector_to_postgis,
        op_kwargs={
            "vector_path": "{{ ti.xcom_pull(task_ids='unzip_gz_file') }}",
            "table_name": "france_population_h3",
        },
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_files',
        python_callable=delete_file,
        op_kwargs={
            "paths": [
                "{{ ti.xcom_pull(task_ids='download_population_data') }}",
                "{{ ti.xcom_pull(task_ids='unzip_gz_file') }}",
            ]
        },
    )

    download_task >> unzip_task >> load_task >> cleanup_task
