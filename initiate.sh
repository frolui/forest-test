docker-compose down -v
docker-compose build
docker-compose run airflow-webserver airflow db init
docker-compose run airflow-webserver airflow db migrate
docker-compose run airflow-webserver airflow users create   --username admin   --password admin   --firstname Admin   --lastname Admin   --role Admin   --email admin@example.com
docker-compose run airflow-webserver airflow connections add 'postgres_default' --conn-type postgres --conn-host postgres --conn-schema airflow --conn-login airflow --conn-password airflow --conn-port 5432
docker-compose up

