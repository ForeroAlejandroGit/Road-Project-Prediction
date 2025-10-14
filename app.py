from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from models import init_db, Proyecto
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

init_db()

@app.route('/')
def index():
    return render_template('index.html', maps_api_key=Config.GOOGLE_MAPS_API_KEY)

@app.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    proyectos = Proyecto.get_all()
    return jsonify(proyectos)

@app.route('/api/proyectos/<int:proyecto_id>', methods=['GET'])
def get_proyecto(proyecto_id):
    proyecto = Proyecto.get_by_id(proyecto_id)
    if proyecto:
        return jsonify(proyecto)
    return jsonify({'error': 'Proyecto no encontrado'}), 404

@app.route('/api/proyectos', methods=['POST'])
def create_proyecto():
    data = request.get_json(silent=True) or {}
    proyecto_id = Proyecto.create(data)
    return jsonify({'id': proyecto_id, 'message': 'Proyecto creado'}), 201

@app.route('/api/proyectos/<int:proyecto_id>', methods=['PUT'])
def update_proyecto(proyecto_id):
    data = request.get_json(silent=True) or {}
    Proyecto.update(proyecto_id, data)
    return jsonify({'message': 'Proyecto actualizado'})

@app.route('/api/proyectos/<int:proyecto_id>', methods=['DELETE'])
def delete_proyecto(proyecto_id):
    Proyecto.delete(proyecto_id)
    return jsonify({'message': 'Proyecto eliminado'})

@app.route('/api/predict', methods=['POST'])
def predict_cost():
    data = request.get_json(silent=True) or {}
    prediction = data['longitud'] * 50000 * (1 + data['num_ufs'] * 0.1)
    return jsonify({'costo_predicho': round(prediction, 2)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

