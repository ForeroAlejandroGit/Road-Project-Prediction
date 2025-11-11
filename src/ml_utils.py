"""
Machine Learning Utility Functions

This module contains shared utility functions used across multiple ML notebooks
for data preprocessing, outlier detection, and model evaluation.
"""

import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression, BayesianRidge, Ridge, ElasticNet
from sklearn.svm import SVR
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, GridSearchCV
from sklearn.metrics import r2_score
import warnings

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import plotly.graph_objects as go


def remove_outliers(df: pd.DataFrame, target: str, method: str = 'ensemble', 
                   contamination: float = 0.1, voting_threshold: float = 0.5) -> pd.DataFrame:
    """
    Advanced outlier detection using multiple methods.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target : str
        Target column name
    method : str
        'ensemble' (default): Combines multiple methods with voting
        'isolation_forest': Uses Isolation Forest only
        'lof': Uses Local Outlier Factor only
        'robust_statistical': Uses Modified Z-score with MAD
        'all_strict': All methods must agree (strictest)
    contamination : float
        Expected proportion of outliers (0.05-0.2 typical)
    voting_threshold : float
        For ensemble method, fraction of methods that must flag as outlier (0.5 = majority)
    
    Returns:
    --------
    pd.DataFrame
        Cleaned dataframe without outliers
    """
    # Remove zero values first (domain-specific)
    df_nonzero = df[df[target] != 0].copy()
    
    if len(df_nonzero) < 10:
        return df_nonzero
    
    # Prepare features: numerical columns + target
    numerical_cols = df_nonzero.select_dtypes(include=[np.number]).columns.tolist()
    
    # Scale features for better outlier detection
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_nonzero[numerical_cols])
    
    # Initialize outlier flags
    outlier_flags = {}
    
    # Method 1: Isolation Forest (excellent for high-dimensional data)
    if method in ['ensemble', 'isolation_forest', 'all_strict']:
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,
            max_samples='auto',
            bootstrap=True
        )
        iso_predictions = iso_forest.fit_predict(X_scaled)
        outlier_flags['isolation_forest'] = (iso_predictions == -1)
        
    # Method 2: Local Outlier Factor (density-based, good for local anomalies)
    if method in ['ensemble', 'lof', 'all_strict']:
        n_neighbors = min(20, len(df_nonzero) - 1)
        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination
        )
        lof_predictions = lof.fit_predict(X_scaled)
        outlier_flags['lof'] = (lof_predictions == -1)
    
    # Method 3: Modified Z-score with MAD (robust to outliers themselves)
    if method in ['ensemble', 'robust_statistical', 'all_strict']:
        target_values = df_nonzero[target].values
        median = np.median(target_values)
        mad = np.median(np.abs(target_values - median))
        
        # Modified Z-score (more robust than standard Z-score)
        if mad != 0:
            modified_z_scores = 0.6745 * (target_values - median) / mad
            # Threshold of 3.5 is standard for modified Z-score
            outlier_flags['robust_statistical'] = np.abs(modified_z_scores) > 3.5
        else:
            outlier_flags['robust_statistical'] = np.zeros(len(df_nonzero), dtype=bool)
    
    # Method 4: Multivariate Z-score on target (additional check)
    if method in ['ensemble', 'all_strict']:
        target_scaled = scaler.fit_transform(df_nonzero[[target]])
        outlier_flags['z_score'] = np.abs(target_scaled.flatten()) > 3
    
    # Combine methods based on selected strategy
    if method == 'ensemble':
        # Voting: flag as outlier if voting_threshold fraction of methods agree
        outlier_matrix = np.column_stack(list(outlier_flags.values()))
        votes = outlier_matrix.sum(axis=1)
        is_outlier = votes >= (len(outlier_flags) * voting_threshold)
        
    elif method == 'all_strict':
        # All methods must agree (most conservative)
        outlier_matrix = np.column_stack(list(outlier_flags.values()))
        is_outlier = outlier_matrix.all(axis=1)
        
    elif method in ['isolation_forest', 'lof', 'robust_statistical']:
        # Single method
        is_outlier = outlier_flags[method]
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Filter out outliers
    df_clean = df_nonzero[~is_outlier].copy()
    return df_clean


def calculate_metrics(y_true, y_pred, model_name: str = "Model", include_rmsle: bool = False) -> dict:
    """
    Calculate and return comprehensive regression metrics.
    
    Parameters:
    -----------
    y_true : array-like
        True target values
    y_pred : array-like
        Predicted target values
    model_name : str
        Name of the model for identification in results
    include_rmsle : bool
        If True, also calculate RMSLE (Root Mean Squared Log Error).
        Useful for data with exponential growth patterns.
    
    Returns:
    --------
    dict
        Dictionary containing comprehensive regression metrics:
        - Model: Model name
        - R²: R-squared score
        - MAE: Mean Absolute Error
        - RMSE: Root Mean Squared Error
        - RMSLE: Root Mean Squared Log Error (only if include_rmsle=True)
        - MAPE (%): Mean Absolute Percentage Error
        - Median AE: Median Absolute Error
        - Max Error: Maximum absolute error
    """
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    # Additional metrics
    median_ae = np.median(np.abs(y_true - y_pred))
    max_error = np.max(np.abs(y_true - y_pred))
    
    metrics = {
        'Model': model_name,
        'R²': round(float(r2), 3),
        'MAE': round(float(mae), 3),
        'RMSE': round(float(rmse), 3),
        'MAPE (%)': round(float(mape), 3),
        'Median AE': round(float(median_ae), 3),
        'Max Error': round(float(max_error), 3)
    }
    
    # Add RMSLE if requested (useful for exponential/log-scale predictions)
    if include_rmsle:
        rmsle = np.sqrt(np.mean((np.log1p(y_pred) - np.log1p(y_true))**2))
        metrics['RMSLE'] = round(float(rmsle), 3)
    
    return metrics

def train_multiple_models(df_vp: pd.DataFrame, predictors: list[str], target: str, log_transform: str = 'none', 
                          apply_outlier_removal: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray, Pipeline, dict]:
    """
    Train multiple regression models and return the best one based on R² and MAPE.
    
    Parameters:
    -----------
    df_vp : pd.DataFrame
        Input dataframe
    predictors : list[str]
        List of predictor column names
    target : str
        Target column name
    log_transform : str
        Type of log transformation: 'none', 'input', 'output', or 'both'
    apply_outlier_removal : bool
        Whether to apply outlier removal (default: True)
    
    Returns:
    --------
    tuple containing:
        - X : np.ndarray
            Feature matrix (transformed if log_transform='input' or 'both')
        - y : np.ndarray
            Target values (original scale)
        - y_predicted : np.ndarray
            Predicted values from best model (original scale)
        - best_model : Pipeline
            Best trained model pipeline
        - metrics : dict
            Performance metrics for the best model
    """
    
    df_vp = df_vp[df_vp[target] > 0].copy()
    
    if apply_outlier_removal:
        df_clean = remove_outliers(df_vp, target, method='ensemble', contamination=0.1)
    else:
        df_clean = df_vp
    
    X = df_clean[predictors].values
    y = df_clean[target].values
    
    if log_transform in ['input', 'both']:
        X = np.log1p(X)
    
    if log_transform in ['output', 'both']:
        y_train = np.log1p(y)
    else:
        y_train = y
    
    warnings.filterwarnings('ignore', category=UserWarning)
    
    model_configs = {
        'Bayesian Ridge': {
            'model': BayesianRidge(),
            'params': {
                'model__alpha_1': [1e-6, 1e-5, 1e-4],
                'model__alpha_2': [1e-6, 1e-5, 1e-4],
                'model__lambda_1': [1e-6, 1e-5, 1e-4],
                'model__lambda_2': [1e-6, 1e-5, 1e-4]
            }
        },
        'Ridge': {
            'model': Ridge(),
            'params': {
                'model__alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
            }
        },
        'ElasticNet': {
            'model': ElasticNet(max_iter=10000),
            'params': {
                'model__alpha': [0.01, 0.1, 1.0, 10.0],
                'model__l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]
            }
        },
        'SVR': {
            'model': SVR(kernel='rbf'),
            'params': {
                'model__C': [0.1, 1.0, 10.0, 100.0],
                'model__epsilon': [0.01, 0.1, 0.5],
                'model__gamma': ['scale', 'auto']
            }
        },
        'Gaussian Process': {
            'model': GaussianProcessRegressor(
                kernel=C(1.0, (1e-3, 1e6)) * RBF(1.0, (1e-6, 1e3)),
                random_state=42,
                n_restarts_optimizer=5
            ),
            'params': {}
        }
    }
    
    loo = LeaveOneOut()
    all_results = []
    all_models = {}
    all_predictions = {}
    
    for name, config in model_configs.items():
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', config['model'])
        ])
        
        if config['params']:
            grid_search = GridSearchCV(
                pipeline, 
                config['params'], 
                cv=min(3, len(y)),
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            grid_search.fit(X, y_train)
            best_pipeline = grid_search.best_estimator_
        else:
            best_pipeline = pipeline
        
        y_pred_loo = np.zeros(len(y_train))
        
        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_tr, y_te = y_train[train_idx], y_train[test_idx]
            best_pipeline.fit(X_train, y_tr)
            y_pred_loo[test_idx] = best_pipeline.predict(X_test)
        
        if log_transform in ['output', 'both']:
            y_pred_original = np.expm1(y_pred_loo)
        else:
            y_pred_original = y_pred_loo
        
        # Store model and predictions
        all_models[name] = best_pipeline
        all_predictions[name] = y_pred_original
        
        metrics = calculate_metrics(y, y_pred_original, model_name=name)
        all_results.append(metrics)
    
    results_df = pd.DataFrame(all_results).sort_values('R²', ascending=False)
    results_df_sorted = results_df.sort_values(by=['R²', 'MAPE (%)'], ascending=[False, True])
    best_model_name = results_df_sorted.iloc[0]['Model']
    best_model = all_models[best_model_name]
    y_predicted = all_predictions[best_model_name]
    best_metrics = results_df_sorted.iloc[0].to_dict()
    return X, y, y_predicted, best_model, best_metrics


def create_scatter_plot_with_regression(df: pd.DataFrame, predictor_name: str, target_name: str, hue_name: str = 'ALCANCE', 
                                         df_raw: pd.DataFrame = None, title: str = None) -> go.Figure:
    """
    Create interactive scatter plot with regression line and R² value, colored by hue.
    Includes tooltips with project information on hover.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data to plot
    predictor_name : str
        Name of predictor variable (x-axis)
    target_name : str
        Name of target variable (y-axis)
    hue_name : str
        Name of categorical variable for color coding
    df_raw : pd.DataFrame, optional
        Raw dataframe with project codes and names for enhanced hover information
    title : str, optional
        Plot title (auto-generated if None)
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Plotly figure with scatter plot and regression line
    """
    from scipy.stats import linregress
    
    # Color map for different project types
    colors_map = {
        'Segunda calzada': '#1f77b4',
        'operacion y mantenimiento': '#ff7f0e', 
        'Mejoramiento': '#2ca02c',
        'Rehabilitación': '#d62728',
        'Nuevo': '#9467bd',
        'Construcción': '#8c564b',
        'Puesta a punto': '#e377c2'
    }
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter points colored by category
    for category in sorted(df[hue_name].unique()):
        mask = df[hue_name] == category
        df_category = df[mask]
        
        # Create hover text with project information
        hover_text = []
        for idx in df_category.index:
            hover = f"<b>{hue_name}:</b> {category}<br>"
            
            # Try to add project code and name from df_raw if available
            if df_raw is not None and idx in df_raw.index:
                if 'CÓDIGO DEL PROYECTO' in df_raw.columns:
                    hover += f"<b>Código:</b> {df_raw.loc[idx, 'CÓDIGO DEL PROYECTO']}<br>"
                if 'NOMBRE DEL PROYECTO' in df_raw.columns:
                    hover += f"<b>Nombre:</b> {df_raw.loc[idx, 'NOMBRE DEL PROYECTO']}<br>"
            
            # Add project code from df if available
            if 'CÓDIGO' in df.columns and idx in df.index:
                hover += f"<b>Código:</b> {df.loc[idx, 'CÓDIGO']}<br>"
            
            # Add predictor and target values
            if predictor_name in df.columns:
                hover += f"<b>{predictor_name}:</b> {df.loc[idx, predictor_name]:.2f}<br>"
            if target_name in df.columns:
                hover += f"<b>{target_name}:</b> ${df.loc[idx, target_name]:,.0f}"
            
            hover_text.append(hover)
        
        fig.add_trace(go.Scatter(
            x=df_category[predictor_name],
            y=df_category[target_name],
            mode='markers',
            name=category,
            marker=dict(
                size=12,
                color=colors_map.get(category, '#7f7f7f'),
                opacity=0.8,
                line=dict(width=1, color='DarkSlateGrey')
            ),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text
        ))
    
    # Calculate and plot overall regression line
    slope, intercept, r_value, p_value, _ = linregress(df[predictor_name], df[target_name])
    x_line = np.linspace(df[predictor_name].min(), df[predictor_name].max(), 100)
    y_line = slope * x_line + intercept
    
    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        name=f'Overall R²={r_value**2:.3f}',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout
    if title is None:
        title = f'{predictor_name} vs {target_name} by {hue_name}'
    
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, family='Arial')
        ),
        xaxis=dict(
            title=dict(
                text=f'<b>{predictor_name}</b>',
                font=dict(size=13)
            ),
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=0.5
        ),
        yaxis=dict(
            title=dict(
                text=f'<b>{target_name}</b>',
                font=dict(size=13)
            ),
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=0.5
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="lightgray",
            borderwidth=1
        ),
        width=1000,
        height=600
    )
    
    return fig


def get_bridges_structures_tunnels(df_vp, target_name, exclude_codes=None, contamination=0.1):
    """
    Get and clean bridges, structures, and tunnels data for a specific target variable.
    Groups data by project code and filters for projects with relevant infrastructure.
    
    Parameters:
    -----------
    df_vp : pd.DataFrame
        Input dataframe with project data
    target_name : str
        Name of the target column to predict
    exclude_codes : list, optional
        List of project codes to exclude from analysis
    contamination : float
        Expected proportion of outliers for outlier detection (default: 0.1)
    
    Returns:
    --------
    tuple[pd.DataFrame, pd.DataFrame]
        - df_filtered: Filtered dataframe before outlier removal
        - df_clean: Cleaned dataframe after outlier removal
    """
    # Select relevant columns
    df = df_vp.loc[:, 'CÓDIGO':'ALCANCE'].join(df_vp.loc[:, [target_name]])
    
    # Group by project code
    bridges_structures_tunnels_cols = [
        'PUENTES VEHICULARES UND', 
        'PUENTES VEHICULARES M2', 
        'PUENTES PEATONALES UND',
        'PUENTES PEATONALES M2',
        'TUNELES UND',
        'TUNELES KM'
    ]
    
    agg_dict = {
        'ALCANCE': 'first',
        target_name: 'sum'
    }
    # Add aggregation for all infrastructure columns
    for col in bridges_structures_tunnels_cols:
        agg_dict[col] = 'sum'
    
    df_grouped = df.groupby('CÓDIGO').agg(agg_dict).reset_index()
    
    # Filter: projects with bridges/structures/tunnels and positive target values
    df_filtered = df_grouped[
        (df_grouped[bridges_structures_tunnels_cols].sum(axis=1) > 0) & 
        (df_grouped[target_name] > 0)
    ]
    
    # Exclude specific codes if provided
    if exclude_codes:
        df_filtered = df_filtered[~df_filtered['CÓDIGO'].isin(exclude_codes)]
    
    # Remove outliers
    df_clean = remove_outliers(df_filtered, target_name, contamination=contamination)
    
    return df_filtered, df_clean


def predicted_plot(y: np.array, y_predicted: np.array, df_item_cleaned: pd.DataFrame, 
                   predictor_name: str, target_name: str, hue_name: str, df_raw: pd.DataFrame = None) -> go.Figure:
    """
    Creates beautiful executive Plotly visualizations for model analysis.
    
    Parameters:
    -----------
    y : array-like
        Actual values
    y_predicted : array-like
        Predicted values
    df_item_cleaned : pd.DataFrame
        Cleaned dataframe with all project data
    predictor_name : str
        Name of the predictor column (e.g., 'LONGITUD KM', 'PUENTES VEHICULARES M2')
    target_name : str
        Name of the target column (e.g., '5 - TALUDES', '4 - SUELOS')
    hue_name : str
        Name of the hue column (e.g., 'ALCANCE')
    df_raw : pd.DataFrame, optional
        Raw dataframe with project codes and names for enhanced hover information
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Plotly figure showing actual vs predicted values
    """
    # Color map for different project types
    colors_map = {
        'Segunda calzada': '#1f77b4',
        'operacion y mantenimiento': '#ff7f0e', 
        'Mejoramiento': '#2ca02c',
        'Rehabilitación': '#d62728',
        'Nuevo': '#9467bd',
        'Construcción': '#8c564b',
        'Puesta a punto': '#e377c2'
    }
    
    # Convert y and y_predicted to pandas Series if they aren't already
    if not isinstance(y, pd.Series):
        y = pd.Series(y, index=df_item_cleaned.index)
    if not isinstance(y_predicted, pd.Series):
        y_predicted = pd.Series(y_predicted, index=df_item_cleaned.index)
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter points colored by category
    for category in sorted(df_item_cleaned[hue_name].unique()):
        mask = df_item_cleaned[hue_name] == category
        indices = df_item_cleaned[mask].index
        y_actual = y[mask]
        y_pred = y_predicted[mask]
        
        # Create hover text with project information
        hover_text = []
        for idx in indices:
            hover = f"<b>{hue_name}:</b> {category}<br>"
            
            # Try to add project code and name from df_raw if available
            if df_raw is not None and idx in df_raw.index:
                if 'CÓDIGO' in df_raw.columns:
                    hover += f"<b>Código:</b> {df_raw.loc[idx, 'CÓDIGO']}<br>"
                if 'NOMBRE DEL PROYECTO' in df_raw.columns:
                    hover += f"<b>Nombre:</b> {df_raw.loc[idx, 'NOMBRE DEL PROYECTO']}<br>"
            
            # Add project code from df_item_cleaned if available
            if 'CÓDIGO' in df_item_cleaned.columns and idx in df_item_cleaned.index:
                hover += f"<b>Código:</b> {df_item_cleaned.loc[idx, 'CÓDIGO']}<br>"
            
            # Add predictor value
            if predictor_name in df_item_cleaned.columns:
                hover += f"<b>{predictor_name}:</b> {df_item_cleaned.loc[idx, predictor_name]:.2f}<br>"
            
            # Add actual and predicted values
            hover += f"<b>Valor Real:</b> ${y_actual.loc[idx]:,.0f}<br>"
            hover += f"<b>Predicción:</b> ${y_pred.loc[idx]:,.0f}"
            
            hover_text.append(hover)
        
        fig.add_trace(go.Scatter(
            x=y_actual,
            y=y_pred,
            mode='markers',
            name=category,
            marker=dict(
                size=12,
                color=colors_map.get(category, '#7f7f7f'),
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text
        ))
    
    # Add perfect prediction line
    min_val = min(y.min(), y_predicted.min())
    max_val = max(y.max(), y_predicted.max())
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        name='Predicción Perfecta',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=True
    ))
    
    # Update layout for executive look
    fig.update_layout(
        title=dict(
            text=f'<b>Predicción vs Realidad - {target_name}</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=20, family='Arial Black')
        ),
        xaxis=dict(
            title=dict(
                text='<b>Valor Real ($)</b>',
                font=dict(size=14)
            ),
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=0.5
        ),
        yaxis=dict(
            title=dict(
                text='<b>Valor Predicho ($)</b>',
                font=dict(size=14)
            ),
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=0.5
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="lightgray",
            borderwidth=1
        ),
        width=900,
        height=600
    )
    
    return fig


def train_models_by_alcance_and_transform(df_vp: pd.DataFrame, predictors: list[str], target: str, 
                                       hue_name: str = 'ALCANCE', min_samples: int = 3) -> dict:
    """
    Train models for each hue category, testing all log transformations and returning THE best model.
    
    Parameters:
    -----------
    df_vp : pd.DataFrame
        Input dataframe
    predictors : list[str]
        List of predictor column names
    target : str
        Target column name
    hue_name : str
        Column name to group by (default: 'ALCANCE')
    min_samples : int
        Minimum samples required per category (default: 5)
    
    Returns:
    --------
    dict
        {hue_value: {'X', 'y', 'y_predicted', 'model', 'metrics', 'log_transform', 'n_samples'}}
        Returns None for categories with insufficient data
    """
    results = {}
    log_transforms = ['none', 'input', 'output', 'both']
    df = df_vp[df_vp[target] > 0]
    
    for hue_value in df[hue_name].unique():
        df_hue = df[df[hue_name] == hue_value]
        
        # Check columns exist
        required_cols = predictors + [target]
        if not all(col in df_hue.columns for col in required_cols):
            continue
        
        # Filter valid data
        df_hue = df_hue[required_cols].dropna()
        
        if len(df_hue) > 10:
            df_hue = remove_outliers(df_hue, target)
        
        if len(df_hue) < min_samples:
            results[hue_value] = None
            continue
        
        best_result = None
        best_score = -float('inf')
        
        for log_transform in log_transforms:
            try:
                X, y, y_predicted, model, metrics = train_multiple_models(
                    df_hue, predictors, target, log_transform=log_transform, apply_outlier_removal=False
                )
                score = 0.35 * metrics['R²'] - 0.65 * (metrics['MAPE (%)'] / 100)
                if score > best_score:
                    best_score = score
                    best_result = {
                        'X': X, 'y': y, 'y_predicted': y_predicted, 
                        'model': model, 'metrics': metrics, 
                        'log_transform': log_transform, 'n_samples': len(y)
                    }
            except Exception as e:
                pass
        
        results[hue_value] = best_result
    
    return results


def print_prediction_metrics(results: pd.DataFrame, target_name: str) -> pd.DataFrame:
    """
    Print comprehensive prediction accuracy metrics from a results DataFrame.
    
    Parameters:
    -----------
    results : pd.DataFrame
        DataFrame containing 'ACTUAL' and 'PREDICTED' columns with the true and predicted values
    target_name : str
        Name of the target variable being predicted (for display purposes)
    
    Returns:
    --------
    pd.DataFrame
        Enhanced results DataFrame with additional metrics:
        - APE (%): Absolute Percentage Error for each prediction
        - ACCURACY (%): Accuracy percentage (100 - APE)
        - WITHIN_20%: Boolean flag for predictions within ±20% accuracy
    """
    # Validate input DataFrame has required columns
    if 'ACTUAL' not in results.columns or 'PREDICTED' not in results.columns:
        raise ValueError("Results DataFrame must contain 'ACTUAL' and 'PREDICTED' columns")
    
    # Create a copy to avoid modifying the original
    output = results.copy()
    
    # Calculate various accuracy metrics for each prediction
    output['APE (%)'] = (abs(output['ACTUAL'] - output['PREDICTED']) / output['ACTUAL'].replace(0, np.nan)) * 100  # Absolute Percentage Error
    output['ACCURACY (%)'] = 100 - output['APE (%)']  # Accuracy as percentage
    
    # Add quality indicators
    output['WITHIN_20%'] = output['APE (%)'] <= 20  # Flag for acceptable predictions
    
    # Display summary statistics
    print("\n" + "="*60)
    print(f"  PREDICTION ACCURACY SUMMARY - {target_name}")
    print("="*60)
    print(f"  Mean Absolute Percentage Error (MAPE): {output['APE (%)'].mean():.2f}%")
    print(f"  Median Absolute Percentage Error: {output['APE (%)'].median():.2f}%")
    print(f"  Mean Accuracy: {output['ACCURACY (%)'].mean():.2f}%")
    print(f"  Predictions within ±20%: {output['WITHIN_20%'].sum()} / {len(output)} ({output['WITHIN_20%'].sum()/len(output)*100:.1f}%)")
    print("="*60 + "\n")
    
    return output

def consolidate_results_by_alcance(results_target):
    # Lists to collect data
    data_list = []
    metrics_list = []
    models_dict = {}
    
    # Iterate through each alcance type
    for alcance_type, result in results_target.items():
        # Skip if result is None (insufficient data)
        if result is None:
            continue
        
        # Extract X, y, y_predicted
        X = result['X']
        y = result['y']
        y_predicted = result['y_predicted']
        metrics = result['metrics']
        
        # Extract model and log_transform if available
        if 'model' in result:
            models_dict[alcance_type] = {
                'model': result['model'],
                'log_transform': result.get('log_transform', 'none')
            }
        
        # Create dataframe for this alcance type
        # Handle X as DataFrame or array
        if isinstance(X, pd.DataFrame):
            longitud_km = X.iloc[:, 0].values  # First column is LONGITUD KM
        else:
            longitud_km = X.flatten()
        
        # Create temporary dataframe
        temp_df = pd.DataFrame({
            'LONGITUD KM': longitud_km,
            'ALCANCE': alcance_type,
            'y': y,
            'y_predicted': y_predicted
        })
        data_list.append(temp_df)
        
        # Create metrics dataframe for this alcance type
        metrics_df = pd.DataFrame([metrics])
        metrics_df.insert(0, 'ALCANCE', alcance_type)
        # Add log_transform and n_samples if available
        if 'log_transform' in result:
            metrics_df['log_transform'] = result['log_transform']
        if 'n_samples' in result:
            metrics_df['n_samples'] = result['n_samples']
        metrics_list.append(metrics_df)
    
    # Concatenate all data
    if len(data_list) > 0:
        consolidated_data = pd.concat(data_list, ignore_index=True)
    else:
        consolidated_data = pd.DataFrame(columns=['LONGITUD KM', 'ALCANCE', 'y', 'y_predicted'])
    
    # Concatenate all metrics
    if len(metrics_list) > 0:
        consolidated_metrics = pd.concat(metrics_list, ignore_index=True)
    else:
        consolidated_metrics = pd.DataFrame()
    
    return {'X': consolidated_data[['LONGITUD KM', 'ALCANCE']], 'y': consolidated_data['y'], 'y_predicted': consolidated_data['y_predicted'], 
            'models': models_dict, 'metrics': consolidated_metrics
    }
