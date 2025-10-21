
import sqlite3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config

def get_db():
    db = sqlite3.connect(Config.DATABASE)
    db.row_factory = sqlite3.Row
    return db

class Proyecto:
    @staticmethod
    def get_all():
        db = get_db()
        proyectos = db.execute('SELECT * FROM proyectos ORDER BY created_at DESC').fetchall()
        db.close()
        return [dict(p) for p in proyectos]
    
    @staticmethod
    def get_by_id(proyecto_id):
        db = get_db()
        proyecto = db.execute('SELECT * FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone()
        db.close()
        return dict(proyecto) if proyecto else None
    
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        proyecto = db.execute('SELECT * FROM proyectos WHERE codigo = ?', (codigo,)).fetchone()
        db.close()
        return dict(proyecto) if proyecto else None
    
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.execute('''
            INSERT INTO proyectos (nombre, codigo, num_ufs, longitud, anio_inicio, duracion, fase, ubicacion, costo, lat_inicio, lng_inicio, lat_fin, lng_fin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['nombre'], data['codigo'], data['num_ufs'], data['longitud'],
            data['anio_inicio'], data['duracion'], data['fase'], data['ubicacion'],
            data['costo'], data['lat_inicio'], data['lng_inicio'], data['lat_fin'], data['lng_fin']
        ))
        db.commit()
        proyecto_id = cursor.lastrowid
        db.close()
        return proyecto_id
    
    @staticmethod
    def update(proyecto_id, data):
        db = get_db()
        db.execute('''
            UPDATE proyectos 
            SET nombre=?, codigo=?, num_ufs=?, longitud=?, anio_inicio=?, duracion=?, fase=?, ubicacion=?, costo=?, lat_inicio=?, lng_inicio=?, lat_fin=?, lng_fin=?
            WHERE id=?
        ''', (
            data['nombre'], data['codigo'], data['num_ufs'], data['longitud'],
            data['anio_inicio'], data['duracion'], data['fase'], data['ubicacion'],
            data['costo'], data['lat_inicio'], data['lng_inicio'], data['lat_fin'], data['lng_fin'],
            proyecto_id
        ))
        db.commit()
        db.close()
    
    @staticmethod
    def delete(proyecto_id):
        db = get_db()
        db.execute('DELETE FROM proyectos WHERE id = ?', (proyecto_id,))
        db.commit()
        db.close()


class UnidadFuncional:
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        ufs = db.execute('SELECT * FROM unidad_funcional WHERE codigo = ? ORDER BY unidad_funcional', (codigo,)).fetchall()
        db.close()
        return [dict(uf) for uf in ufs]
    
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.execute('''
            INSERT INTO unidad_funcional (codigo, unidad_funcional, longitud_km, puentes_vehiculares_und, puentes_vehiculares_mt2,
                                         puentes_peatonales_und, puentes_peatonales_mt2, tuneles_und, tuneles_km, alcance, zona, tipo_terreno)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['codigo'], data['unidad_funcional'], data['longitud_km'], data['puentes_vehiculares_und'],
            data['puentes_vehiculares_mt2'], data['puentes_peatonales_und'], data['puentes_peatonales_mt2'],
            data['tuneles_und'], data['tuneles_km'], data['alcance'], data['zona'], data['tipo_terreno']
        ))
        db.commit()
        uf_id = cursor.lastrowid
        db.close()
        return uf_id
    
    @staticmethod
    def delete(uf_id):
        db = get_db()
        db.execute('DELETE FROM unidad_funcional WHERE id = ?', (uf_id,))
        db.commit()
        db.close()


class ItemFaseI:
    """Model for Fase I - Prefactibilidad items (13 fields)"""
    ITEM_COLUMNS = [
        'transporte', 'diseno_geometrico', 'prefactibilidad_tuneles', 
        'geologia', 'geotecnia', 'hidrologia_hidraulica', 'ambiental_social',
        'predial', 'riesgos_sostenibilidad', 'evaluacion_economica', 
        'socioeconomica_financiera', 'estructuras', 'direccion_coordinacion'
    ]
    
    ITEM_LABELS = {
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
    
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        item_row = db.execute('SELECT * FROM item_fase_i WHERE codigo = ?', (codigo,)).fetchone()
        db.close()
        
        if not item_row:
            return None
        
        return dict(item_row)
    
    @staticmethod
    def create(data):
        db = get_db()
        columns = ['codigo'] + ItemFaseI.ITEM_COLUMNS
        placeholders = ', '.join(['?'] * len(columns))
        column_names = ', '.join(columns)
        
        values = [data.get('codigo')]
        for col in ItemFaseI.ITEM_COLUMNS:
            values.append(data.get(col, 0))
        
        cursor = db.execute(f'''
            INSERT INTO item_fase_i ({column_names})
            VALUES ({placeholders})
        ''', values)
        db.commit()
        item_id = cursor.lastrowid
        db.close()
        return item_id
    
    @staticmethod
    def update(codigo, data):
        db = get_db()
        set_clause = ', '.join([f'{col} = ?' for col in ItemFaseI.ITEM_COLUMNS])
        values = [data.get(col, 0) for col in ItemFaseI.ITEM_COLUMNS]
        values.append(codigo)
        
        db.execute(f'''
            UPDATE item_fase_i SET {set_clause} WHERE codigo = ?
        ''', values)
        db.commit()
        db.close()
    
    @staticmethod
    def delete(codigo):
        db = get_db()
        db.execute('DELETE FROM item_fase_i WHERE codigo = ?', (codigo,))
        db.commit()
        db.close()


class ItemFaseII:
    """Model for Fase II - Factibilidad items (13 fields, with aggregated subcomponents)"""
    ITEM_COLUMNS = [
        'transporte', 'topografia', 'geologia', 'taludes', 
        'hidrologia_hidraulica', 'estructuras', 'tuneles', 'pavimento',
        'predial', 'ambiental_social', 'costos_presupuestos', 
        'socioeconomica', 'direccion_coordinacion'
    ]
    
    ITEM_LABELS = {
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
    
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        item_row = db.execute('SELECT * FROM item_fase_ii WHERE codigo = ?', (codigo,)).fetchone()
        db.close()
        
        if not item_row:
            return None
        
        return dict(item_row)
    
    @staticmethod
    def create(data):
        db = get_db()
        columns = ['codigo'] + ItemFaseII.ITEM_COLUMNS
        placeholders = ', '.join(['?'] * len(columns))
        column_names = ', '.join(columns)
        
        values = [data.get('codigo')]
        for col in ItemFaseII.ITEM_COLUMNS:
            values.append(data.get(col, 0))
        
        cursor = db.execute(f'''
            INSERT INTO item_fase_ii ({column_names})
            VALUES ({placeholders})
        ''', values)
        db.commit()
        item_id = cursor.lastrowid
        db.close()
        return item_id
    
    @staticmethod
    def update(codigo, data):
        db = get_db()
        set_clause = ', '.join([f'{col} = ?' for col in ItemFaseII.ITEM_COLUMNS])
        values = [data.get(col, 0) for col in ItemFaseII.ITEM_COLUMNS]
        values.append(codigo)
        
        db.execute(f'''
            UPDATE item_fase_ii SET {set_clause} WHERE codigo = ?
        ''', values)
        db.commit()
        db.close()
    
    @staticmethod
    def delete(codigo):
        db = get_db()
        db.execute('DELETE FROM item_fase_ii WHERE codigo = ?', (codigo,))
        db.commit()
        db.close()


class ItemFaseIII:
    """Model for Fase III - Diseños a detalle items (20 fields, parent headers skipped)"""
    ITEM_COLUMNS = [
        'transporte', 'informacion_geografica', 'trazado_diseno_geometrico', 
        'seguridad_vial', 'sistemas_inteligentes', 'geologia', 'hidrogeologia',
        'suelos', 'taludes', 'pavimento', 'socavacion', 'estructuras', 'tuneles',
        'urbanismo_paisajismo', 'predial', 'impacto_ambiental', 'cantidades',
        'evaluacion_socioeconomica', 'otros_manejo_redes', 'direccion_coordinacion'
    ]
    
    ITEM_LABELS = {
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
    
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        item_row = db.execute('SELECT * FROM item_fase_iii WHERE codigo = ?', (codigo,)).fetchone()
        db.close()
        
        if not item_row:
            return None
        
        return dict(item_row)
    
    @staticmethod
    def create(data):
        db = get_db()
        columns = ['codigo'] + ItemFaseIII.ITEM_COLUMNS
        placeholders = ', '.join(['?'] * len(columns))
        column_names = ', '.join(columns)
        
        values = [data.get('codigo')]
        for col in ItemFaseIII.ITEM_COLUMNS:
            values.append(data.get(col, 0))
        
        cursor = db.execute(f'''
            INSERT INTO item_fase_iii ({column_names})
            VALUES ({placeholders})
        ''', values)
        db.commit()
        item_id = cursor.lastrowid
        db.close()
        return item_id
    
    @staticmethod
    def update(codigo, data):
        db = get_db()
        set_clause = ', '.join([f'{col} = ?' for col in ItemFaseIII.ITEM_COLUMNS])
        values = [data.get(col, 0) for col in ItemFaseIII.ITEM_COLUMNS]
        values.append(codigo)
        
        db.execute(f'''
            UPDATE item_fase_iii SET {set_clause} WHERE codigo = ?
        ''', values)
        db.commit()
        db.close()
    
    @staticmethod
    def delete(codigo):
        db = get_db()
        db.execute('DELETE FROM item_fase_iii WHERE codigo = ?', (codigo,))
        db.commit()
        db.close()
