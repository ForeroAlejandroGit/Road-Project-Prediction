import sqlite3
from src.config import Config


def get_db():
    db = sqlite3.connect(Config.DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            num_ufs INTEGER,
            longitud REAL,
            anio_inicio INTEGER,
            duracion INTEGER,
            fase TEXT,
            ubicacion TEXT,
            costo REAL,
            lat_inicio REAL,
            lng_inicio REAL,
            lat_fin REAL,
            lng_fin REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS unidad_funcional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            unidad_funcional INTEGER NOT NULL,
            longitud_km REAL,
            puentes_vehiculares_und INTEGER,
            puentes_vehiculares_mt2 INTEGER,
            puentes_peatonales_und INTEGER,
            puentes_peatonales_mt2 INTEGER,
            tuneles_und INTEGER,
            tuneles_km REAL,
            alcance TEXT,
            zona TEXT,
            tipo_terreno TEXT,
            FOREIGN KEY (codigo) REFERENCES proyectos(codigo) ON DELETE CASCADE
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            transporte REAL DEFAULT 0,
            informacion_geografica REAL DEFAULT 0,
            trazado_diseno_geometrico REAL DEFAULT 0,
            seguridad_vial REAL DEFAULT 0,
            sistemas_inteligentes REAL DEFAULT 0,
            geologia REAL DEFAULT 0,
            hidrogeologia REAL DEFAULT 0,
            suelos REAL DEFAULT 0,
            taludes REAL DEFAULT 0,
            pavimento REAL DEFAULT 0,
            socavacion REAL DEFAULT 0,
            estructuras REAL DEFAULT 0,
            tuneles REAL DEFAULT 0,
            urbanismo_paisajismo REAL DEFAULT 0,
            predial REAL DEFAULT 0,
            impacto_ambiental REAL DEFAULT 0,
            cantidades REAL DEFAULT 0,
            evaluacion_socioeconomica REAL DEFAULT 0,
            otros_manejo_redes REAL DEFAULT 0,
            direccion_coordinacion REAL DEFAULT 0,
            FOREIGN KEY (codigo) REFERENCES proyectos(codigo) ON DELETE CASCADE
        )
    ''')
    
    db.commit()
    
    count = db.execute('SELECT COUNT(*) as count FROM proyectos').fetchone()['count']
    if count == 0:
        sample_data = [
            ('PEDREGAL - PASTO UF4-UF5', '6935', 2, 37.96, 2016, 6, 'Detalle', 'Nariño', 862658.080, 1.2345, -77.2812, 1.2145, -77.2912),
            ('BUGA - BUENAVENTURA', '0654801', 21, 142.26, 2023, 14, 'Detalle', 'Valle del Cauca', 3385721.983, 3.9018, -76.2978, 3.8818, -76.3178),
            ('QUEREMAL - DANUBIO', '0581301', 1, 5.24, 2022, 12, 'Detalle', 'Valle del Cauca', 610090.248, 3.5234, -76.7345, 3.5434, -76.7545),
        ]
        db.executemany('''
            INSERT INTO proyectos (nombre, codigo, num_ufs, longitud, anio_inicio, duracion, fase, ubicacion, costo, lat_inicio, lng_inicio, lat_fin, lng_fin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        uf_sample = [
            ('6935', 4, 15.76, 4, 6292, 0, 0, 0, 0, 'Segunda calzada', 'Rural', 'Montañoso'),
            ('6935', 5, 22.2, 0, 0, 1, 77, 0, 0, 'Segunda calzada', 'Rural', 'Montañoso'),
        ]
        db.executemany('''
            INSERT INTO unidad_funcional (codigo, unidad_funcional, longitud_km, puentes_vehiculares_und, puentes_vehiculares_mt2, 
                                         puentes_peatonales_und, puentes_peatonales_mt2, tuneles_und, tuneles_km, alcance, zona, tipo_terreno)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', uf_sample)
        
        item_sample = [
            ('6935', 0, 0, 48662655, 29502029, 31376747, 0, 48023645, 64347356, 78892217, 27445905, 70781010, 226142019, 0, 16129209, 0, 0, 0, 0, 117131003, 104254285),
        ]
        db.executemany('''
            INSERT INTO item (codigo, transporte, informacion_geografica, trazado_diseno_geometrico, seguridad_vial, sistemas_inteligentes,
                            geologia, hidrogeologia, suelos, taludes, pavimento, socavacion, estructuras, tuneles, urbanismo_paisajismo,
                            predial, impacto_ambiental, cantidades, evaluacion_socioeconomica, otros_manejo_redes, direccion_coordinacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', item_sample)
        
        db.commit()
    
    db.close()


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


class Item:
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
        'trazado_diseno_geometrico': '2.2 TRAZADO Y DISEÑO GEOMÉTRICO',
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
        item_row = db.execute('SELECT * FROM item WHERE codigo = ?', (codigo,)).fetchone()
        db.close()
        
        if not item_row:
            return None
        
        return dict(item_row)
    
    @staticmethod
    def create(data):
        db = get_db()
        columns = ['codigo'] + Item.ITEM_COLUMNS
        placeholders = ', '.join(['?'] * len(columns))
        column_names = ', '.join(columns)
        
        values = [data.get('codigo')]
        for col in Item.ITEM_COLUMNS:
            values.append(data.get(col, 0))
        
        cursor = db.execute(f'''
            INSERT INTO item ({column_names})
            VALUES ({placeholders})
        ''', values)
        db.commit()
        item_id = cursor.lastrowid
        db.close()
        return item_id
    
    @staticmethod
    def update(codigo, data):
        db = get_db()
        set_clause = ', '.join([f'{col} = ?' for col in Item.ITEM_COLUMNS])
        values = [data.get(col, 0) for col in Item.ITEM_COLUMNS]
        values.append(codigo)
        
        db.execute(f'''
            UPDATE item SET {set_clause} WHERE codigo = ?
        ''', values)
        db.commit()
        db.close()
    
    @staticmethod
    def delete(codigo):
        db = get_db()
        db.execute('DELETE FROM item WHERE codigo = ?', (codigo,))
        db.commit()
        db.close()


