from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path

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
    except Exception as e:
        print("[WARN] No se pudo cargar el modelo:", e)
except ImportError as e:
    print("[INFO] TensorFlow/NumPy no disponible, funcionando en modo simulación:", e)

# =========================
# CONFIGURACIÓN FLASK
# =========================
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Secret key para sesiones (en producción usa una variable de entorno segura)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
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

    # Si no tenemos TensorFlow o el modelo, usamos predicción simulada
    if model is None or image is None or np is None:
        # Predicción simulada (útil para probar la UI sin TensorFlow)
        result = 'plastic'
        confidence = 75.0
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
        except Exception as e:
            print("[ERROR] Error al procesar imagen:", e)
            result = 'error'
            confidence = 0.0

    info = INFO_RESIDUOS.get(result, None)

    return render_template(
        'index.html',
        prediction=f"Predicción: {result} ({confidence:.2f}% confianza)",
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

# =========================
# EJECUTAR SERVIDOR
# =========================
if __name__ == '__main__':
    app.run(debug=True)
