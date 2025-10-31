import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, GridSearchCV
import warnings

from src.ml_utils import remove_outliers, calculate_metrics

def train_cantidades_model(df_vp: pd.DataFrame, predictors: list[str], target: str, log_transform: str = 'none'):
    
    df = df_vp.drop(columns=['NOMBRE DEL PROYECTO', 'ALCANCE', 'ZONA', 'TIPO TERRENO'])
    agg_dict = {col: 'sum' for col in df.columns if col not in ['CÓDIGO']}
    df = df.groupby('CÓDIGO', as_index=False).agg(agg_dict)
    df = df[df[target] > 0]
    df = df.loc[:, 'LONGITUD KM':'TUNELES KM'].join(df.loc[:, [target]])
    
    df_clean = remove_outliers(df, target, method='ensemble', contamination=0.1)
    
    X = df_clean[predictors].values
    y = df_clean[target].values
    
    if log_transform in ['input', 'both']:
        X = np.log1p(X)
    
    if log_transform in ['output', 'both']:
        y_train = np.log1p(y)
    else:
        y_train = y
    
    warnings.filterwarnings('ignore', category=UserWarning)
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', Ridge())
    ])
    
    grid_search = GridSearchCV(
        pipeline, 
        {'model__alpha': [0.01, 0.1, 1.0, 10.0, 100.0]},
        cv=min(3, len(y)),
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
    
    grid_search.fit(X, y_train)
    model = grid_search.best_estimator_
    
    loo = LeaveOneOut()
    y_pred_loo = np.zeros(len(y_train))
    
    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_tr = y_train[train_idx]
        model.fit(X_train, y_tr)
        y_pred_loo[test_idx] = model.predict(X_test)
    
    if log_transform in ['output', 'both']:
        y_pred = np.expm1(y_pred_loo)
    else:
        y_pred = y_pred_loo
    
    model.fit(X, y_train)
    
    metrics = calculate_metrics(y, y_pred, model_name='Ridge')
    print(metrics)
    
    return {'X': X, 'y': y, 'y_predicted': y_pred, 'model': model, 'metrics': metrics}

