from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.postgres_data_management import load_vector_to_postgis, run_sql_script
from shared.files_management import download_file, delete_file, unzip_gz_file
from datetime import datetime
import gzip
import os

default_args = {
    'start_date': datetime(2025, 1, 2),
}

with DAG(
    'load_lieux_data',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    download_task = PythonOperator(
        task_id='download_lieux_archive',
        python_callable=download_file,
        op_kwargs={
            'url': 'https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/departements/18/cadastre-18-lieux_dits.json.gz',
            'destination_path': '/opt/airflow/data/cadastre/cadastre-18-lieux.json.gz'
        },
        do_xcom_push=True,
    )

    unzip_task = PythonOperator(
        task_id='unzip_gz_file',
        python_callable=unzip_gz_file,
        op_kwargs={
            'source_path': "{{ ti.xcom_pull(task_ids='download_lieux_archive') }}",
            'destination_path': '/opt/airflow/data/cadastre/cadastre-18-lieux.json'
        },
        do_xcom_push=True,
    )

    load_task = PythonOperator(
        task_id="load_lieux",
        python_callable=load_vector_to_postgis,
        op_kwargs={
            "vector_path": "{{ ti.xcom_pull(task_ids='unzip_gz_file') }}",
            "table_name": "lieux",
        },
    )

    create_layer_task = PythonOperator(
        task_id='create_lieux_layer',
        python_callable=run_sql_script,
        op_kwargs={
            'script_path': '/opt/airflow/dags/cadastre/sql/create_lieux_data_layer.sql',
        },
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_files',
        python_callable=lambda paths: [delete_file(path) for path in paths],
        op_kwargs={
            "paths": [
                "{{ ti.xcom_pull(task_ids='download_lieux_archive') }}",
                "{{ ti.xcom_pull(task_ids='unzip_gz_file') }}",
            ]
        },
    )

    download_task >> unzip_task >> load_task >> create_layer_task >> cleanup_task