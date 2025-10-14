# 🛣️ Sistema de Predicción de Costos en Proyectos Viales

Aplicación web para gestión y predicción de costos en proyectos de infraestructura vial utilizando Machine Learning.

## 🏗️ Arquitectura

### Backend (Python/Flask)
- **Framework**: Flask - Ligero y Pythonic
- **Base de datos**: SQLite - Sin servidor, perfecto para prototipos
- **API**: RESTful JSON API
- **ML**: Scikit-learn para modelos predictivos (SVR)

### Frontend (Vue 3)
- **Framework**: Vue 3 via CDN (sin build tools)
- **Reactividad**: Sistema reactivo de Vue para UI dinámica
- **Mapas**: Google Maps JavaScript API
- **Estilo**: CSS puro con variables CSS modernas

### Estructura del Proyecto
```
Road-Project-Prediction/
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── config.py              # Configuración
├── requirements.txt       # Dependencias Python
├── database.db            # Base de datos SQLite (auto-generada)
├── static/
│   ├── css/
│   │   └── style.css     # Estilos
│   └── js/
│       └── app.js        # Aplicación Vue.js
└── templates/
    └── index.html        # Plantilla HTML principal
```

## 🚀 Instalación

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar Google Maps API**:
- Obtén una API key en [Google Cloud Console](https://console.cloud.google.com/)
- Edita `config.py` y reemplaza `YOUR_API_KEY_HERE` con tu key

3. **Ejecutar la aplicación**:
```bash
python app.py
```

4. **Abrir en navegador**:
```
http://localhost:5000
```

## 📋 Funcionalidades

### ✅ Gestión de Proyectos
- Crear, leer, actualizar y eliminar proyectos viales
- Visualización en tabla interactiva
- Detalles completos de cada proyecto

### 🗺️ Visualización Geográfica
- Mapa interactivo con Google Maps
- Rutas entre puntos de inicio y fin de proyectos
- Marcadores clickeables
- **Reactividad**: Al hacer clic en una fila de la tabla, la ruta se dibuja automáticamente en el mapa

### 📊 Análisis Histórico
- Total de proyectos
- Inversión total acumulada
- Longitud total de vías
- Costo promedio por kilómetro

### 🤖 Modelo Predictivo
- Predicción de costos basada en parámetros del proyecto
- Interfaz simple para ingreso de datos
- Preparado para integrar modelos SVR de scikit-learn

## 🎯 Separación de Responsabilidades

### Backend (`app.py`)
- Endpoints REST API
- Lógica de negocio
- Integración con base de datos
- Predicciones ML

### Modelos (`models.py`)
- Esquema de base de datos
- Operaciones CRUD
- Inicialización de datos

### Frontend (`static/js/app.js`)
- Estado de la aplicación (Vue reactivo)
- Interacción con API
- Lógica de UI
- Integración con Google Maps

### Estilos (`static/css/style.css`)
- Diseño visual
- Variables CSS para temas
- Responsive design

## 🛠️ Próximos Pasos

### 1. Integración de Modelos SVR
```python
# En app.py, reemplaza la predicción simple por tu modelo SVR
import joblib

model = joblib.load('modelo_svr.pkl')

@app.route('/api/predict', methods=['POST'])
def predict_cost():
    data = request.json
    features = [[data['longitud'], data['num_ufs']]]
    prediccion = model.predict(features)
    return jsonify({'costo_predicho': float(prediccion[0])})
```

### 2. Más Features del Modelo
- Agregar campos al formulario: tipo de terreno, región, complejidad
- Extender el modelo para usar más variables predictoras
- Crear endpoint para re-entrenar el modelo

### 3. Visualizaciones Avanzadas
- Gráficos con Chart.js o similar
- Dashboard con métricas en tiempo real
- Comparación de proyectos

### 4. Autenticación
```python
# Agregar Flask-Login para usuarios
from flask_login import LoginManager, login_required
```

### 5. Exportación de Datos
- CSV, Excel para reportes
- PDF para documentos oficiales

### 6. Validaciones
- Backend: Validar datos en endpoints
- Frontend: Mensajes de error amigables

## 🎨 Filosofía de Diseño

- **Simplicidad**: Sin bundlers, sin TypeScript, sin complejidad innecesaria
- **Reactividad**: Vue 3 proporciona reactividad elegante sin overhead
- **Belleza**: UI moderna con CSS limpio
- **Funcionalidad**: Todo funciona desde el primer momento
- **Escalabilidad**: Estructura preparada para crecer

## 🔑 API Endpoints

- `GET /api/proyectos` - Listar todos los proyectos
- `GET /api/proyectos/<id>` - Obtener un proyecto
- `POST /api/proyectos` - Crear proyecto
- `PUT /api/proyectos/<id>` - Actualizar proyecto
- `DELETE /api/proyectos/<id>` - Eliminar proyecto
- `POST /api/predict` - Predecir costo

## 💡 Consejos

1. **Google Maps API**: Asegúrate de habilitar "Directions API" y "Maps JavaScript API"
2. **Desarrollo**: Usa el modo debug de Flask para hot-reload
3. **Producción**: Cambia `SECRET_KEY` y usa Gunicorn/uWSGI
4. **Base de datos**: Para producción, migra a PostgreSQL

## 📚 Tecnologías

- Python 3.8+
- Flask 3.0
- Vue.js 3.3
- Google Maps API
- SQLite
- Scikit-learn

---

**Desarrollado como prototipo funcional para predicción de costos en proyectos viales** 🛣️

