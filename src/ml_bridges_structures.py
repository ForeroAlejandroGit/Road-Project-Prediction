import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.ml_utils import remove_outliers, calculate_metrics, get_bridges_structures_tunnels

def train_brindges_structures_model(df_vp: pd.DataFrame, target_name: str, predictors: list[str],
                                    exclude_codes: list[str] = None, use_log_transform: bool = False) -> dict:
    """
    Train linear regression model using Leave-One-Out cross-validation.
    """
    df_filtered, df_clean = get_bridges_structures_tunnels(df_vp, target_name, exclude_codes)
    
    X = df_clean[predictors].values
    y = df_clean[target_name].values
    
    # Ensure X is 2D
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    # Always remove zeros (required for MAPE calculation and log transform)
    mask_nonzero = (X.flatten() > 0) & (y > 0)
    X = X[mask_nonzero]
    y = y[mask_nonzero]
    
    # Initialize Leave-One-Out
    loo = LeaveOneOut()
    
    # Create model
    if use_log_transform:
        model = TransformedTargetRegressor(
            regressor=Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', LinearRegression())
            ]),
            func=np.log,
            inverse_func=np.exp
        )
    else:
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', LinearRegression())
        ])
    
    # LOO Cross-validation
    y_pred = np.zeros_like(y)
    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model.fit(X_train, y_train)
        y_pred[test_idx] = model.predict(X_test)
    
    metrics = calculate_metrics(y, y_pred)
    print(metrics)
    
    # Fit final model on all data
    model.fit(X, y)
    
    return {'X': X, 'y': y, 'y_predicted': y_pred,'model': model, 'metrics': metrics}
