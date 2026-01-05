# MediWatch Notebooks

This directory contains Jupyter notebooks for the MediWatch project.

## Notebooks

### 01_eda_and_preprocessing.ipynb

Comprehensive notebook covering:
- **Data Loading**: Download and load the Kaggle diabetes dataset
- **Exploratory Data Analysis (EDA)**:
  - Missing value analysis
  - Target variable distribution
  - Numerical feature distributions
  - Categorical feature analysis
  - Correlation analysis
- **Data Preprocessing**:
  - Handle special values and missing data
  - Data type conversions
  - Duplicate removal
- **Feature Engineering**:
  - Age groups
  - Medical history features
  - Interaction features
  - BMI categories (if applicable)
- **Feature Selection**:
  - Low variance removal
  - Feature importance analysis
  - Correlation-based selection
- **Data Export**: Save preprocessed data for model training

## Setup Instructions

### 1. Install Dependencies

```bash
# Install required packages
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter

# For Kaggle dataset download
pip install kaggle
```

### 2. Download the Dataset

**Option A: Using Kaggle API (Recommended)**

1. Create a Kaggle account at https://www.kaggle.com
2. Go to Account → API → Create New API Token
3. This downloads `kaggle.json`
4. Place it in `~/.kaggle/` directory:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```
5. Run in the notebook or terminal:
   ```python
   import kaggle
   kaggle.api.dataset_download_files('brandao/diabetes', path='../data/raw', unzip=True)
   ```

**Option B: Manual Download**

1. Visit https://www.kaggle.com/datasets/brandao/diabetes
2. Click "Download" button
3. Extract the CSV file to `../data/raw/` directory
4. Rename to `diabetic_data.csv` if needed

### 3. Run the Notebook

```bash
# Start Jupyter
jupyter notebook

# Or use Jupyter Lab
jupyter lab

# Open 01_eda_and_preprocessing.ipynb
```

## Dataset Information

**Source**: [Kaggle - Diabetes 130-US hospitals for years 1999-2008](https://www.kaggle.com/datasets/brandao/diabetes)

**Description**: This dataset represents 10 years (1999-2008) of clinical care at 130 US hospitals and integrated delivery networks. It includes over 50 features representing patient and hospital outcomes.

**Target Variable**: `readmitted` - Indicates whether the patient was readmitted within 30 days, after 30 days, or not readmitted.

**Key Features**:
- Patient demographics (age, gender, race)
- Medical history (diagnoses, procedures, medications)
- Hospital stay information (time in hospital, number of lab procedures)
- Medication changes
- And many more...

## Directory Structure

After running the notebook, your data directory will look like:

```
data/
├── raw/
│   └── diabetic_data.csv          # Original dataset
└── processed/
    ├── processed_data.csv          # Preprocessed dataset
    └── label_encoders.pkl          # Saved encoders for inference
```

## Expected Outputs

The notebook produces:
1. **Visualizations**: Distribution plots, correlation heatmaps, box plots
2. **Statistical summaries**: Missing value analysis, feature statistics
3. **Preprocessed data**: Clean dataset ready for modeling
4. **Artifacts**: Label encoders and transformers saved for inference

## Key Insights

The EDA notebook will help you understand:
- Class imbalance in the target variable
- Missing data patterns and handling strategies
- Feature distributions and outliers
- Feature correlations and multicollinearity
- Important features for prediction

## Next Steps

After completing this notebook:
1. Use the processed data for model training
2. Apply the saved preprocessing artifacts during inference
3. Proceed to model development and hyperparameter tuning
4. Set up MLflow experiment tracking

## Troubleshooting

### Issue: Dataset not found
- Ensure the dataset is downloaded to `../data/raw/`
- Check the filename matches what's expected in the code

### Issue: Kaggle API not working
- Verify `kaggle.json` is in `~/.kaggle/`
- Check file permissions: `chmod 600 ~/.kaggle/kaggle.json`
- Ensure you have accepted the dataset's terms on Kaggle website

### Issue: Import errors
- Install missing packages: `pip install <package-name>`
- Consider using a virtual environment

### Issue: Memory errors
- The dataset is large (~100K rows, 50+ columns)
- Consider using a subset for initial exploration
- Close other applications to free up memory

## References

- [Kaggle Dataset](https://www.kaggle.com/datasets/brandao/diabetes)
- [Dataset Paper](https://www.hindawi.com/journals/bmri/2014/781670/) - Original research paper
- [Scikit-learn Preprocessing](https://scikit-learn.org/stable/modules/preprocessing.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

Place the experimentation notebook(s) here.

Suggested naming:
- `01_experimentation.ipynb` — EDA, preprocessing, feature engineering, baseline model
- `02_hpo.ipynb` — Ray Tune HPO experiments (optional if fully scripted)

Keep results reproducible by:
- logging runs to MLflow
- saving/exporting preprocessing artifacts
