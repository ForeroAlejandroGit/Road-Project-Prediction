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
