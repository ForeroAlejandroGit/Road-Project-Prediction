import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.ml_utils import remove_outliers, calculate_metrics, get_bridges_structures_tunnels

def generate_synthetic_data(df_real, predictor1, predictor2, target, n_synthetic=20):
    X_real = df_real[[predictor1, predictor2]].values
    y_real = df_real[target].values
    
    np.random.seed(42)
    X_synthetic = []
    y_synthetic = []
    
    for _ in range(n_synthetic):
        idx1, idx2 = np.random.choice(len(df_real), 2, replace=False)
        alpha = np.random.beta(2, 2)
        
        x_new = alpha * X_real[idx1] + (1 - alpha) * X_real[idx2]
        x_new *= np.random.uniform(0.99, 1.01, size=2)
        
        ratio1 = x_new[0] / X_real[idx1, 0] if X_real[idx1, 0] != 0 else 1
        ratio2 = x_new[1] / X_real[idx1, 1] if X_real[idx1, 1] != 0 else 1
        y_new = y_real[idx1] * (ratio1**0.6) * (ratio2**0.4)
        y_new *= np.random.uniform(0.99, 1.01)
        
        X_synthetic.append(x_new)
        y_synthetic.append(y_new)
    
    df_synthetic = pd.DataFrame(X_synthetic, columns=[predictor1, predictor2])
    df_synthetic[target] = y_synthetic
    
    return pd.concat([df_real[[predictor1, predictor2, target]], df_synthetic], ignore_index=True)

def train_tunnel_model(df_vp: pd.DataFrame, predictors: list[str], target: str) -> dict:

    if len(predictors) != 2:
        raise ValueError("This model requires exactly 2 predictors")
    
    predictor1, predictor2 = predictors
    
    # Filter data: projects with tunnel data (non-zero target and predictors)
    df_clean = df_vp[df_vp[target] > 0][predictors + [target]].dropna()
    
    if len(df_clean) < 3:
        raise ValueError(f"Insufficient data: only {len(df_clean)} projects with tunnel data")
    
    df_augmented = generate_synthetic_data(df_clean, predictor1, predictor2, target, n_synthetic=200)
    
    X = df_augmented[[predictor1, predictor2]].copy()
    X[predictor1 + '_LOG'] = np.log1p(X[predictor1])
    X[predictor2 + '_LOG'] = np.log1p(X[predictor2])
    y = df_augmented[target].astype(float)
    
    # Create pipeline with scaling embedded (consistent with other ML scripts)
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])
    
    # Wrap with log transformation on target
    model = TransformedTargetRegressor(
        regressor=pipe,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    # Fit model on augmented data
    model.fit(X, y)
    
    # Prepare real data for evaluation
    X_real = df_clean[[predictor1, predictor2]].copy()
    X_real[predictor1 + '_LOG'] = np.log1p(X_real[predictor1])
    X_real[predictor2 + '_LOG'] = np.log1p(X_real[predictor2])
    y_real = df_clean[target].astype(float)
    
    # Predict on real data (scaling happens automatically inside pipeline)
    y_pred = model.predict(X_real)
    
    # Calculate comprehensive metrics using the centralized function
    metrics = calculate_metrics(y_real, y_pred, target)
    
    print(f"\nR² = {metrics['R²']:.4f} | MAPE = {metrics['MAPE (%)']:.2f}%")
    
    return {'X': X_real, 'y': y_real, 'y_predicted': y_pred, 'model': model, 'metrics': metrics}
    