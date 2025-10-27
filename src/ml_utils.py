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

