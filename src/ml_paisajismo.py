import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.ml_utils import remove_outliers, calculate_metrics


def prepare_paisajismo_data(df_vp: pd.DataFrame) -> pd.DataFrame:

    df = df_vp[df_vp['10 - URBANISMO Y PAISAJISMO'] > 0][['CÓDIGO', 'LONGITUD KM', 'PUENTES PEATONALES UND', '10 - URBANISMO Y PAISAJISMO']]
    df = df.groupby('CÓDIGO').agg({'PUENTES PEATONALES UND': 'sum', '10 - URBANISMO Y PAISAJISMO': 'sum', 'LONGITUD KM': 'sum'}).reset_index()
    df = df[df['PUENTES PEATONALES UND'] != 0]
    
    return df


def train_paisajismo_model(df: pd.DataFrame, features: list[str], target: str = '10 - URBANISMO Y PAISAJISMO') -> dict:
    
    # Remove outliers
    df_clean = remove_outliers(df[features + [target]], target=target)
    
    X = df_clean[features]
    y = df_clean[target]
    
    # Create model without scaling (scaling causes issues with very small datasets)
    trained_model = LinearRegression()
    
    # Check if dataset is too small for cross-validation
    n_samples = len(X)
    
    if n_samples <= 2:
        # For 2 or fewer samples, just fit the model and use fitted values
        print(f"Warning: Only {n_samples} samples available. Skipping cross-validation.")
        trained_model.fit(X, y)
        y_pred = trained_model.predict(X)
    else:
        # Cross-validation with Leave-One-Out for larger datasets
        loo = LeaveOneOut()
        y_pred = cross_val_predict(trained_model, X, y, cv=loo)
        # Train final model on all data
        trained_model.fit(X, y)
    
    # Calculate metrics
    metrics = calculate_metrics(y, y_pred, model_name="Linear Regression")
    print(metrics)
    
    return {'X': X, 'y': y, 'y_predicted': y_pred, 'trained_model': trained_model}

