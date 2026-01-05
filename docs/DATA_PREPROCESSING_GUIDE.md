# Data Exploration and Preprocessing - Complete Guide

## Overview

This guide covers the complete data exploration and preprocessing workflow for the MediWatch project, including dataset download, exploratory data analysis (EDA), preprocessing, and feature engineering.

## Quick Start

### 1. Download the Dataset

```bash
# Using the download script
python scripts/download_data.py --verify

# Or manually download from Kaggle
# Visit: https://www.kaggle.com/datasets/brandao/diabetes
# Place CSV in: data/raw/
```

### 2. Run EDA Notebook

```bash
# Start Jupyter
jupyter notebook notebooks/01_eda_and_preprocessing.ipynb
```

### 3. Run Preprocessing Pipeline

```bash
# Automated preprocessing
python scripts/preprocess_data.py
```

## Detailed Workflow

### Phase 1: Data Acquisition

#### Option A: Kaggle API (Recommended)

1. **Install Kaggle API**:
   ```bash
   pip install kaggle
   ```

2. **Configure API Credentials**:
   ```bash
   # Get your API token from Kaggle.com → Account → API
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

3. **Download Dataset**:
   ```bash
   python scripts/download_data.py --verify
   ```

#### Option B: Manual Download

1. Visit https://www.kaggle.com/datasets/brandao/diabetes
2. Click "Download" button
3. Extract to `data/raw/diabetic_data.csv`

### Phase 2: Exploratory Data Analysis

The EDA notebook (`01_eda_and_preprocessing.ipynb`) provides comprehensive analysis:

#### 2.1 Initial Data Exploration
- Dataset shape and structure
- Data types and missing values
- Statistical summaries

#### 2.2 Missing Values Analysis
- Identify columns with missing data
- Calculate missing percentages
- Visualize missing value patterns
- Strategy: Drop columns with >50% missing, impute rest

#### 2.3 Target Variable Analysis
- Identify `readmitted` column
- Analyze class distribution
- Check for class imbalance
- Visualize distribution (bar plot, pie chart)

#### 2.4 Numerical Features Analysis
- Distribution plots (histograms)
- Box plots for outlier detection
- Statistical summaries (mean, median, std, etc.)
- Skewness and kurtosis analysis

#### 2.5 Categorical Features Analysis
- Unique value counts
- Category distributions
- High cardinality detection
- Frequency visualizations

#### 2.6 Correlation Analysis
- Correlation matrix heatmap
- Identify highly correlated features (|r| > 0.7)
- Multicollinearity detection
- Feature relationships with target

### Phase 3: Data Preprocessing

#### 3.1 Handle Special Values
```python
# Replace '?' with NaN (common in diabetes dataset)
df.replace('?', np.nan, inplace=True)

# Replace other missing indicators
special_values = ['Unknown', 'unknown', 'None', 'NA', '']
for val in special_values:
    df.replace(val, np.nan, inplace=True)
```

#### 3.2 Missing Value Imputation
- **Numerical columns**: Median imputation
- **Categorical columns**: Mode imputation
- **High missingness**: Drop columns with >50% missing

#### 3.3 Data Type Conversions
```python
# Convert string numbers to numeric
for col in df.select_dtypes(include=['object']).columns:
    try:
        df[col] = pd.to_numeric(df[col])
    except ValueError:
        pass  # Keep as categorical
```

#### 3.4 Handle Duplicates
```python
n_duplicates = df.duplicated().sum()
if n_duplicates > 0:
    df.drop_duplicates(inplace=True)
```

### Phase 4: Feature Engineering

#### 4.1 Age Groups
```python
# If age is numeric
df['age_group'] = pd.cut(
    df['age'],
    bins=[0, 18, 30, 45, 60, 75, 120],
    labels=['0-18', '19-30', '31-45', '46-60', '61-75', '76+']
)

# If age is already categorical (e.g., '[0-10)', '[10-20)')
# Keep as-is or map to broader groups
```

#### 4.2 Medical History Features
```python
# Count number of diagnoses
diag_cols = [col for col in df.columns if 'diag' in col.lower()]
df['num_diagnoses'] = df[diag_cols].notna().sum(axis=1)

# Count medication changes
med_change_cols = [col for col in df.columns if 'change' in col.lower()]
df['medication_changes'] = (df[med_change_cols] == 'Ch').sum(axis=1)
```

#### 4.3 Interaction Features
```python
# Procedures per day in hospital
df['procedures_per_day'] = df['num_procedures'] / (df['time_in_hospital'] + 1)

# Medications per diagnosis
df['meds_per_diagnosis'] = df['num_medications'] / (df['num_diagnoses'] + 1)

# Lab procedures per day
df['lab_procedures_per_day'] = df['num_lab_procedures'] / (df['time_in_hospital'] + 1)
```

#### 4.4 Categorical Encoding

**Binary Features** (2 unique values):
```python
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['feature_encoded'] = le.fit_transform(df['feature'])
```

**Low Cardinality** (≤10 unique values):
```python
# One-hot encoding
dummies = pd.get_dummies(df['feature'], prefix='feature', drop_first=True)
df = pd.concat([df, dummies], axis=1)
```

**High Cardinality** (>10 unique values):
```python
# Label encoding
le = LabelEncoder()
df['feature_encoded'] = le.fit_transform(df['feature'].astype(str))
```

### Phase 5: Feature Selection

#### 5.1 Remove Low Variance Features
```python
from sklearn.feature_selection import VarianceThreshold

selector = VarianceThreshold(threshold=0.01)
selector.fit(df[numerical_features])
low_variance_features = [
    feat for feat, var in zip(numerical_features, selector.variances_) 
    if var < 0.01
]
```

#### 5.2 Feature Importance Analysis
```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)
```

#### 5.3 Correlation-Based Selection
```python
# Remove highly correlated features (|r| > 0.9)
corr_matrix = df[numerical_features].corr().abs()
upper_triangle = corr_matrix.where(
    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
)
to_drop = [col for col in upper_triangle.columns if any(upper_triangle[col] > 0.9)]
```

### Phase 6: Data Export

#### 6.1 Save Preprocessed Data
```python
# Save to CSV
df_processed.to_csv('data/processed/processed_data.csv', index=False)

# Save train/test split
train_df.to_csv('data/processed/train.csv', index=False)
test_df.to_csv('data/processed/test.csv', index=False)
```

#### 6.2 Save Preprocessing Artifacts
```python
import pickle

# Save label encoders
with open('data/processed/label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)

# Save preprocessing artifacts
artifacts = PreprocessingArtifacts(
    label_encoders=label_encoders,
    scaler=scaler,
    feature_names=feature_cols,
    target_encoder=target_encoder,
    metadata=metadata
)
artifacts.save('data/processed/preprocessing_artifacts.pkl')
```

## Using Preprocessing Artifacts in Production

During inference, reuse the saved artifacts to ensure consistency:

```python
from mediwatch.data.preprocess import apply_preprocessing, PreprocessingArtifacts

# Load artifacts
artifacts = PreprocessingArtifacts.load('data/processed/preprocessing_artifacts.pkl')

# Apply preprocessing to new data
df_new = load_new_data()
X_new = apply_preprocessing(df_new, artifacts)

# Make predictions
predictions = model.predict(X_new)
```

## Key Considerations

### 1. Data Leakage Prevention
- **Never fit** preprocessing transformers on test/production data
- Always use saved artifacts from training
- Maintain same preprocessing pipeline for train/test/inference

### 2. Handling Unseen Categories
```python
# During inference, handle categories not seen in training
def safe_transform(le, value):
    if str(value) in le.classes_:
        return le.transform([str(value)])[0]
    else:
        return -1  # Default value for unseen categories
```

### 3. Feature Consistency
- Ensure same features in same order
- Handle missing columns gracefully
- Add missing features with default values

### 4. Reproducibility
- Set random seeds: `random_state=42`
- Version preprocessing code
- Track preprocessing parameters in metadata

## Expected Results

After completing preprocessing:

### Dataset Statistics
- **Original**: ~100,000 rows, 50+ columns
- **Processed**: ~99,000 rows (after removing duplicates)
- **Features**: 60-100 features (after engineering and encoding)
- **Train/Test Split**: 80/20

### Output Files
```
data/
├── raw/
│   └── diabetic_data.csv          (~100,000 rows, 50+ cols)
└── processed/
    ├── train.csv                   (~80,000 rows)
    ├── test.csv                    (~20,000 rows)
    ├── processed_data.csv          (full processed dataset)
    ├── label_encoders.pkl          (encoding artifacts)
    └── preprocessing_artifacts.pkl (complete artifacts)
```

### Key Features Created
1. `num_diagnoses` - Count of diagnoses
2. `procedures_per_day` - Procedures normalized by hospital stay
3. `meds_per_diagnosis` - Medication intensity
4. `lab_procedures_per_day` - Lab procedure frequency
5. Age group categories
6. Encoded categorical variables

## Troubleshooting

### Issue: High Memory Usage
**Solution**: 
- Process data in chunks
- Use `dtype` optimization
- Use `category` dtype for categorical columns

### Issue: Encoding Errors
**Solution**:
- Handle missing values before encoding
- Use `astype(str)` before LabelEncoder
- Implement fallback for unseen categories

### Issue: Feature Mismatch
**Solution**:
- Ensure consistent feature order
- Add missing features with default values
- Remove extra features not in training

### Issue: Class Imbalance
**Solution**:
- Use stratified sampling
- Consider SMOTE or undersampling
- Use class weights in model training

## Next Steps

After preprocessing:

1. **Model Development** (`notebooks/02_model_training.ipynb`)
   - Baseline models
   - Hyperparameter tuning
   - Model evaluation

2. **Experiment Tracking** (MLflow)
   - Log preprocessing parameters
   - Track experiments
   - Compare models

3. **Model Training Pipeline** (Airflow)
   - Orchestrate preprocessing
   - Automate training
   - Schedule retraining

## References

- **Dataset**: [Kaggle Diabetes Dataset](https://www.kaggle.com/datasets/brandao/diabetes)
- **Paper**: [Impact of HbA1c Measurement on Hospital Readmission Rates](https://www.hindawi.com/journals/bmri/2014/781670/)
- **Scikit-learn**: [Preprocessing Guide](https://scikit-learn.org/stable/modules/preprocessing.html)
- **Pandas**: [Data Cleaning Tutorial](https://pandas.pydata.org/docs/user_guide/missing_data.html)

## Summary

This comprehensive preprocessing workflow ensures:
- ✓ Clean, consistent data
- ✓ Proper handling of missing values
- ✓ Rich feature engineering
- ✓ Reproducible preprocessing
- ✓ Production-ready artifacts
- ✓ No data leakage

The preprocessed data is now ready for model training and evaluation!
