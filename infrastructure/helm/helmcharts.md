requires helm be installed first


### helpful commands
```
# view logs
kubectl logs {container_name} -n {namespace}
#view logs for pod
kubectl describe pod {pod_name} -n {namespace}
# Quick list of container names using jsonpath
kubectl get pod airflow-scheduler-0 -n airflow -o jsonpath='{.spec.initContainers[*].name} {.spec.containers[*].name}'

```

## postgres:
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql -f postgres-values.yml

kubectl port-forward postgres-postgresql-0 5432:5432
```

test postgress runs:
```
kubectl exec -it postgres-postgresql-0 -- env PGPASSWORD=MyAppPassword123 psql -U airflow_user -d airflow_db -c "\conninfo"
```

if it fails, you need to delete the helm chart AND remove it form cache:
```
helm uninstall postgres
kubectl delete pvc data-postgres-postgresql-0
```

## airflow:

before starting airflow, you need to set the secret values to authenticate with github:
replace <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN> with your github personal access token

```
kubectl create secret generic airflow-git-credentials `
  --from-literal=GIT_SYNC_USERNAME=PeterMoras `
  --from-literal=GIT_SYNC_PASSWORD=<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN> `
  --from-literal=GITSYNC_USERNAME=PeterMoras `
  --from-literal=GITSYNC_PASSWORD=<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN> `
  -n airflow
```


```
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace -f airflow-values.yml
```

After starting airflow, connect to it by exposing port 8080, then opening localhost:8080 in your browser:
`kubectl port-forward svc/airflow-api-server 8080:8080 --namespace airflow`

default username/passsword is admin/admin

mlflow:

First, create the mlflow database in your existing postgres instance. This command takes the existing postgres server on kubernetes ad makes it create the mlflow_db database using the user credentials:
```
kubectl exec -it postgres-postgresql-0 -- env PGPASSWORD=MyAppPassword123 psql -U airflow_user -d airflow_db -c "CREATE DATABASE mlflow_db;"
```

once the database is created, install mlflow
```
helm repo add community-charts https://community-charts.github.io/helm-charts
helm install mlflow community-charts/mlflow --namespace mlflow --create-namespace -f mlflow-values.yml
```

Access MLflow UI:
```
kubectl port-forward svc/mlflow 5000:5000 --namespace mlflow

$POD_NAME=$(kubectl get pods --namespace mlflow -l "app.kubernetes.io/name=mlflow,app.kubernetes.io/instance=mlflow" -o jsonpath="{.items[0].metadata.name}")
$CONTAINER_PORT=$(kubectl get pod --namespace mlflow $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}") 
kubectl --namespace mlflow port-forward $POD_NAME 8080:$CONTAINER_PORT
```