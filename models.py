import sqlite3
from config import Config

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
            codigo TEXT NOT NULL,
            item TEXT NOT NULL,
            causado REAL,
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
            ('6935', '1 - TRANSPORTE', 0),
            ('6935', '2 1 - INFORMACIÓN GEOGRAFICA', 0),
            ('6935', '2 2 TRAZADO Y DISEÑO GEOMETRICO', 48662655),
            ('6935', '2 3 - SEGURIDAD VIAL', 29502029),
            ('6935', '2 4 - SISTEMAS INTELIGENTES', 31376747),
            ('6935', '3 1 - GEOLOGÍA', 0),
            ('6935', '3 2 - HIDROGEOLOGÍA', 48023645),
            ('6935', '4 - SUELOS', 64347356),
            ('6935', '5 - TALUDES', 78892217),
            ('6935', '6 - PAVIMENTO', 27445905),
            ('6935', '7 - SOCAVACIÓN', 70781010),
            ('6935', '8 - ESTRUCTURAS', 226142019),
            ('6935', '9 - TÚNELES', 0),
            ('6935', '10 - URBANISMO Y PAISAJISMO', 16129209),
            ('6935', '11 - PREDIAL', 0),
            ('6935', '12 - IMPACTO AMBIENTA', 0),
            ('6935', '13 - CANTIDADES', 0),
            ('6935', '14 - EVALUACIÓN SOCIOECONÓMICA', 0),
            ('6935', '15 - OTROS - MANEJO DE RESIDUOS', 117131003),
            ('6935', '16 - DIRECCIÓN Y CORDINACIÓN', 104254285),
        ]
        db.executemany('''
            INSERT INTO item (codigo, item, causado)
            VALUES (?, ?, ?)
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
    @staticmethod
    def get_by_codigo(codigo):
        db = get_db()
        items = db.execute('SELECT * FROM item WHERE codigo = ? ORDER BY item', (codigo,)).fetchall()
        db.close()
        return [dict(i) for i in items]
    
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.execute('''
            INSERT INTO item (codigo, item, causado)
            VALUES (?, ?, ?)
        ''', (data['codigo'], data['item'], data['causado']))
        db.commit()
        item_id = cursor.lastrowid
        db.close()
        return item_id
    
    @staticmethod
    def update(item_id, data):
        db = get_db()
        db.execute('''
            UPDATE item SET causado = ? WHERE id = ?
        ''', (data['causado'], item_id))
        db.commit()
        db.close()
    
    @staticmethod
    def delete(item_id):
        db = get_db()
        db.execute('DELETE FROM item WHERE id = ?', (item_id,))
        db.commit()
        db.close()

