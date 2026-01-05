# MediWatch - Quick Reference

## Dataset Download

```bash
# Kaggle API (recommended)
python scripts/download_data.py --verify

# Manual
# Visit: https://www.kaggle.com/datasets/brandao/diabetes
# Save to: data/raw/diabetic_data.csv
```

## Run EDA Notebook

```bash
jupyter notebook notebooks/01_eda_and_preprocessing.ipynb
```

## Automated Preprocessing

```bash
python scripts/preprocess_data.py
```

## Python API

### Load Data
```python
from mediwatch.data.load import load_diabetes_dataset

df = load_diabetes_dataset('data/raw')
print(f"Shape: {df.shape}")
```

### Preprocess (Training)
```python
from mediwatch.data.preprocess import preprocess_pipeline

split_data, artifacts = preprocess_pipeline(
    df=df,
    target_col='readmitted',
    test_size=0.2,
    artifacts_path='data/processed/artifacts.pkl'
)

X_train = split_data.train.drop('readmitted', axis=1)
y_train = split_data.train['readmitted']
```

### Preprocess (Inference)
```python
from mediwatch.data.preprocess import apply_preprocessing, PreprocessingArtifacts

# Load artifacts
artifacts = PreprocessingArtifacts.load('data/processed/artifacts.pkl')

# Apply to new data
X_new = apply_preprocessing(new_data, artifacts)
```

## File Locations

```
data/raw/diabetic_data.csv          # Raw dataset
data/processed/train.csv             # Training data
data/processed/test.csv              # Test data
data/processed/artifacts.pkl         # Preprocessing artifacts
```

## Key Features

| Feature | Description |
|---------|-------------|
| `num_diagnoses` | Count of diagnoses |
| `procedures_per_day` | Procedures / hospital days |
| `meds_per_diagnosis` | Medications / diagnoses |
| `lab_procedures_per_day` | Lab tests / hospital days |
| `age_group` | Categorical age ranges |
| `*_encoded` | Encoded categorical features |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dataset not found | Run `python scripts/download_data.py` |
| Kaggle API error | Check `~/.kaggle/kaggle.json` permissions |
| Import errors | Install: `pip install pandas numpy scikit-learn` |
| Memory issues | Use data subsampling for exploration |

## Documentation

- Full guide: [docs/DATA_PREPROCESSING_GUIDE.md](DATA_PREPROCESSING_GUIDE.md)
- Notebook setup: [notebooks/README.md](../notebooks/README.md)
- Implementation: [docs/PREPROCESSING_IMPLEMENTATION_SUMMARY.md](PREPROCESSING_IMPLEMENTATION_SUMMARY.md)
