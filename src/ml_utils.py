"""
Machine Learning Utility Functions

This module contains shared utility functions used across multiple ML notebooks
for data preprocessing, outlier detection, and model evaluation.
"""

import numpy as np
import pandas as pd
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
        print(f"  → Warning: Only {len(df_nonzero)} samples. Skipping outlier detection.")
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
    
    # Report
    n_outliers = is_outlier.sum()
    pct_removed = (n_outliers / len(df_nonzero)) * 100
    print(f"  → Removed {n_outliers}/{len(df_nonzero)} outliers ({pct_removed:.1f}%) using {method}")
    
    if method == 'ensemble' and len(outlier_flags) > 1:
        for flag_name, flags in outlier_flags.items():
            print(f"     • {flag_name}: {flags.sum()} outliers")
    
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
        'R²': r2,
        'MAE': mae,
        'RMSE': rmse,
        'MAPE (%)': mape,
        'Median AE': median_ae,
        'Max Error': max_error
    }
    
    # Add RMSLE if requested (useful for exponential/log-scale predictions)
    if include_rmsle:
        rmsle = np.sqrt(np.mean((np.log1p(y_pred) - np.log1p(y_true))**2))
        metrics['RMSLE'] = rmsle
    
    return metrics


def create_scatter_plot_with_regression(df, predictor_name, target_name, hue_name='ALCANCE', 
                                         df_raw=None, title=None):
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
    
    fig.show()
    return fig


def analysis_plots(y, y_predicted, df_item_cleaned, predictor_name, target_name, 
                   hue_name, df_raw=None):
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
                if 'CÓDIGO DEL PROYECTO' in df_raw.columns:
                    hover += f"<b>Código:</b> {df_raw.loc[idx, 'CÓDIGO DEL PROYECTO']}<br>"
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
    
    fig.show()
    return fig

