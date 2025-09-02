from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.postgres_data_management import load_vector_to_postgis, run_sql_script
from shared.files_management import download_file, delete_file
from datetime import datetime
import py7zr
import os
from airflow.operators.python import get_current_context


# Task: extract shapefile
def extract_shapefile_from_7z(archive_path: str, output_dir: str, target_base: str):
    shapefile_extensions = {'.shp', '.shx', '.dbf', '.prj', '.cpg'}
    os.makedirs(output_dir, exist_ok=True)

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        all_files = archive.getnames()
        shapefile_files = [
            f for f in all_files
            if f.startswith(target_base) and os.path.splitext(f)[1].lower() in shapefile_extensions
        ]
        if not shapefile_files:
            raise ValueError("Shapefile not found in archive!")
        archive.extract(path=output_dir, targets=shapefile_files)

# DAG and parameters
default_args = {
    'start_date': datetime(2025, 1, 2),
}

with DAG(
    'load_bd_foret_data',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    download_task = PythonOperator(
        task_id='download_bd_foret_archive',
        python_callable=download_file,
        op_kwargs={
            'url': 'https://data.geopf.fr/telechargement/download/BDFORET/BDFORET_2-0__SHP_LAMB93_D018_2014-04-01/BDFORET_2-0__SHP_LAMB93_D018_2014-04-01.7z',
            'destination_path': '/opt/airflow/data/BDFORET_2-0__SHP_LAMB93_D018_2014-04-01.7z'
        },
        do_xcom_push=True,
    )

    extract_task = PythonOperator(
        task_id='extract_shapefile',
        python_callable=extract_shapefile_from_7z,
        op_kwargs={
            'archive_path': "{{ ti.xcom_pull(task_ids='download_bd_foret_archive') }}",
            'output_dir': '/opt/airflow/data/extracted_shp/',
            'target_base': 'BDFORET_2-0__SHP_LAMB93_D018_2014-04-01/BDFORET/1_DONNEES_LIVRAISON/BDF_2-0_SHP_LAMB93_D018/FORMATION_VEGETALE'
        }
    )

    load_task = PythonOperator(
        task_id='load_to_postgis',
        python_callable=load_vector_to_postgis,
        op_kwargs={
            'vector_path': '/opt/airflow/data/extracted_shp/BDFORET_2-0__SHP_LAMB93_D018_2014-04-01/BDFORET/1_DONNEES_LIVRAISON/BDF_2-0_SHP_LAMB93_D018/FORMATION_VEGETALE.shp',
            'table_name': 'bd_foret_formation_vegetale'
        }
    )

    create_layer_task = PythonOperator(
        task_id='create_bd_foret_layer',
        python_callable=run_sql_script,
        op_kwargs={
            'script_path': '/opt/airflow/dags/bd_foret/sql/update_bd_foret_data.sql',
        },
    )

    hexagonize_task = PythonOperator(
        task_id='hexagonize_bd_foret_layer',
        python_callable=run_sql_script,
        op_kwargs={
            'script_path': '/opt/airflow/dags/bd_foret/sql/hexagonize_db_foret_data.sql',
        },
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_files',
        python_callable=lambda paths: [delete_file(path) for path in paths],
        op_kwargs={
            "paths": [
                "{{ ti.xcom_pull(task_ids='download_task') }}",
            ]
        },
    )

    download_task >> extract_task >> load_task >> create_layer_task >> hexagonize_task >> cleanup_task
