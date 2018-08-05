from flask import Flask, jsonify, request
from flask_cors import CORS
from io import BytesIO
from PIL import Image
import numpy as np
import base64

from main import encode, decode

app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route('/encode', methods=['POST'])
def hello_world():
    errors = []
    if 'image' not in request.files:
        errors.append('no image')
    if 'text' not in request.form:
        errors.append('no text')
    if 'key' not in request.form:
        errors.append('no key')
    if len(errors) > 0:
        return jsonify({'status': 400, 'errors': errors}), 400
    img_data = np.array(Image.open(request.files['image']).convert('RGBA'))
    encode(img_data, request.form['text'], request.form['key'])
    image = Image.fromarray(img_data, 'RGBA')
    img_io = BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    return jsonify({'status': 200, 'data': base64.b64encode(img_io.getvalue()).decode('utf-8')}), 200


@app.route('/decode', methods=['POST'])
def for_decode():
    errors = []
    if 'image' not in request.files:
        errors.append('no image')
    if 'key' not in request.form:
        errors.append('no key')
    if len(errors) > 0:
        return jsonify({'status': 400, 'errors': errors}), 400
    img_data = np.array(Image.open(request.files['image']).convert('RGBA'))
    return jsonify({'status': 200, 'data': decode(img_data, request.form['key'])})
