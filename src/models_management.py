from src.ml_direction import train_direction_model
from src.ml_geotecnia import train_geotecnia_model, prepare_geotecnia_data
from src.ml_bridges_structures import train_brindges_structures_model
from src.ml_tunnels import train_tunnel_model
from src.ml_paisajismo import train_paisajismo_model, prepare_paisajismo_data
from src.ml_cantidades_socioeconomica import train_cantidades_model
import src.ml_utils as ml_utils
import pandas as pd

from src.config import Config
import src.eda as eda
import src.present_value as present_value

class ModelsManagement:
    def __init__(self, fase: str):
        self.fase = fase
        self.df_vp = None
        self.pv = None
        self.anual_increment = None
    
    def prepare_data(self) -> pd.DataFrame:
        self.pv = present_value.PresentValue()
        self.anual_increment = self.pv.fetch_incremento_from_database()
        preproccesing = eda.EDA()
        self.df_vp = preproccesing.create_dataset(self.pv.present_value_costs, fase=self.fase)
        return self.df_vp

    def train_models(self) -> dict:
        
        if self.fase == 'II':
            return self.train_models_fase_II()
        elif self.fase == 'III':
            return self.train_models_fase_III()
        else:
            raise ValueError(f"Fase {self.fase} no soportada")

    def train_models_fase_II(self) -> dict:
        predictors = ['LONGITUD KM']
        hue_name = 'ALCANCE'
        
        targets = ['1 - TRANSPORTE', '2 - TRAZADO Y TOPOGRAFIA (incluye subcomponentes)', 
                '3 - GEOLOGÍA (incluye subcomponentes)', '8 - PAVIMENTO', '9 - PREDIAL', '10 - AMBIENTAL Y SOCIAL',
                '11 - COSTOS Y PRESUPUESTOS', '12 - SOCIOECONÓMICA', '13 - DIRECCIÓN Y COORDINACIÓN']
        
        df = self.df_vp[['LONGITUD KM', 'ALCANCE']].join(self.df_vp.loc[:, '1 - TRANSPORTE':])
        # results = train_and_calculate_metrics(df, targets, predictors, hue_name)
        
        return Exception('Not implemented')

    def train_models_fase_III(self) -> dict:
        predictors = ['LONGITUD KM']
        hue_name = 'ALCANCE'
        
        targets = ['1 - TRANSPORTE', '2.1 - INFORMACIÓN GEOGRÁFICA','2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', 
                '2.3 - SEGURIDAD VIAL', '2.4 - SISTEMAS INTELIGENTES', '5 - TALUDES', '6 - PAVIMENTO',
                '7 - SOCAVACIÓN', '11 - PREDIAL', '12 - IMPACTO AMBIENTAL', '15 - OTROS - MANEJO DE REDES']
        
        # Iterate through targets and train models for each one
        results = {}
        for target in targets:
            linear_depedent_results = ml_utils.train_models_by_alcance_and_transform(self.df_vp, predictors, target, hue_name, min_samples=3)
            results[target] = ml_utils.consolidate_results_by_alcance(linear_depedent_results)
        
        # Train coordination model (uses other targets as predictors)
        df = self.df_vp[['LONGITUD KM', 'ALCANCE']].join(self.df_vp.loc[:, '1 - TRANSPORTE':])
        predictors_coord = ["2.2 - TRAZADO Y DISEÑO GEOMÉTRICO", "5 - TALUDES", "7 - SOCAVACIÓN"]
        target_coord = '16 - DIRECCIÓN Y COORDINACIÓN'
        results['16 - DIRECCIÓN Y COORDINACIÓN'] = train_direction_model(df, predictors_coord, target_coord)
        
        df_geo = prepare_geotecnia_data(self.df_vp)
        predictors_geo = ["2.2 - TRAZADO Y DISEÑO GEOMÉTRICO", "5 - TALUDES", "7 - SOCAVACIÓN"]
        target_geo = "3 - GEOLOGÍA"
        results[target_geo] = train_geotecnia_model(df_geo, predictors_geo, target_geo)
        
        predictors_suelos = ['PUENTES VEHICULARES M2']
        target_suelos = '4 - SUELOS'
        results[target_suelos] = train_brindges_structures_model(self.df_vp, target_suelos, predictors_suelos, exclude_codes=['0654801'], use_log_transform=True)
        
        predictors_estructuras = ['PUENTES VEHICULARES UND']
        target_estructuras = '8 - ESTRUCTURAS'
        results[target_estructuras] = train_brindges_structures_model(self.df_vp, target_estructuras, predictors_estructuras, exclude_codes=['0654801'], use_log_transform=False)
        
        target_tuneles = '9 - TÚNELES'
        predictors_tuneles = ['TUNELES UND', 'TUNELES KM']
        results[target_tuneles] = train_tunnel_model(self.df_vp, predictors_tuneles, target_tuneles)
        
        df_pais = prepare_paisajismo_data(self.df_vp)
        predictors_pais = ['PUENTES PEATONALES UND']
        target_pais = '10 - URBANISMO Y PAISAJISMO'
        results[target_pais] = train_paisajismo_model(df_pais, predictors_pais, target_pais)
        
        predictors_cant = ['PUENTES VEHICULARES UND', 'PUENTES VEHICULARES M2', 'PUENTES PEATONALES UND']
        target_cant = '13 - CANTIDADES'
        results[target_cant] = train_cantidades_model(self.df_vp, predictors_cant, target_cant, log_transform='none')
        
        return results

    def predict_fase_III(self, codigo: str, longitud_km: float, puentes_vehiculares_und: int,
                         puentes_vehiculares_m2: float, puentes_peatonales_und: int,
                         puentes_peatonales_m2: float, tuneles_und: int, tuneles_km: float,
                         alcance: str, models: dict) -> dict:
        
        import numpy as np
        
        predictions = {}
        
        basic_targets = ['1 - TRANSPORTE', '2.1 - INFORMACIÓN GEOGRÁFICA', '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO',
                        '2.3 - SEGURIDAD VIAL', '2.4 - SISTEMAS INTELIGENTES', '5 - TALUDES', '6 - PAVIMENTO',
                        '7 - SOCAVACIÓN', '11 - PREDIAL', '12 - IMPACTO AMBIENTAL', '15 - OTROS - MANEJO DE REDES']
        
        # Predict for basic targets using alcance-specific models
        for target in basic_targets:
            print(f"Processing {target}...")
            
            # Check if target exists in models and has the specific alcance
            if models.get(target) is not None:
                result = models.get(target).get(alcance)
                
                if result is not None:
                    model = result['model']
                    log_transform = result['log_transform']
                    
                    # Prepare input data
                    input_value = longitud_km
                    
                    # Apply log transformation to input if needed
                    if log_transform in ['input', 'both']:
                        input_value = np.log1p(input_value)
                    
                    # Make prediction
                    prediction = model.predict(np.array([[input_value]]))[0]
                    
                    # Apply inverse log transformation to output if needed
                    if log_transform in ['output', 'both']:
                        prediction = np.expm1(prediction)
                    
                    predictions[target] = prediction
                    print(f"  ✓ Predicted: {prediction:,.2f} (log_transform: {log_transform})")
                else:
                    predictions[target] = None
                    print(f"  ✗ Alcance '{alcance}' not available for this target")
            else:
                predictions[target] = None
                print(f"  ✗ Target not found in models")
        
        # Prepare input_data for subsequent models that need multiple predictors
        input_data = pd.DataFrame({
            'CÓDIGO': [codigo],
            'LONGITUD KM': [longitud_km],
            'PUENTES VEHICULARES UND': [puentes_vehiculares_und],
            'PUENTES VEHICULARES M2': [puentes_vehiculares_m2],
            'PUENTES PEATONALES UND': [puentes_peatonales_und],
            'PUENTES PEATONALES M2': [puentes_peatonales_m2],
            'TUNELES UND': [tuneles_und],
            'TUNELES KM': [tuneles_km],
            'ALCANCE': [alcance]
        })
        
        # Add predicted values to input_data for models that use them as predictors
        input_data['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO'] = [predictions['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO']]
        input_data['5 - TALUDES'] = [predictions['5 - TALUDES']]
        input_data['7 - SOCAVACIÓN'] = [predictions['7 - SOCAVACIÓN']]
        
        # Create LOG versions of predictors (required by train_and_calculate_metrics models)
        # These models expect both original and log-transformed columns
        for col in ['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', '5 - TALUDES', '7 - SOCAVACIÓN']:
            if input_data[col][0] is not None:
                input_data[col + ' LOG'] = np.log1p(input_data[col])
            else:
                input_data[col + ' LOG'] = [None]
        
        # Coordination model (uses train_and_calculate_metrics format - expects original + LOG columns)
        if '16 - DIRECCIÓN Y COORDINACIÓN' in models:
            model_coord = models['16 - DIRECCIÓN Y COORDINACIÓN']['model']
            coord_cols = ['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', '5 - TALUDES', '7 - SOCAVACIÓN',
                         '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO LOG', '5 - TALUDES LOG', '7 - SOCAVACIÓN LOG']
            predictions['16 - DIRECCIÓN Y COORDINACIÓN'] = model_coord.predict(input_data[coord_cols])[0]
        
        # Geology model (also uses train_and_calculate_metrics format)
        if '3 - GEOLOGÍA' in models:
            model_geo = models['3 - GEOLOGÍA']['model']
            geo_cols = ['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', '5 - TALUDES', '7 - SOCAVACIÓN']
            predictions['3 - GEOLOGÍA'] = model_geo.predict(input_data[geo_cols])[0]
        
        # Suelos model (simple predictor, no LOG columns needed in input)
        if '4 - SUELOS' in models:
            model_suelos = models['4 - SUELOS']['model']
            predictions['4 - SUELOS'] = model_suelos.predict(np.array([[puentes_vehiculares_m2]]))[0]
        
        # Estructuras model (simple predictor, no LOG columns needed in input)
        if '8 - ESTRUCTURAS' in models:
            model_estructuras = models['8 - ESTRUCTURAS']['model']
            predictions['8 - ESTRUCTURAS'] = model_estructuras.predict(np.array([[puentes_vehiculares_und]]))[0]
        
        # Tunnels model (expects 2 predictors + their LOG versions)
        if '9 - TÚNELES' in models and (tuneles_und > 0 or tuneles_km > 0):
            model_tuneles = models['9 - TÚNELES']['model']
            X_tuneles = pd.DataFrame({
                'TUNELES UND': [tuneles_und],
                'TUNELES KM': [tuneles_km],
                'TUNELES UND_LOG': [np.log1p(tuneles_und)],
                'TUNELES KM_LOG': [np.log1p(tuneles_km)]
            })
            predictions['9 - TÚNELES'] = model_tuneles.predict(X_tuneles)[0]
        else:
            predictions['9 - TÚNELES'] = None
        
        # Paisajismo model (simple predictor, no LOG columns needed in input)
        if '10 - URBANISMO Y PAISAJISMO' in models:
            model_pais = models['10 - URBANISMO Y PAISAJISMO']['model']
            predictions['10 - URBANISMO Y PAISAJISMO'] = model_pais.predict(np.array([[puentes_peatonales_und]]))[0]
        
        # Cantidades model (multiple predictors, log_transform='none' so no LOG transform needed)
        if '13 - CANTIDADES' in models:
            model_cant = models['13 - CANTIDADES']['model']
            X_cant = np.array([[puentes_vehiculares_und, puentes_vehiculares_m2, puentes_peatonales_und]])
            predictions['13 - CANTIDADES'] = model_cant.predict(X_cant)[0]
        
        return predictions