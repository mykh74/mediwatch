# Monitoring

This folder holds monitoring and drift detection artifacts.

- `evidently/`: drift report generation scripts (placeholder)

When implemented, the monitoring job should:
- load a reference dataset (training/validation snapshot)
- load a current dataset (new batch)
- compute drift metrics (e.g., PSI, KS) across multiple columns
- emit a report/dashboard artifact
- trigger retraining when drift criteria are met


bash:
```
python monitoring/evidently/scan_drift.py \
  --reference data/processed/train.csv \
  --input data/processed/ \
  --output monitoring/reports
```
powershell:
python monitoring/evidently/scan_drift.py `
--reference data/processed/train.csv `
--input data/processed/ `
--output monitoring/reports