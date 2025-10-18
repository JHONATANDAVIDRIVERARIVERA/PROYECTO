from flask import Flask, render_template, request
import numpy as np
import os

# Intentamos importar TensorFlow; si falla, dejamos que la app siga funcionando
TF_AVAILABLE = True
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
except Exception as e:
    TF_AVAILABLE = False
    load_model = None
    image = None
    print("[WARN] TensorFlow no está disponible. Funcionamiento en modo 'mock' ->", e)

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
model = None
if TF_AVAILABLE:
    try:
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"[WARN] No se pudo cargar el modelo '{MODEL_PATH}':", e)
        model = None

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

    # Si el modelo no está disponible, devolvemos una predicción simulada
    if model is None:
        # Predicción simulada (útil para probar la UI sin TensorFlow)
        result = 'plastic'
        confidence = 75.0
    else:
        # Preprocesar imagen
        img = image.load_img(filepath, target_size=(128, 128))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0

        # Predicción real
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
