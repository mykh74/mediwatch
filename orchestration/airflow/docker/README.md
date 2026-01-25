## How to use airflow
1. build docker image defined in docker-compose.yml by running `docker compose build` in the file's directory
2. start docker container defined in docker-compose.yml by running `docker compose up` in the file's directory
3. run airflow commands by running `docker exec -it docker-airflow-worker {command}` where {command} is the airflow command you wish to run
    - e.g. `docker exec -it docker-airflow-worker airflow info`
    - the container name might have additional name parts, like "docker-airflow-worker-1". to check, run docker ps after step 2 to confirm the container name
    - airflow will continue to run as long as the terminal window does
4. run any DAGs setup in airflow with the command `airflow dags trigger {dag_id}`. The hello_world_test DAG which prints "hello world" exists as an example
    - the full command for running this would therefore be `docker exec -it docker-airflow-worker airflow dags trigger hello_world_test`


### Using the airflow UI
upon setting up airflow, the UI can be accessed at http://localhost:8080/
default login credentials are
>username: airflow

>password: airflow

### Shutting down airflow
run `docker compose down` in the docker-compose.yml file's directory to shut down airflow.
Ctrl + C in the terminal running airflow will also work.