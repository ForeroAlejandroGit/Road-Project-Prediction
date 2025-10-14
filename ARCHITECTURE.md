# 🏗️ Arquitectura del Sistema

## Resumen

Este proyecto implementa una **Single Page Application (SPA)** con arquitectura de 3 capas:

1. **Frontend**: Vue 3 + Vue Router (SPA reactiva sin build)
2. **Backend**: Flask REST API
3. **Datos**: SQLite con 3 tablas relacionadas

## Decisiones de Diseño

### ¿Por qué Vue Router en lugar de v-if/v-show?

**Antes**: Una sola página con `v-if="currentView === 'x'"` para cambiar vistas.

**Ahora**: Vue Router con rutas independientes.

**Ventajas**:
- ✅ URLs navegables (`/#/detalle`, `/#/nuevo`)
- ✅ Historial del navegador funciona (botón atrás)
- ✅ Componentes separados en archivos diferentes
- ✅ Lazy loading de datos por ruta
- ✅ Navegación programática (`this.$router.push`)
- ✅ Separación clara de responsabilidades

### ¿Por qué Jinja2 includes + {% raw %}?

**Problema**: Vue usa `{{ }}` y Jinja2 también.

**Solución**: 
- Componentes Vue en archivos separados (`templates/components/`)
- Jinja2 `{% raw %}` envuelve el código Vue
- Templates se incluyen via `{% include %}` en las rutas

**Ventaja**: 
- Separación física de vistas
- Sin conflicto de sintaxis
- Fácil mantenimiento

### Estructura de Datos

```
proyectos (tabla principal)
  └── codigo (TEXT UNIQUE)
       ├── unidad_funcional (1:N) ── FK: codigo
       └── item (1:N) ─────────────── FK: codigo
```

**Relaciones**:
- Un proyecto tiene muchas unidades funcionales
- Un proyecto tiene muchos items de costo
- Cascada de eliminación (ON DELETE CASCADE)

## Flujo de Datos

### 1. Carga Inicial

```
Usuario → http://localhost:5000
         ↓
    Flask renderiza index.html
         ↓
    Vue monta la app
         ↓
    Router carga vista '/' (Inicio)
         ↓
    GET /api/proyectos
         ↓
    Renderiza tabla + mapa
```

### 2. Click en Proyecto (Reactivity)

```
Usuario click en fila
         ↓
    selectProyecto(proyecto)
         ↓
    appState.selectedProyecto = proyecto (reactivo)
         ↓
    drawRoute() dibuja en Google Maps
         ↓
    Botón "Detalle Proyecto" aparece (v-if)
```

### 3. Vista Detalle con Datos Relacionados

```
Usuario → /detalle
         ↓
    Componente Detalle monta
         ↓
    watch(selectedProyecto) detecta cambio
         ↓
    GET /api/unidades-funcionales/6935
    GET /api/items/6935 (paralelo)
         ↓
    Renderiza tablas + mapa detallado
```

## API REST Design

### Endpoints por Recurso

**Proyectos**:
- `GET /api/proyectos` → Lista
- `GET /api/proyectos/<id>` → Por ID numérico
- `GET /api/proyectos/codigo/<codigo>` → Por código de proyecto
- `POST /api/proyectos` → Crear
- `PUT /api/proyectos/<id>` → Actualizar
- `DELETE /api/proyectos/<id>` → Eliminar

**Unidades Funcionales**:
- `GET /api/unidades-funcionales/<codigo>` → Todas las UFs de un proyecto
- `POST /api/unidades-funcionales` → Crear UF
- `DELETE /api/unidades-funcionales/<id>` → Eliminar UF

**Items**:
- `GET /api/items/<codigo>` → Todos los items de un proyecto
- `POST /api/items` → Crear item
- `PUT /api/items/<id>` → Actualizar costo causado
- `DELETE /api/items/<id>` → Eliminar item

### Formato de Respuesta

```json
// GET /api/proyectos
[
  {
    "id": 1,
    "codigo": "6935",
    "nombre": "PEDREGAL - PASTO UF4-UF5",
    "num_ufs": 2,
    "longitud": 37.96,
    ...
  }
]

// GET /api/unidades-funcionales/6935
[
  {
    "id": 1,
    "codigo": "6935",
    "unidad_funcional": 4,
    "longitud_km": 15.76,
    "puentes_vehiculares_und": 4,
    ...
  }
]

// GET /api/items/6935
[
  {
    "id": 1,
    "codigo": "6935",
    "item": "1 - TRANSPORTE",
    "causado": 0
  },
  ...
]
```

## Estado Global (Vue Provide/Inject)

### App State (Root Component)

```javascript
{
  proyectos: [],              // Todos los proyectos
  selectedProyecto: null,     // Proyecto seleccionado
  editingProyecto: null,      // Proyecto en edición
  form: {...}                 // Formulario activo
}
```

### Compartir Estado entre Rutas

```javascript
// Root app.js
provide() {
  return { appState: this };
}

// Componente hijo (Inicio, Detalle, etc.)
inject: ['appState'],
computed: {
  proyectos() { return this.appState.proyectos; }
}
```

**Ventaja**: Estado global sin Vuex/Pinia, perfecto para prototipos.

## Google Maps Integration

### Mapa Principal (Vista Inicio)

```javascript
initMap() → Crea map global
loadProyectos() → updateMapMarkers()
  ↓
  Crea marcadores para cada proyecto
  ↓
  Click en marcador → selectProyecto()
  ↓
  drawRoute() usa DirectionsService
```

### Mapa Detalle (Vista Detalle)

```javascript
watch(selectedProyecto) {
  $nextTick() → espera DOM
    ↓
  Crea detalleMap en #detalle-map
    ↓
  DirectionsRenderer dibuja ruta
}
```

## Patrón de Componentes

### Cada Vista es Autónoma

```
Inicio
  - Mapa + tabla
  - Métodos: selectProyecto, editProyecto, deleteProyecto

Nuevo
  - Formulario
  - Métodos: saveProyecto, cancelForm

Detalle
  - Info proyecto + UFs + Items
  - data(): unidadesFuncionales, items (local)
  - Métodos: loadRelatedData()

Historicos
  - Stats cards
  - computed: totalInversion, costoPromedioKm

Modelo
  - Form predicción
  - data(): prediccion, costoPredicho (local)
```

## Template Inheritance

```
base.html (Layout común)
  ├── <head> con Vue + Vue Router CDNs
  └── {% block content %}
       └── index.html (SPA container)
            ├── <header> con <router-link>
            └── <router-view>
                 └── Renderiza componente según ruta
                      ├── inicio.html
                      ├── nuevo.html
                      ├── detalle.html
                      ├── historicos.html
                      └── modelo.html
```

## Próximos Pasos Arquitecturales

### 1. Autenticación (Flask-Login)

```python
@app.route('/api/proyectos')
@login_required
def get_proyectos():
    ...
```

### 2. Paginación (API)

```python
@app.route('/api/proyectos?page=1&per_page=20')
def get_proyectos():
    page = request.args.get('page', 1, type=int)
    ...
```

### 3. Filtros y Búsqueda

```
GET /api/proyectos?ubicacion=Valle&fase=Detalle
```

### 4. Validación Backend

```python
from marshmallow import Schema, fields, validate

class ProyectoSchema(Schema):
    codigo = fields.Str(required=True, validate=validate.Length(min=1))
    longitud = fields.Float(validate=validate.Range(min=0))
    ...
```

### 5. Tests

```python
def test_get_proyectos():
    response = client.get('/api/proyectos')
    assert response.status_code == 200
    assert len(response.json) > 0
```

### 6. Migration a PostgreSQL

```python
# config.py
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')

# Con SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)
```

---

## Conclusión

Esta arquitectura proporciona:
- ✅ Separación clara de responsabilidades
- ✅ Reactividad sin complejidad
- ✅ API REST escalable
- ✅ Datos relacionados bien modelados
- ✅ UI moderna y funcional
- ✅ Sin tooling complejo (no webpack, no npm build)

**Es un equilibrio perfecto entre simplicidad y funcionalidad para un prototipo profesional.**

