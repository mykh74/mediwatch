requires helm be installed first

postgres:
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

airflow:
```
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace -f airflow-values.yml
```