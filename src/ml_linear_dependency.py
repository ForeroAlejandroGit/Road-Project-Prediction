import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV, cross_validate, RepeatedKFold, LeaveOneOut
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_predict


from src.config import Config
import src.eda as eda
import src.present_value as present_value
from src.ml_utils import remove_outliers, calculate_metrics, analysis_plots

def train_model(df_clean: pd.DataFrame, predictor_name: list[str], target_name: str, hue_name: str = None) -> tuple[pd.DataFrame, pd.Series, pd.Series, TransformedTargetRegressor]:
    cols = predictor_name + ([hue_name] if hue_name else [])
    X = df_clean[cols].copy()
    
    for pred in predictor_name:
        X[pred + ' LOG'] = np.log1p(X[pred])
    
    y = df_clean[target_name].astype(float)
    
    num_cols = predictor_name + [pred + ' LOG' for pred in predictor_name]
    transformers = [('num', StandardScaler(), num_cols)]
    if hue_name:
        transformers.append(('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), [hue_name]))
    
    pre = ColumnTransformer(transformers)
    svr = SVR(kernel='rbf')
    pipe = Pipeline([('pre', pre), ('svr', svr)])
    model = TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)

    param_grid = {
        'regressor__svr__C': [5, 10, 80, 200, 1000],
        'regressor__svr__epsilon': [0.01],
        'regressor__svr__gamma': ['scale', 'auto', 0.01, 0.1, 1.0],
    }

    cv = RepeatedKFold(n_splits=min(5, len(y)//2), n_repeats=min(5, len(y)//2), random_state=42) if len(y) >= 10 else LeaveOneOut()
    gs = GridSearchCV(model, param_grid, scoring='neg_root_mean_squared_error', cv=cv, n_jobs=-1, refit=True)
    gs.fit(X, y)

    cv_simple = RepeatedKFold(n_splits=min(5, len(y)//2), n_repeats=1, random_state=42) if len(y) >= 10 else LeaveOneOut()
    y_oof = cross_val_predict(gs.best_estimator_, X, y, cv=cv_simple, n_jobs=-1)
    
    metrics = calculate_metrics(y, y_oof, target_name, include_rmsle=True)
    print({'R2': metrics['R²'], 'MAE': metrics['MAE'], 'RMSLE': metrics['RMSLE'], 'MAPE%': metrics['MAPE (%)']})
    
    return X, y, y_oof, gs.best_estimator_


def train_and_calculate_metrics(df: pd.DataFrame, target_columns: list[str], predictor_name: list[str], hue_name: str = None) -> dict:
    results = {}
    
    for target_name in target_columns:
        cols = predictor_name + ([hue_name] if hue_name else []) + [target_name]
        df_item = df.loc[:, cols]
        print(target_name)
        df_item_cleaned = remove_outliers(df_item, target_name) 
        X, y, y_predicted, trained_model = train_model(df_item_cleaned, predictor_name, target_name, hue_name)
        
        results[target_name] = { 'X': X, 'y': y, 'y_predicted': y_predicted,'trained_model': trained_model }
        
    return results 