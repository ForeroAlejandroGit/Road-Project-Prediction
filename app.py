from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from models import init_db, Proyecto, UnidadFuncional, Item
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

@app.route('/api/proyectos/codigo/<codigo>', methods=['GET'])
def get_proyecto_by_codigo(codigo):
    proyecto = Proyecto.get_by_codigo(codigo)
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

@app.route('/api/unidades-funcionales/<codigo>', methods=['GET'])
def get_unidades_funcionales(codigo):
    ufs = UnidadFuncional.get_by_codigo(codigo)
    return jsonify(ufs)

@app.route('/api/unidades-funcionales', methods=['POST'])
def create_unidad_funcional():
    data = request.get_json(silent=True) or {}
    uf_id = UnidadFuncional.create(data)
    return jsonify({'id': uf_id, 'message': 'Unidad funcional creada'}), 201

@app.route('/api/unidades-funcionales/<int:uf_id>', methods=['DELETE'])
def delete_unidad_funcional(uf_id):
    UnidadFuncional.delete(uf_id)
    return jsonify({'message': 'Unidad funcional eliminada'})

@app.route('/api/items/<codigo>', methods=['GET'])
def get_items(codigo):
    items = Item.get_by_codigo(codigo)
    return jsonify(items)

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json(silent=True) or {}
    item_id = Item.create(data)
    return jsonify({'id': item_id, 'message': 'Item creado'}), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json(silent=True) or {}
    Item.update(item_id, data)
    return jsonify({'message': 'Item actualizado'})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    Item.delete(item_id)
    return jsonify({'message': 'Item eliminado'})

@app.route('/api/predict', methods=['POST'])
def predict_cost():
    data = request.get_json(silent=True) or {}
    prediction = data['longitud'] * 50000 * (1 + data['num_ufs'] * 0.1)
    return jsonify({'costo_predicho': round(prediction, 2)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

