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