import requests, pandas as pd, time
import sqlite3
from src.config import Config
class PresentValue:

    def __init__(self):
        self.incremento = None

    def fetch_incremento_from_database(self) -> pd.Series:
        with sqlite3.connect(Config.DATABASE) as conn:
            df = pd.read_sql_query("SELECT * FROM anual_increment", conn)
            # Convert DataFrame to Series - assuming first column is year and second is increment
            if df.shape[1] == 2:
                self.incremento = df.set_index(df.columns[0])[df.columns[1]]
            else:
                # If only one column with index, squeeze to Series
                self.incremento = df.squeeze()
        return self.incremento

    def present_value(self, past_value: float, past_year: int, present_year: int = None) -> float:
        """Compound yearly increments from past_year+1 to present_year and return present value."""
        inc = self.incremento.copy().astype(float)
        inc.index = inc.index.astype(int)
        if inc.max() > 1.0:
            inc = inc / 100.0

        if present_year is None:
            present_year = min(pd.Timestamp.now().year, int(inc.index.max()))
        
        # Ensure years are integers (handle numpy.float64 from DataFrames)
        past_year = int(past_year)
        present_year = int(present_year)
        
        if present_year <= past_year:
            return float(past_value)

        years = range(past_year + 1, present_year + 1)
        inc_years = inc.reindex(years).fillna(0.0)
        factor = (1.0 + inc_years).prod()
        return float(past_value) * float(factor)
    
    def present_value_costs(self, row: pd.Series, mask: list[str], present_year: int) -> pd.Series:
        new_row = row.copy()
        for col in mask:
            new_row[col] = self.present_value(new_row[col], new_row['AÑO INICIO'], present_year) 
        return new_row

    
# Example: compute present value for 1,000,000 from 2015 to latest available
# example_value = 1_000_000
# example_past_year = 2015
# present_val = present_value(example_value, example_past_year)
# present_val
