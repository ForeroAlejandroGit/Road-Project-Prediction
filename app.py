from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from src.config import Config
import src.models_management as models_management

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)



