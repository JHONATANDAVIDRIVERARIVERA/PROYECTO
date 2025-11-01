from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
import logging
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
from datetime import timedelta
import threading

# Variables globales para TensorFlow/modelo
load_model = None
image = None
model = None
np = None

# Intentar importar TensorFlow y NumPy (opcional)
try:
    import numpy as np
    from tensorflow.keras.models import load_model as tf_load_model
    from tensorflow.keras.preprocessing import image as tf_image
    
    # Si la importación tiene éxito, asignamos las funciones
    load_model = tf_load_model
    image = tf_image
    
    # Intentar cargar el modelo
    try:
        model = load_model('garbage_model.h5')
        print("[INFO] Modelo cargado correctamente")
        logging.info('Modelo cargado correctamente en import inicial')
    except Exception as e:
        print("[WARN] No se pudo cargar el modelo:", e)
        logging.warning('No se pudo cargar el modelo en import inicial: %s', e)
except ImportError as e:
    print("[INFO] TensorFlow/NumPy no disponible, funcionando en modo simulación:", e)
    logging.warning('TensorFlow/NumPy no disponible en import inicial: %s', e)

# =========================
# CONFIGURACIÓN FLASK
# =========================
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Logging básico a archivo para diagnóstico
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'app.log'),
    level=logging.INFO,
    format='%(asctime)s [PID:%(process)d] %(levelname)s: %(message)s'
)
logging.info('Aplicación (app.py) cargada — logging inicializado')
# Secret key para sesiones (en producción usa una variable de entorno segura)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
# Hacer que las sesiones sean permanentes por defecto y duren 30 días
app.permanent_session_lifetime = timedelta(days=30)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# BASE DE DATOS DE USUARIOS (SQLite)
# =========================
DB_PATH = Path(__file__).parent / 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Crear tabla de usuarios si no existe y añadir usuario admin por defecto
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Asegurar usuario admin por defecto (solo creación inicial)
    try:
        cur.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if cur.fetchone() is None:
            hashed = generate_password_hash('admin123')
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', hashed))
            conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()

# Inicializar DB al importar
init_db()
# =========================
# CONFIGURACIÓN DEL MODELO
# =========================
MODEL_PATH = 'garbage_model.h5'

# Debes usar las mismas clases detectadas en el entrenamiento
CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

# Si existe class_indices.json (guardado por train.py), cargar el orden real de clases
try:
    import json
    # Usar ruta absoluta relativa al archivo para evitar problemas de working dir en PaaS
    CI_PATH = Path(__file__).parent / 'class_indices.json'
    if CI_PATH.exists():
        try:
            with open(CI_PATH, 'r', encoding='utf-8') as fh:
                ci = json.load(fh)
            # invertir mapping {class: index} -> list ordered by index
            max_index = max(ci.values())
            labels = [None] * (max_index + 1)
            for cls, idx in ci.items():
                labels[idx] = cls
            CLASS_NAMES = labels
            print('[INFO] Cargado class_indices.json desde', CI_PATH, 'clases ordenadas:', CLASS_NAMES)
            logging.info('Cargado class_indices.json desde %s', CI_PATH)
        except Exception as e:
            print('[WARN] Error leyendo/parsing class_indices.json:', e)
            logging.warning('Error leyendo/parsing %s: %s', CI_PATH, e)
    else:
        print('[INFO] No se encontró class_indices.json en', CI_PATH)
        logging.info('No se encontró class_indices.json en %s', CI_PATH)
except Exception as e:
    print('[WARN] No se pudo intentar cargar class_indices.json:', e)
    logging.warning('No se pudo intentar cargar class_indices.json: %s', e)

# Diccionario con información de cada tipo de residuo
INFO_RESIDUOS = {
    "cardboard": {
        "nombre": "Cartón",
        "descripcion": "El cartón es un material compuesto principalmente de fibra de papel reciclado. Se utiliza en cajas, empaques y envases.",
        "contenedor": "Contenedor azul o de papel y cartón.",
        "razon": "Debe ir en este contenedor porque puede reciclarse para fabricar nuevos productos de papel."
    },
    "glass": {
        "nombre": "Vidrio",
        "descripcion": "El vidrio es un material inorgánico, duro y transparente utilizado en botellas, frascos y envases.",
        "contenedor": "Contenedor verde.",
        "razon": "El vidrio puede reciclarse indefinidamente sin perder calidad, por eso se separa del resto."
    },
    "metal": {
        "nombre": "Metal",
        "descripcion": "Incluye envases de aluminio, latas y otros objetos metálicos reciclables.",
        "contenedor": "Contenedor amarillo.",
        "razon": "El metal puede fundirse y reutilizarse, reduciendo el uso de materias primas."
    },
    "paper": {
        "nombre": "Papel",
        "descripcion": "El papel proviene de fibras vegetales procesadas y se usa en hojas, cuadernos y sobres.",
        "contenedor": "Contenedor azul.",
        "razon": "Es reciclable y se transforma en nuevos productos de papel, ayudando a conservar los bosques."
    },
    "plastic": {
        "nombre": "Plástico",
        "descripcion": "Material sintético derivado del petróleo, usado en botellas, envoltorios y envases.",
        "contenedor": "Contenedor amarillo.",
        "razon": "El plástico se recicla para fabricar nuevos productos, reduciendo la contaminación ambiental."
    },
    "trash": {
        "nombre": "Desechos no reciclables",
        "descripcion": "Son residuos que no pueden reciclarse, como servilletas sucias, pañales o colillas.",
        "contenedor": "Contenedor gris o negro.",
        "razon": "Estos residuos deben ir al vertedero o tratamiento especial, ya que no son reciclables."
    }
}

# =========================
# RUTA PRINCIPAL
# =========================
@app.route('/')
def index():
    # Página principal protegida; requiere login
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', prediction=None, user=session.get('user'))

# =========================
# RUTA PARA SUBIR Y CLASIFICAR
# =========================
@app.route('/predict', methods=['POST'])
def upload():
    # Proteger esta ruta
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files.get('file')
    if not file:
        return render_template('index.html', prediction="No se subió ninguna imagen.")
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # No intentar recargar el modelo sin autorización (evita bloquear la petición).
    # El modelo se carga en background al arrancar y existe la ruta /reload_model
    # para administradores. Si no está cargado, devolvemos un mensaje claro.
    global model
    if model is None or load_model is None or image is None or np is None:
        logging.info('Predict requested but model not loaded in this process (PID=%d)', os.getpid())

    # Si no tenemos TensorFlow o el modelo, avisamos claramente y NO devolvemos una
    # predicción simulada (evita confundir a usuarios remotos).
    prediction_override = None
    if model is None or image is None or np is None:
        # No devolvemos una etiqueta ficticia; mostramos mensaje claro en la UI
        prediction_override = ('Modelo no cargado en este proceso. Inicia sesión como admin y pulsa "Recargar modelo" o reinicia la aplicación.')
        # Avisar al usuario/admin para recargar modelo (si no está cargado en este proceso)
        flash('Modelo no cargado en el servidor; por favor recarga o reinicia la app (admin).', 'error')
        logging.warning('Modelo no cargado (predicción no disponible) para %s (PID=%d)', filepath, os.getpid())
    else:
        try:
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
            logging.info('Predicción real para %s -> %s (%.2f%%) [PID=%d]', filepath, result, confidence, os.getpid())
        except Exception as e:
            print("[ERROR] Error al procesar imagen:", e)
            logging.error('Error procesando imagen %s: %s', filepath, e)
            result = 'error'
            confidence = 0.0

    info = INFO_RESIDUOS.get(result, None) if (model is not None and result is not None) else None

    # Si definimos un override de mensaje (ej. modelo no cargado), usarlo para la UI
    if prediction_override is not None:
        prediction_text = prediction_override
    else:
        prediction_text = f"Predicción: {result} ({confidence:.2f}% confianza)"

    return render_template(
        'index.html',
        prediction=prediction_text,
        img_path=filepath,
        info=info
    )




# =========================
# AUTENTICACIÓN SIMPLE
# =========================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('user') != 'admin':
            flash('Acceso restringido: se requiere usuario admin.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Por favor ingresa usuario y contraseña.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row['password'], password):
            session['user'] = username
            # Mantener la sesión incluso si el usuario cierra el navegador
            session.permanent = True
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales inválidas.', 'error')
            return render_template('login.html')

    # GET
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not username or not password:
            flash('Usuario y contraseña requeridos.', 'error')
            return render_template('register.html')
        if password != password2:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('register.html')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            hashed = generate_password_hash(password)
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('El usuario ya existe.', 'error')
            conn.close()
            return render_template('register.html')
        except sqlite3.Error:
            flash('Error al crear usuario.', 'error')
            conn.close()
            return render_template('register.html')
        conn.close()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        # Crear nuevo usuario desde formulario admin
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Usuario y contraseña requeridos.', 'error')
        else:
            try:
                hashed = generate_password_hash(password)
                cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
                conn.commit()
                flash(f'Usuario "{username}" creado.', 'success')
            except sqlite3.IntegrityError:
                flash('El usuario ya existe.', 'error')
            except sqlite3.Error:
                flash('Error al crear usuario.', 'error')

    cur.execute('SELECT id, username FROM users ORDER BY username')
    rows = cur.fetchall()
    conn.close()
    return render_template('users.html', users=rows, user=session.get('user'))



@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    if not row:
        flash('Usuario no encontrado.', 'error')
        conn.close()
        return redirect(url_for('users'))

    username = row['username']
    # No permitir eliminar admin
    if username == 'admin':
        flash('No se puede eliminar el usuario admin.', 'error')
        conn.close()
        return redirect(url_for('users'))

    # Evitar que el admin se elimine a sí mismo accidentalmente
    if username == session.get('user'):
        flash('No puedes eliminar la sesión actualmente iniciada.', 'error')
        conn.close()
        return redirect(url_for('users'))

    try:
        cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash(f'Usuario "{username}" eliminado.', 'success')
    except sqlite3.Error:
        flash('Error al eliminar usuario.', 'error')
    finally:
        conn.close()

    return redirect(url_for('users'))


def reload_model_from_disk():
    """Intenta recargar el modelo desde disco y actualiza la variable global `model`.
    Devuelve (ok: bool, message: str).
    """
    global model, load_model, image, np
    # Si las funciones de TF no están disponibles en este proceso, intentar importarlas dinámicamente
    if load_model is None or image is None or np is None:
        try:
            import numpy as _np
            from tensorflow.keras.models import load_model as _tf_load_model
            from tensorflow.keras.preprocessing import image as _tf_image
            # asignar a variables globales
            np = _np
            load_model = _tf_load_model
            image = _tf_image
        except Exception as e:
            logging.error('Error importando TensorFlow/NumPy en reload_model_from_disk: %s', e)
            return False, f'TensorFlow/NumPy no disponible o error al importarlos: {e}'

    try:
        new_model = load_model(MODEL_PATH)
        model = new_model
        logging.info('Modelo recargado desde %s', MODEL_PATH)
        return True, f'Modelo recargado desde {MODEL_PATH}'
    except Exception as e:
        logging.error('Error recargando el modelo desde %s: %s', MODEL_PATH, e)
        return False, f'Error recargando el modelo: {e}'


@app.route('/reload_model', methods=['POST'])
@admin_required
def reload_model():
    ok, msg = reload_model_from_disk()
    if ok:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('index'))


@app.route('/model_status', methods=['GET'])
@admin_required
def model_status():
    """Devuelve el estado del modelo cargado (solo admin)."""
    return jsonify({
        'loaded': model is not None,
        'model_path': MODEL_PATH,
        'class_names': CLASS_NAMES
    })


@app.route('/public_model_status', methods=['GET'])
def public_model_status():
    """Estado público del modelo (para la UI)."""
    return jsonify({
        'loaded': model is not None,
        'model_path': MODEL_PATH if model is not None else None
    })


@app.route('/whoami', methods=['GET'])
def whoami():
    """Endpoint de diagnóstico: devuelve el PID del proceso y si el modelo está cargado.
    Útil para depurar qué proceso atendió la petición desde clientes remotos.
    """
    try:
        pid = os.getpid()
    except Exception:
        pid = None
    return jsonify({
        'pid': pid,
        'model_loaded': model is not None,
        'model_path': MODEL_PATH if model is not None else None
    })


# Ruta para recolectar ejemplos etiquetados y guardarlos en dataset/<clase>
@app.route('/collect', methods=['GET', 'POST'])
@admin_required
def collect():
    """Formulario simple (solo admin) para subir imágenes etiquetadas
    y guardarlas en la carpeta correspondiente dentro de `dataset/`.
    """
    if request.method == 'POST':
        clase = request.form.get('clase')
        file = request.files.get('file')
        if not clase or not file:
            flash('Selecciona una clase y un archivo.', 'error')
            return redirect(url_for('collect'))

        # Asegurar que la carpeta de la clase existe
        dataset_dir = os.path.join(os.path.dirname(__file__), 'dataset')
        target_dir = os.path.join(dataset_dir, clase)
        os.makedirs(target_dir, exist_ok=True)

        # Guardar con nombre único
        filename = file.filename
        base, ext = os.path.splitext(filename)
        i = 1
        dest_name = filename
        while os.path.exists(os.path.join(target_dir, dest_name)):
            dest_name = f"{base}_{i}{ext}"
            i += 1

        dest_path = os.path.join(target_dir, dest_name)
        file.save(dest_path)
        flash(f'Imagen guardada en dataset/{clase}/{dest_name}', 'success')
        return redirect(url_for('collect'))

    # GET: mostrar formulario
    clases = CLASS_NAMES
    return render_template('collect.html', clases=clases, user=session.get('user'))

# =========================
# RUTAS DE LAS PÁGINAS DEL MENÚ
# =========================
@app.route('/pagina1')
@login_required
def pagina1():
    return render_template('pagina1.html', user=session.get('user'))

@app.route('/pagina2')
@login_required
def pagina2():
    return render_template('pagina2.html', user=session.get('user'))

@app.route('/pagina3')
@login_required
def pagina3():
    return render_template('pagina3.html', user=session.get('user'))

# =========================
# EJECUTAR SERVIDOR
# =========================
# Registrar handler para cargar el modelo cuando el proceso empiece a servir peticiones.
# Usamos before_serving si está disponible (Flask >=2.0/2.3), si no, intentamos
# before_first_request; como último recurso intentamos recargar inmediatamente.
if hasattr(app, 'before_serving'):
    @app.before_serving
    def load_model_on_start():
        ok, msg = reload_model_from_disk()
        if ok:
            print(f"[INFO] {msg} (cargado en proceso)")
        else:
            print(f"[WARN] {msg} (no cargado en proceso)")
elif hasattr(app, 'before_first_request'):
    @app.before_first_request
    def load_model_on_first_request():
        ok, msg = reload_model_from_disk()
        if ok:
            print(f"[INFO] {msg} (cargado en proceso)")
        else:
            print(f"[WARN] {msg} (no cargado en proceso)")
else:
    # Fallback: intentar cargar ahora (puede bloquear el arranque)
    ok, msg = reload_model_from_disk()
    if ok:
        print(f"[INFO] {msg} (cargado en proceso - fallback inmediato)")
    else:
        print(f"[WARN] {msg} (no cargado en proceso - fallback inmediato)")

if __name__ == '__main__':
    # Allow configuring host/port via environment variables. Many PaaS
    # (Render/Heroku) set $PORT — prefer that if present.
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    # Prefer the standard PORT env var used by many hosts (Render, Heroku)
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', '5000')))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('1','true','yes')

    # Start model loading in background so startup isn't blocked by TensorFlow
    # initialization (helps prevent platform timeouts / 502 on first deploy).
    def _bg_load():
        logging.info('Background model loader thread started (PID=%s)', os.getpid())
        ok, msg = reload_model_from_disk()
        if ok:
            logging.info('Background loader: %s', msg)
        else:
            logging.warning('Background loader failed: %s', msg)

    t = threading.Thread(target=_bg_load, daemon=True)
    t.start()

    app.run(debug=debug, host=host, port=port)
