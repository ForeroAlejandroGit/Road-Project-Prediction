import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from src.present_value import PresentValue
from src.config import Config

class EDA:
    def __init__(self, filename: str = None):
        self.filename = "../data/BASE DE DATOS PRESUPUESTOS.xlsx"
    
    def get_head(self, df: pd.DataFrame) -> pd.DataFrame:
        df_head = df.iloc[ 0:15 , 0:2 ]
        df_head = pd.DataFrame([df_head.iloc[:,1].to_list()], columns=df_head.iloc[:,0].to_list())

        # Assign dtypes: categorical, string, and numeric
        str_cols = [ "NOMBRE DEL PROYECTO"]
        int_cols = [ "AÑO INICIO"]

        df_head[str_cols] = df_head[str_cols].astype("string")
        df_head[int_cols] = df_head[int_cols].astype("Int64")
        
        return df_head.loc[:, ['NOMBRE DEL PROYECTO', 'CÓDIGO DEL PROYECTO', 'AÑO INICIO', 'FASE', 'DEPARTAMENTO']]

    def get_uf(self, df: pd.DataFrame) -> pd.DataFrame:
        df_uf = df.iloc[0:11,3:].iloc[ : , :-1 ]
        column_names = (df_uf.iloc[1:, 0].astype(str) + " " + df_uf.iloc[1:, 1].astype(str)).to_list()
        column_names = [column.replace(" nan", "") for column in column_names]
        df_uf = df_uf.drop(df_uf.columns[[1]], axis=1)
        
        return df_uf, column_names

    def get_items(self, df: pd.DataFrame) -> pd.DataFrame:
        # Detect phase from the FASE field
        fase = str(df.iloc[3, 1]) if df.shape[0] > 3 and df.shape[1] > 1 else ""
        
        # Extract item data (starting from row 17, columns 0-1, taking only column 1 values)
        df_items_raw = df.iloc[17:, 0:2]
        values = df_items_raw.iloc[:, 1].to_list()
        
        # Define column names based on phase
        if 'Fase I - Prefactibilidad' in fase:
            # Fase I - Prefactibilidad columns (13 items)
            columns_names_items = [
                "1 - TRANSPORTE", 
                "2 - DISEÑO GEOMÉTRICO", 
                "3 - PREFACTIBILIDAD TÚNELES",
                "4 - GEOLOGIA", 
                "5 - GEOTECNIA", 
                "6 - HIDROLOGÍA E HIDRÁULICA", 
                "7 - AMBIENTAL Y SOCIAL",
                "8 - PREDIAL", 
                "9 - RIESGOS Y SOSTENIBILIDAD", 
                "10 - EVALUACIÓN ECONÓMICA",
                "11 - SOCIO ECONÓMICA, FINANCIERA", 
                "12 - ESTRUCTURAS", 
                "13 - DIRECCIÓN Y COORDINACIÓN"
            ]
        elif 'Fase II - Factibilidad' in fase:
            # Fase II - Factibilidad columns (17 items including subcomponents)
            columns_names_items = [
                "1 - TRANSPORTE", 
                "2 - TRAZADO Y TOPOGRAFIA",
                "2.1 - INFORMACIÓN GEOGRÁFICA", 
                "2.2 - TRAZADO Y DISEÑO GEOMÉTRICO",
                "3 - GEOLOGÍA",
                "3.1 - GEOLOGÍA", 
                "3.2 - HIDROGEOLOGÍA",
                "4 - TALUDES",
                "5 - HIDROLOGÍA E HIDRÁULICA",
                "6 - ESTRUCTURAS", 
                "7 - TÚNELES", 
                "8 - PAVIMENTO", 
                "9 - PREDIAL",
                "10 - AMBIENTAL Y SOCIAL", 
                "11 - COSTOS Y PRESUPUESTOS",
                "12 - SOCIOECONÓMICA", 
                "13 - DIRECCIÓN Y COORDINACIÓN"
            ]
        else:
            # Fase III - Diseños a detalle (default - 22 items)
            columns_names_items = [
                "1 - TRANSPORTE", 
                "2 - TRAZADO Y DISEÑO GEOMÉTRICO", 
                "2.1 - INFORMACIÓN GEOGRÁFICA", 
                "2.2 TRAZADO Y DISEÑO GEOMÉTRICO", 
                "2.3 - SEGURIDAD VIAL",
                "2.4 - SISTEMAS INTELIGENTES", 
                "3 - GEOLOGÍA", 
                "3.1 - GEOLOGÍA", 
                "3.2 - HIDROGEOLOGÍA",
                "4 - SUELOS", 
                "5 - TALUDES", 
                "6 - PAVIMENTO", 
                "7 - SOCAVACIÓN", 
                "8 - ESTRUCTURAS",
                "9 - TÚNELES", 
                "10 - URBANISMO Y PAISAJISMO", 
                "11 - PREDIAL", 
                "12 - IMPACTO AMBIENTAL",
                "13 - CANTIDADES", 
                "14 - EVALUACIÓN SOCIOECONÓMICA", 
                "15 - OTROS - MANEJO DE REDES",
                "16 - DIRECCIÓN Y COORDINACIÓN"
            ]
        
        # Ensure values list matches column count
        if len(values) != len(columns_names_items):
            print(f"WARNING: Fase '{fase}' has {len(values)} values but {len(columns_names_items)} columns expected")
            # Pad or truncate to match
            if len(values) < len(columns_names_items):
                values.extend([0] * (len(columns_names_items) - len(values)))
            else:
                values = values[:len(columns_names_items)]
        
        df_items = pd.DataFrame([values], columns=columns_names_items)
        
        return df_items
    
    def assemble_sheet(self, df: pd.DataFrame) -> pd.DataFrame:

        df_head = self.get_head(df)
        df_uf, column_names = self.get_uf(df)
        df_items = self.get_items(df)
        rows = []
        
        #Create a row for each functional unit
        for i in range(1, df_uf.shape[1]):
            
            #Aggregate longitud, puentes, tuneles for the current functional unit
            df_uf_x = pd.DataFrame([df_uf.iloc[1:,i].to_list()], columns=column_names)  
            df_uf_x['NOMBRE UF'] = df_uf.iloc[0, i]
            
            df_items_for_functional_unit = df_items / 1 # Future consideration divide  by df_uf_totals
            
            row = pd.concat([df_head, df_uf_x, df_items_for_functional_unit], axis=1)
            rows.append(row)
            
        return pd.concat(rows, axis=0, ignore_index=True)
    
    def assemble_projects_from_excel(self) -> pd.DataFrame:
        with pd.ExcelFile(self.filename, engine="openpyxl") as xls:
            
            project_names = [project_name for project_name in xls.sheet_names if project_name.isnumeric()]
            df_project =[]

            for project_name in project_names:
                df = pd.read_excel(self.filename, sheet_name=project_name, header=None, engine="openpyxl")
                df_project.append(self.assemble_sheet(df))

        return pd.concat(df_project, axis=0, ignore_index=True)
    
    def weighted_values(self, row: pd.Series, fase: str) -> pd.Series:
        """
        Apply weighted values to row based on the specified fase.
        
        Args:
            row: DataFrame row with project data
            fase: The project phase ('I', 'II', or 'III')
        
        Returns:
            Series with weighted values applied
        """
        new_row = row.copy()
        new_row = new_row.fillna(0)
        
        # Validate fase parameter
        if fase not in ['I', 'II', 'III']:
            raise ValueError("fase must be 'I', 'II', or 'III'")

        # Get longitude weight (common to all phases)
        longitude_weigth = new_row['LONGITUD KM WEIGHT']
        
        if fase == 'I':
            # Fase I - Apply longitude weight to most items
            new_row['1 - TRANSPORTE'] *= longitude_weigth
            new_row['2 - DISEÑO GEOMÉTRICO'] *= longitude_weigth
            new_row['3 - PREFACTIBILIDAD TÚNELES'] *= longitude_weigth
            new_row['4 - GEOLOGIA'] *= longitude_weigth
            new_row['5 - GEOTECNIA'] *= longitude_weigth
            new_row['6 - HIDROLOGÍA E HIDRÁULICA'] *= longitude_weigth
            new_row['7 - AMBIENTAL Y SOCIAL'] *= longitude_weigth
            new_row['8 - PREDIAL'] *= longitude_weigth
            new_row['9 - RIESGOS Y SOSTENIBILIDAD'] *= longitude_weigth
            new_row['10 - EVALUACIÓN ECONÓMICA'] *= longitude_weigth
            new_row['11 - SOCIO ECONÓMICA, FINANCIERA'] *= longitude_weigth
            new_row['12 - ESTRUCTURAS'] *= longitude_weigth
            new_row['13 - DIRECCIÓN Y COORDINACIÓN'] *= longitude_weigth
            
        elif fase == 'II':
            # Fase II - Apply longitude weight to most items
            new_row['1 - TRANSPORTE'] *= longitude_weigth
            new_row['2 - TRAZADO Y TOPOGRAFIA (incluye subcomponentes)'] *= longitude_weigth
            new_row['3 - GEOLOGÍA (incluye subcomponentes)'] *= longitude_weigth
            new_row['4 - TALUDES'] *= longitude_weigth
            new_row['5 - HIDROLOGÍA E HIDRÁULICA'] *= longitude_weigth
            new_row['6 - ESTRUCTURAS'] *= longitude_weigth
            new_row['7 - TÚNELES'] *= longitude_weigth
            new_row['8 - PAVIMENTO'] *= longitude_weigth
            new_row['9 - PREDIAL'] *= longitude_weigth
            new_row['10 - AMBIENTAL Y SOCIAL'] *= longitude_weigth
            new_row['11 - COSTOS Y PRESUPUESTOS'] *= longitude_weigth
            new_row['12 - SOCIOECONÓMICA'] *= longitude_weigth
            new_row['13 - DIRECCIÓN Y COORDINACIÓN'] *= longitude_weigth
            
        else:  # fase == 'III'
            # Fase III - Original logic with detailed breakdown
            new_row['1 - TRANSPORTE'] *= longitude_weigth
            new_row['2.1 - INFORMACIÓN GEOGRÁFICA'] *= longitude_weigth
            new_row['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO'] *= longitude_weigth
            new_row['2.3 - SEGURIDAD VIAL'] *= longitude_weigth
            new_row['2.4 - SISTEMAS INTELIGENTES'] *= longitude_weigth
            new_row['3.1 - GEOLOGÍA'] *= longitude_weigth
            new_row['3.2 - HIDROGEOLOGÍA'] *= longitude_weigth
            new_row['4 - SUELOS'] *= longitude_weigth
            new_row['5 - TALUDES'] *= longitude_weigth
            new_row['6 - PAVIMENTO'] *= longitude_weigth
            new_row['7 - SOCAVACIÓN'] *= longitude_weigth
            new_row['8 - ESTRUCTURAS'] *= longitude_weigth
            new_row['9 - TÚNELES'] *= longitude_weigth
            new_row['10 - URBANISMO Y PAISAJISMO'] *= longitude_weigth
            new_row['11 - PREDIAL'] *= longitude_weigth
            new_row['12 - IMPACTO AMBIENTAL'] *= longitude_weigth
            new_row['13 - CANTIDADES'] *= longitude_weigth
            new_row['14 - EVALUACIÓN SOCIOECONÓMICA'] *= longitude_weigth
            new_row['15 - OTROS - MANEJO DE REDES'] *= longitude_weigth
            new_row['16 - DIRECCIÓN Y COORDINACIÓN'] *= longitude_weigth
        
        ###TODO: Add bridge, tunnel and urbanism analysis (commented for future implementation)
        # #Bridge analysis
        # bridge_weigth = 1
        # if new_row['PUENTES VEHICULARES UND'] > 0 or new_row['PUENTES PEATONALES UND'] > 0:
        #     bridges_ratio = 3
        #     bridge_weigth = ((new_row['PUENTES VEHICULARES UND WEIGHT'] + new_row['PUENTES VEHICULARES M2 WEIGHT'])*bridges_ratio + new_row['PUENTES PEATONALES UND WEIGHT'])/bridges_ratio*3
        #     # Apply to structures column based on fase
        #     if fase == 'I':
        #         new_row['12 - ESTRUCTURAS'] *= bridge_weigth
        #     elif fase == 'II':
        #         new_row['6 - ESTRUCTURAS'] *= bridge_weigth
        #     else:  # fase III
        #         new_row['4 - SUELOS'] *= bridge_weigth
        #         new_row['8 - ESTRUCTURAS'] *= bridge_weigth
        
        # #Tunnel analysis
        # tunnel_weight = 1
        # if new_row['TUNELES UND'] > 0:
        #     tunnel_weight = new_row['TUNELES UND WEIGHT'] + new_row['TUNELES KM WEIGHT']
        #     # Apply to tunnel column based on fase
        #     if fase == 'I':
        #         new_row['3 - PREFACTIBILIDAD TÚNELES'] *= tunnel_weight
        #     elif fase == 'II':
        #         new_row['7 - TÚNELES'] *= tunnel_weight
        #     else:  # fase III
        #         new_row['9 - TÚNELES'] *= tunnel_weight
        
        # #Urbanism analysis
        # urbanism_weight = 1
        # if new_row['PUENTES PEATONALES UND'] > 0:  
        #     urbanism_weight = new_row['PUENTES PEATONALES UND WEIGHT']
        #     # Apply to urbanism column (only exists in some phases)
        #     if fase == 'III':
        #         new_row['10 - URBANISMO Y PAISAJISMO'] *= urbanism_weight
        
        return new_row

    def create_dataset(self, present_value_costs, fase: str = 'III') -> pd.DataFrame:
        """
        Creates a dataset from the database with present value costs applied.
        
        Args:
            present_value_costs: Function to calculate present value costs
            fase: The project phase ('I', 'II', or 'III'). Defaults to 'III' for backward compatibility.
        
        Returns:
            DataFrame with processed project data
        """
        # df = self.assemble_projects_from_excel()
        df = self.assemble_projects_from_database(fase=fase)
        
        mask = df.columns[df.columns.str.match(r"^\d")].tolist()
        df_present_value = df.apply(present_value_costs, axis=1, mask=mask, present_year=2025)
        df = df_present_value.drop(columns=['AÑO INICIO', 'NOMBRE UF'])

        cols = df.loc[:, 'LONGITUD KM':'TUNELES KM'].columns
        totals = df.groupby('NOMBRE DEL PROYECTO')[cols].transform('sum').replace(0, pd.NA)
        w = (df[cols] / totals).fillna(0)
        w.columns = [f'{c} WEIGHT' for c in cols]
        df = df.join(w)
        df = df.apply(self.weighted_values, axis=1, fase=fase)
        nombre_series = df['NOMBRE DEL PROYECTO']
        codigo_series = df['CÓDIGO DEL PROYECTO']
        
        # Determine the last item column based on fase
        if fase == 'I':
            last_column = '13 - DIRECCIÓN Y COORDINACIÓN'
        elif fase == 'II':
            last_column = '13 - DIRECCIÓN Y COORDINACIÓN'
        else:  # fase == 'III'
            last_column = '16 - DIRECCIÓN Y COORDINACIÓN'
        
        df = df.loc[:, 'LONGITUD KM':last_column]
        df.insert(0, 'NOMBRE DEL PROYECTO', nombre_series)
        df.insert(1, 'CÓDIGO', codigo_series)
        
        return df
    
    def calculate_cost_per_km(self, df: pd.DataFrame, target_columns: list[str], length_column: str = 'LONGITUD KM') -> pd.DataFrame:
        df_cost_per_km = df.copy()
        for col in target_columns:
            df_cost_per_km[f'{col} per KM'] = df_cost_per_km[col] / df_cost_per_km[length_column]
        return df_cost_per_km
    
    def show_plots_eda(self, predictor_name: str, target_name: str, hue_name: str, df_clean: pd.DataFrame) -> None:

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Input distribution
        sns.histplot(df_clean[predictor_name], kde=True, ax=axes[0,0], color='royalblue')
        axes[0,0].set_title('Input Distribution', fontsize=14, weight='bold')

        # Output distribution  
        sns.histplot(df_clean[target_name], kde=True, ax=axes[0,1], color='crimson')
        axes[0,1].set_title('Target Distribution', fontsize=14, weight='bold')

        # Scatter by category
        sns.scatterplot(data=df_clean, x=predictor_name, y=target_name, hue=hue_name, ax=axes[1,0], s=60, alpha=0.7)
        axes[1,0].set_title(f'Relationship by {hue_name}', fontsize=14, weight='bold')

        # Joint plot with regression
        sns.regplot(data=df_clean, x=predictor_name, y=target_name, ax=axes[1,1], scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
        axes[1,1].set_title('Linear Trend', fontsize=14, weight='bold')

        plt.suptitle('Data Analysis', fontsize=16, weight='bold')
        plt.tight_layout()
        plt.show()

    def assemble_projects_from_database(self, fase: str, database_path: str = None) -> pd.DataFrame:
        """
        Assembles project data from database based on the specified fase.
        
        Args:
            fase: The project phase ('I', 'II', or 'III')
            database_path: Path to the database (defaults to Config.DATABASE)
        
        Returns:
            DataFrame with project data for the specified fase
        """
        if database_path is None:
            database_path = Config.DATABASE
        
        # Validate fase parameter
        if fase not in ['I', 'II', 'III']:
            raise ValueError("fase must be 'I', 'II', or 'III'")
        
        # Define item table and field mappings based on fase
        if fase == 'I':
            item_table = 'item_fase_i'
            item_field_to_excel = {
                'transporte': '1 - TRANSPORTE',
                'diseno_geometrico': '2 - DISEÑO GEOMÉTRICO',
                'prefactibilidad_tuneles': '3 - PREFACTIBILIDAD TÚNELES',
                'geologia': '4 - GEOLOGIA',
                'geotecnia': '5 - GEOTECNIA',
                'hidrologia_hidraulica': '6 - HIDROLOGÍA E HIDRÁULICA',
                'ambiental_social': '7 - AMBIENTAL Y SOCIAL',
                'predial': '8 - PREDIAL',
                'riesgos_sostenibilidad': '9 - RIESGOS Y SOSTENIBILIDAD',
                'evaluacion_economica': '10 - EVALUACIÓN ECONÓMICA',
                'socioeconomica_financiera': '11 - SOCIO ECONÓMICA, FINANCIERA',
                'estructuras': '12 - ESTRUCTURAS',
                'direccion_coordinacion': '13 - DIRECCIÓN Y COORDINACIÓN'
            }
            item_columns = [
                '1 - TRANSPORTE', '2 - DISEÑO GEOMÉTRICO', '3 - PREFACTIBILIDAD TÚNELES',
                '4 - GEOLOGIA', '5 - GEOTECNIA', '6 - HIDROLOGÍA E HIDRÁULICA',
                '7 - AMBIENTAL Y SOCIAL', '8 - PREDIAL', '9 - RIESGOS Y SOSTENIBILIDAD',
                '10 - EVALUACIÓN ECONÓMICA', '11 - SOCIO ECONÓMICA, FINANCIERA',
                '12 - ESTRUCTURAS', '13 - DIRECCIÓN Y COORDINACIÓN'
            ]
        elif fase == 'II':
            item_table = 'item_fase_ii'
            item_field_to_excel = {
                'transporte': '1 - TRANSPORTE',
                'topografia': '2 - TRAZADO Y TOPOGRAFIA (incluye subcomponentes)',
                'geologia': '3 - GEOLOGÍA (incluye subcomponentes)',
                'taludes': '4 - TALUDES',
                'hidrologia_hidraulica': '5 - HIDROLOGÍA E HIDRÁULICA',
                'estructuras': '6 - ESTRUCTURAS',
                'tuneles': '7 - TÚNELES',
                'pavimento': '8 - PAVIMENTO',
                'predial': '9 - PREDIAL',
                'ambiental_social': '10 - AMBIENTAL Y SOCIAL',
                'costos_presupuestos': '11 - COSTOS Y PRESUPUESTOS',
                'socioeconomica': '12 - SOCIOECONÓMICA',
                'direccion_coordinacion': '13 - DIRECCIÓN Y COORDINACIÓN'
            }
            item_columns = [
                '1 - TRANSPORTE', '2 - TRAZADO Y TOPOGRAFIA (incluye subcomponentes)',
                '3 - GEOLOGÍA (incluye subcomponentes)', '4 - TALUDES',
                '5 - HIDROLOGÍA E HIDRÁULICA', '6 - ESTRUCTURAS', '7 - TÚNELES',
                '8 - PAVIMENTO', '9 - PREDIAL', '10 - AMBIENTAL Y SOCIAL',
                '11 - COSTOS Y PRESUPUESTOS', '12 - SOCIOECONÓMICA',
                '13 - DIRECCIÓN Y COORDINACIÓN'
            ]
        else:  # fase == 'III'
            item_table = 'item_fase_iii'
            item_field_to_excel = {
                'transporte': '1 - TRANSPORTE',
                'informacion_geografica': '2.1 - INFORMACIÓN GEOGRÁFICA',
                'trazado_diseno_geometrico': '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO',
                'seguridad_vial': '2.3 - SEGURIDAD VIAL',
                'sistemas_inteligentes': '2.4 - SISTEMAS INTELIGENTES',
                'geologia': '3.1 - GEOLOGÍA',
                'hidrogeologia': '3.2 - HIDROGEOLOGÍA',
                'suelos': '4 - SUELOS',
                'taludes': '5 - TALUDES',
                'pavimento': '6 - PAVIMENTO',
                'socavacion': '7 - SOCAVACIÓN',
                'estructuras': '8 - ESTRUCTURAS',
                'tuneles': '9 - TÚNELES',
                'urbanismo_paisajismo': '10 - URBANISMO Y PAISAJISMO',
                'predial': '11 - PREDIAL',
                'impacto_ambiental': '12 - IMPACTO AMBIENTAL',
                'cantidades': '13 - CANTIDADES',
                'evaluacion_socioeconomica': '14 - EVALUACIÓN SOCIOECONÓMICA',
                'otros_manejo_redes': '15 - OTROS - MANEJO DE REDES',
                'direccion_coordinacion': '16 - DIRECCIÓN Y COORDINACIÓN'
            }
            item_columns = [
                '1 - TRANSPORTE', '2.1 - INFORMACIÓN GEOGRÁFICA', '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO',
                '2.3 - SEGURIDAD VIAL', '2.4 - SISTEMAS INTELIGENTES',
                '3.1 - GEOLOGÍA', '3.2 - HIDROGEOLOGÍA', '4 - SUELOS', '5 - TALUDES',
                '6 - PAVIMENTO', '7 - SOCAVACIÓN', '8 - ESTRUCTURAS', '9 - TÚNELES',
                '10 - URBANISMO Y PAISAJISMO', '11 - PREDIAL', '12 - IMPACTO AMBIENTAL',
                '13 - CANTIDADES', '14 - EVALUACIÓN SOCIOECONÓMICA',
                '15 - OTROS - MANEJO DE REDES', '16 - DIRECCIÓN Y COORDINACIÓN'
            ]
        
        # Connect to database
        conn = sqlite3.connect(database_path)
        
        # Build the item column selections dynamically
        item_selects = ',\n            '.join([f'i.{db_field}' for db_field in item_field_to_excel.keys()])
        
        # Query to join all three tables
        query = f"""
        SELECT 
            p.nombre AS 'NOMBRE DEL PROYECTO',
            p.codigo AS 'CÓDIGO DEL PROYECTO',
            p.anio_inicio AS 'AÑO INICIO',
            p.fase AS 'FASE',
            p.ubicacion AS 'DEPARTAMENTO',
            uf.longitud_km AS 'LONGITUD KM',
            uf.puentes_vehiculares_und AS 'PUENTES VEHICULARES UND',
            uf.puentes_vehiculares_mt2 AS 'PUENTES VEHICULARES M2',
            uf.puentes_peatonales_und AS 'PUENTES PEATONALES UND',
            uf.puentes_peatonales_mt2 AS 'PUENTES PEATONALES M2',
            uf.tuneles_und AS 'TUNELES UND',
            uf.tuneles_km AS 'TUNELES KM',
            uf.alcance AS 'ALCANCE',
            uf.zona AS 'ZONA',
            uf.tipo_terreno AS 'TIPO TERRENO',
            'UF' || uf.unidad_funcional AS 'NOMBRE UF',
            {item_selects}
        FROM proyectos p
        INNER JOIN unidad_funcional uf ON p.codigo = uf.codigo
        INNER JOIN {item_table} i ON p.codigo = i.codigo
        ORDER BY p.codigo, uf.unidad_funcional
        """
        
        # Load data into dataframe
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Rename item columns to match Excel format
        for db_field, excel_col in item_field_to_excel.items():
            if db_field in df.columns:
                df.rename(columns={db_field: excel_col}, inplace=True)
        
        # Reorder columns to match original structure
        column_order = [
            'NOMBRE DEL PROYECTO', 'CÓDIGO DEL PROYECTO', 'AÑO INICIO', 'FASE', 'DEPARTAMENTO',
            'LONGITUD KM', 'PUENTES VEHICULARES UND', 'PUENTES VEHICULARES M2',
            'PUENTES PEATONALES UND', 'PUENTES PEATONALES M2', 'TUNELES UND', 'TUNELES KM',
            'ALCANCE', 'ZONA', 'TIPO TERRENO', 'NOMBRE UF'
        ] + item_columns
        
        # Only include columns that exist in the dataframe
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        return df