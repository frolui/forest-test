FROM apache/airflow:2.9.1-python3.9

USER root
RUN apt-get update && apt-get install -y libspatialindex-dev gdal-bin libgdal-dev
USER airflow

RUN pip install geopandas psycopg2-binary sqlalchemy geoalchemy2 py7zr zarr xarray s3fs rioxarray dask dask[distributed] fsspec
RUN pip install redis 'flask-limiter[redis]'
RUN pip install kafka-python

