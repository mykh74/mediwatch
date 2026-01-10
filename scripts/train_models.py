"""Train baseline ML models for MediWatch."""
import pandas as pd
import joblib
import os
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, precision_score, recall_score
import json

def main():
    print('='*80)
    print('MEDIWATCH MODEL TRAINING')
    print('='*80)

    print('\nLoading preprocessed data...')
    X_train = pd.read_csv('data/processed/train.csv')
    X_test = pd.read_csv('data/processed/test.csv')
    y_train = X_train.pop('readmitted')
    y_test = X_test.pop('readmitted')

    print(f'Training data shape: {X_train.shape}')
    print(f'Test data shape: {X_test.shape}')
    print(f'\nTarget distribution (Binary Classification):')
    print(f'  0 = No readmission or late readmission (>30 days)')
    print(f'  1 = Early readmission (<30 days) - TARGET')
    print(y_train.value_counts())
    print(f'\nClass balance: {y_train.value_counts(normalize=True) * 100}')

    models = {
        'Logistic_Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random_Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'Gradient_Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
    }

    print('\n' + '='*80)
    print('TRAINING 3 SCIKIT-LEARN MODELS')
    print('='*80)

    os.makedirs('models', exist_ok=True)
    results = {}

    for idx, (name, model) in enumerate(models.items(), 1):
        print(f'\n[{idx}/3] Training {name.replace("_", " ")}...')
        
        # Train
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Calculate metrics for binary classification
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='binary', pos_label=1)
        
        # ROC-AUC for binary classification
        if len(model.classes_) == 2:
            # Binary: use probability of positive class (early readmission)
            roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        else:
            # Fallback for multiclass
            y_test_bin = label_binarize(y_test, classes=model.classes_)
            roc_auc = roc_auc_score(y_test_bin, y_pred_proba, average='weighted', multi_class='ovr')
        
        # Save model
        model_path = f'models/{name}.pkl'
        joblib.dump(model, model_path)
        
        results[name] = {
            'accuracy': float(accuracy),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'model_path': model_path
        }
        
        print(f'  ✓ Accuracy:  {accuracy:.4f}')
        print(f'  ✓ F1 Score:  {f1:.4f}')
        print(f'  ✓ ROC-AUC:   {roc_auc:.4f}')
        print(f'  ✓ Saved to:  {model_path}')

    # Save results
    with open('models/training_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print('\n' + '='*80)
    print('TRAINING COMPLETE!')
    print('='*80)

    print('\nModel Performance Summary:')
    for model_name, metrics in sorted(results.items(), key=lambda x: x[1]['f1_score'], reverse=True):
        print(f'\n{model_name.replace("_", " ")}:')
        print(f'  Accuracy:  {metrics["accuracy"]:.4f}')
        print(f'  F1 Score:  {metrics["f1_score"]:.4f}')
        print(f'  ROC-AUC:   {metrics["roc_auc"]:.4f}')

    # Find best model
    best_model = max(results.items(), key=lambda x: x[1]['f1_score'])
    print(f'\n' + '='*80)
    print(f'✓ BEST MODEL: {best_model[0].replace("_", " ")}')
    print(f'  F1 Score: {best_model[1]["f1_score"]:.4f}')
    print(f'  Model saved at: {best_model[1]["model_path"]}')
    print('='*80)

    print('\nAll models saved in: ./models/')
    print('Training results saved: ./models/training_results.json')

if __name__ == '__main__':
    main()
