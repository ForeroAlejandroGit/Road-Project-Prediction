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

