from flask import Flask, render_template, request
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os

# =========================
# CONFIGURACIÓN FLASK
# =========================
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# =========================
# CARGAR EL MODELO
# =========================
MODEL_PATH = 'garbage_model.h5'
model = load_model(MODEL_PATH)

# Debes usar las mismas clases detectadas en el entrenamiento
CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

# =========================
# RUTA PRINCIPAL
# =========================
@app.route('/')
def index():
    return render_template('index.html', prediction=None)

# =========================
# RUTA PARA SUBIR Y CLASIFICAR
# =========================
@app.route('/predict', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        return render_template('index.html', prediction="No se subió ninguna imagen.")
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Preprocesar imagen
    img = image.load_img(filepath, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    # Predicción
    predictions = model.predict(img_array)
    class_index = np.argmax(predictions)
    result = CLASS_NAMES[class_index]
    confidence = predictions[0][class_index] * 100

    return render_template('index.html', 
                           prediction=f"Predicción: {result} ({confidence:.2f}% confianza)", 
                           img_path=filepath)

# =========================
# EJECUTAR SERVIDOR
# =========================
if __name__ == '__main__':
    app.run(debug=True)
