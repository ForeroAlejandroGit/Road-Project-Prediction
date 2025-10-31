from _typeshed import NoneType
from src.ml_linear_dependency import train_and_calculate_metrics
from src.ml_geotecnia import train_geotecnia_model, prepare_geotecnia_data
from src.ml_bridges_structures import train_brindges_structures_model
from src.ml_tunnels import train_tunnel_model
from src.ml_paisajismo import train_paisajismo_model, prepare_paisajismo_data
from src.ml_cantidades_socioeconomica import train_cantidades_model
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

    def train_models(self, fase: str) -> dict:
        
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
        results = train_and_calculate_metrics(df, targets, predictors, hue_name)
        return results

    def train_models_fase_III(self) -> dict:
        predictors = ['LONGITUD KM']
        hue_name = 'ALCANCE'
        
        targets = ['1 - TRANSPORTE', '2.1 - INFORMACIÓN GEOGRÁFICA','2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', 
                '2.3 - SEGURIDAD VIAL', '2.4 - SISTEMAS INTELIGENTES', '5 - TALUDES', '6 - PAVIMENTO',
                '7 - SOCAVACIÓN', '11 - PREDIAL', '12 - IMPACTO AMBIENTAL', '15 - OTROS - MANEJO DE REDES']
        
        df = self.df_vp[['LONGITUD KM', 'ALCANCE']].join(self.df_vp.loc[:, '1 - TRANSPORTE':])
        results = train_and_calculate_metrics(df, targets, predictors, hue_name)
        
        predictors_coord = ["2.2 - TRAZADO Y DISEÑO GEOMÉTRICO", "5 - TALUDES", "7 - SOCAVACIÓN"]
        targets_coord = ['16 - DIRECCIÓN Y COORDINACIÓN']
        results['16 - DIRECCIÓN Y COORDINACIÓN'] = train_and_calculate_metrics(df, targets_coord, predictors_coord)['16 - DIRECCIÓN Y COORDINACIÓN']
        
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
        
        input_data['LONGITUD KM LOG'] = np.log1p(input_data['LONGITUD KM'])
        
        basic_targets = ['1 - TRANSPORTE', '2.1 - INFORMACIÓN GEOGRÁFICA', '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO',
                        '2.3 - SEGURIDAD VIAL', '2.4 - SISTEMAS INTELIGENTES', '5 - TALUDES', '6 - PAVIMENTO',
                        '7 - SOCAVACIÓN', '11 - PREDIAL', '12 - IMPACTO AMBIENTAL', '15 - OTROS - MANEJO DE REDES']
        
        for target in basic_targets:
            model = models[target]['model']
            predictions[target] = model.predict(input_data[['LONGITUD KM', 'LONGITUD KM LOG', 'ALCANCE']])[0]
        
        input_data['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO'] = [predictions['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO']]
        input_data['5 - TALUDES'] = [predictions['5 - TALUDES']]
        input_data['7 - SOCAVACIÓN'] = [predictions['7 - SOCAVACIÓN']]
        
        input_data['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO LOG'] = np.log1p(input_data['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO'])
        input_data['5 - TALUDES LOG'] = np.log1p(input_data['5 - TALUDES'])
        input_data['7 - SOCAVACIÓN LOG'] = np.log1p(input_data['7 - SOCAVACIÓN'])
        
        model_coord = models['16 - DIRECCIÓN Y COORDINACIÓN']['model']
        coord_features = ['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', '5 - TALUDES', '7 - SOCAVACIÓN',
                          '2.2 - TRAZADO Y DISEÑO GEOMÉTRICO LOG', '5 - TALUDES LOG', '7 - SOCAVACIÓN LOG']
        predictions['16 - DIRECCIÓN Y COORDINACIÓN'] = model_coord.predict(input_data[coord_features])[0]
        
        model_geo = models['3 - GEOLOGÍA']['model']
        predictions['3 - GEOLOGÍA'] = model_geo.predict(input_data[['2.2 - TRAZADO Y DISEÑO GEOMÉTRICO', '5 - TALUDES', '7 - SOCAVACIÓN']])[0]
        
        model_suelos = models['4 - SUELOS']['model']
        predictions['4 - SUELOS'] = model_suelos.predict(input_data[['PUENTES VEHICULARES M2']])[0]
        
        model_estructuras = models['8 - ESTRUCTURAS']['model']
        predictions['8 - ESTRUCTURAS'] = model_estructuras.predict(input_data[['PUENTES VEHICULARES UND']])[0]
        
        input_data['TUNELES UND_LOG'] = np.log1p(input_data['TUNELES UND'])
        input_data['TUNELES KM_LOG'] = np.log1p(input_data['TUNELES KM'])
        
        model_tuneles = models['9 - TÚNELES']['model']
        predictions['9 - TÚNELES'] = model_tuneles.predict(input_data[['TUNELES UND', 'TUNELES KM', 'TUNELES UND_LOG', 'TUNELES KM_LOG']])[0]
        
        model_pais = models['10 - URBANISMO Y PAISAJISMO']['model']
        predictions['10 - URBANISMO Y PAISAJISMO'] = model_pais.predict(input_data[['PUENTES PEATONALES UND']])[0]
        
        model_cant = models['13 - CANTIDADES']['model']
        predictions['13 - CANTIDADES'] = model_cant.predict(input_data[['PUENTES VEHICULARES UND', 'PUENTES VEHICULARES M2', 'PUENTES PEATONALES UND']])[0]
        
        return predictions