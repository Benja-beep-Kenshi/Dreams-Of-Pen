import sqlite3
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, request, url_for, session

app = Flask(__name__)
app.secret_key = "clave_ultra_secreta"

DB_NAME = "dreamsOfPen.db"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpeta de uploads si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
#  CREAR BD Y TABLAS SI NO EXISTEN
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lapicera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            id_marca INTEGER NOT NULL,
            FOREIGN KEY (id_marca) REFERENCES marca(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            puntuacion INTEGER NOT NULL,
            id_usuario INTEGER NOT NULL,
            id_lapicera INTEGER NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id),
            FOREIGN KEY (id_lapicera) REFERENCES lapicera(id)
        )
    """)

    conn.commit()
    conn.close()


# ===================== HELPERS ===============================

def query(sql, params=(), one=False):
    """Consulta que devuelve diccionarios, no tuplas."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    data = cursor.fetchall()
    conn.close()
    return (data[0] if data else None) if one else data


def execute(sql, params=()):
    """Ejecutar INSERT/UPDATE/DELETE."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()


# ===================== LÓGICA DE USUARIOS ====================

def get_usuario_id(nombre):
    row = query("SELECT id FROM usuario WHERE user_name = ?", (nombre,), one=True)
    return row["id"] if row else None


def asegurar_usuario(nombre):
    uid = get_usuario_id(nombre)
    if uid:
        return uid
    execute("INSERT INTO usuario (user_name) VALUES (?)", (nombre,))
    return get_usuario_id(nombre)


def asegurar_marca(nombre):
    row = query("SELECT id FROM marca WHERE nombre = ?", (nombre,), one=True)
    if row:
        return row["id"]
    execute("INSERT INTO marca (nombre) VALUES (?)", (nombre,))
    return query("SELECT id FROM marca WHERE nombre = ?", (nombre,), one=True)["id"]


def asegurar_lapicera(modelo, id_marca):
    row = query("SELECT id FROM lapicera WHERE modelo = ? AND id_marca = ?", (modelo, id_marca), one=True)
    if row:
        return row["id"]
    execute("INSERT INTO lapicera (modelo, id_marca) VALUES (?, ?)", (modelo, id_marca))
    return query("SELECT id FROM lapicera WHERE modelo = ? AND id_marca = ?", (modelo, id_marca), one=True)["id"]


# ===================== RUTAS ================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    nombre = request.form.get("usuario")
    if not nombre:
        return redirect(url_for("index"))
    asegurar_usuario(nombre)
    session["usuario"] = nombre
    return redirect(url_for("resenas"))


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("index"))


@app.route("/resenas")
def resenas():
    if "usuario" not in session:
        return redirect(url_for("index"))
    return render_template("resenas.html")


@app.route("/ver_resenas")
def ver_resenas():
    if "usuario" not in session:
        return redirect(url_for("index"))
    return render_template("ver_resenas.html")


@app.route("/mis_resenas")
def mis_resenas():
    nombre = session.get("usuario")
    if not nombre:
        return redirect(url_for("index"))
    return render_template("mis_resenas.html")


@app.route("/crear", methods=["GET", "POST"])
def crear():
    nombre = session.get("usuario")
    if not nombre:
        return redirect(url_for("index"))
        
    if request.method == "POST":
        marca = request.form.get("marca")
        modelo = request.form.get("modelo")
        texto = request.form.get("texto")
        puntuacion = int(request.form.get("puntuacion"))

        uid = asegurar_usuario(nombre)
        mid = asegurar_marca(marca)
        lid = asegurar_lapicera(modelo, mid)

        execute("""
            INSERT INTO review (texto, puntuacion, id_usuario, id_lapicera)
            VALUES (?, ?, ?, ?)
        """, (texto, puntuacion, uid, lid))

        return redirect(url_for("vermias"))

    return render_template("crear.html")


@app.route("/vermias")
def vermias():
    nombre = session.get("usuario")
    if not nombre:
        return redirect(url_for("index"))
    uid = get_usuario_id(nombre)

    datos = query("""
        SELECT lapicera.modelo AS modelo,
               marca.nombre AS marca,
               review.puntuacion AS puntuacion,
               review.texto AS texto
        FROM review
        JOIN lapicera ON review.id_lapicera = lapicera.id
        JOIN marca ON lapicera.id_marca = marca.id
        WHERE review.id_usuario = ?
        ORDER BY review.id DESC
    """, (uid,))

    return render_template("vermias.html", reviews=datos)


@app.route("/busquedaMarca", methods=["GET", "POST"])
def busquedaMarca():
    if "usuario" not in session:
        return redirect(url_for("index"))
        
    resultados = []
    if request.method == "POST":
        marca = request.form.get("marca")
        resultados = query("""
            SELECT usuario.user_name AS usuario,
                   lapicera.modelo AS modelo,
                   marca.nombre AS marca,
                   review.puntuacion AS puntuacion,
                   review.texto AS texto
            FROM review
            JOIN usuario ON review.id_usuario = usuario.id
            JOIN lapicera ON review.id_lapicera = lapicera.id
            JOIN marca ON lapicera.id_marca = marca.id
            WHERE marca.nombre LIKE ?
        """, ("%" + marca + "%",))

    return render_template("busquedaMarca.html", reviews=resultados)


@app.route("/busquedaUsuario", methods=["GET", "POST"])
def busquedaUsuario():
    if "usuario" not in session:
        return redirect(url_for("index"))
        
    resultados = []
    if request.method == "POST":
        usuario = request.form.get("usuario")
        resultados = query("""
            SELECT usuario.user_name AS usuario,
                   lapicera.modelo AS modelo,
                   marca.nombre AS marca,
                   review.puntuacion AS puntuacion,
                   review.texto AS texto
            FROM review
            JOIN usuario ON review.id_usuario = usuario.id
            JOIN lapicera ON review.id_lapicera = lapicera.id
            JOIN marca ON lapicera.id_marca = marca.id
            WHERE usuario.user_name = ?
        """, (usuario,))

    return render_template("busquedaUsuario.html", reviews=resultados)



# ============================================================
#  INICIALIZAR BD Y CORRER
# ============================================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)