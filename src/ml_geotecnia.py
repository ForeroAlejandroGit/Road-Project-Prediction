import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.ml_utils import remove_outliers, calculate_metrics


def prepare_geotecnia_data(df_vp: pd.DataFrame) -> pd.DataFrame:
    df = df_vp.drop(columns=['ALCANCE', 'ZONA', 'TIPO TERRENO'])
    
    # Group by project code and sum all numeric columns
    agg_dict = {col: 'sum' for col in df.columns if col not in ['CÓDIGO']}
    df = df.groupby('CÓDIGO', as_index=False).agg(agg_dict)
    
    # Combine geology subcomponents
    df['3 - GEOLOGÍA'] = df['3.1 - GEOLOGÍA'] + df['3.2 - HIDROGEOLOGÍA']
    df = df.drop(columns=['3.1 - GEOLOGÍA', '3.2 - HIDROGEOLOGÍA'])
    
    # Filter projects with bridges and geology data
    df = df[df['3 - GEOLOGÍA'] != 0]
    df = df[df['PUENTES VEHICULARES M2'] != 0]
    
    return df


def train_geotecnia_model(df: pd.DataFrame, features: list[str], target: str = '3 - GEOLOGÍA') -> dict:

    # Remove outliers
    df_clean = remove_outliers(df[features + [target]], target=target)
    
    X = df_clean[features]
    y = df_clean[target]
    
    # Create pipeline with scaling and linear regression
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('model', LinearRegression())
    ])
    
    # Wrap with log transformation on target
    trained_model = TransformedTargetRegressor(
        regressor=pipe,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    # Cross-validation with Leave-One-Out
    loo = LeaveOneOut()
    y_pred = cross_val_predict(trained_model, X, y, cv=loo)
    
    # Calculate metrics
    metrics = calculate_metrics(y, y_pred, model_name="Linear Regression (Log y)")
    print(metrics)
    
    # Train final model on all data
    trained_model.fit(X, y)
    
    return {'X': X, 'y': y, 'y_predicted': y_pred, 'model': trained_model, 'metrics': metrics}

