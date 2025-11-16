import mysql.connector
from flask import Flask, render_template, redirect, request, url_for, session

app = Flask(__name__)
app.secret_key = "clave_ultra_secreta_para_sesiones"  # cambia si querés

# -------------------------
# Conexión a MySQL
# -------------------------
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="dreamsOfPen"
)
cursor = conexion.cursor(dictionary=True)

# -------------------------
# Helpers
# -------------------------
def get_usuario_id(nombre):
    """Devuelve id de usuario o None"""
    cursor.execute("SELECT id FROM usuario WHERE user_name = %s", (nombre,))
    row = cursor.fetchone()
    return row["id"] if row else None

def asegurar_usuario(nombre):
    """Crea el usuario si no existe y devuelve su id"""
    uid = get_usuario_id(nombre)
    if uid:
        return uid
    cursor.execute("INSERT INTO usuario (user_name) VALUES (%s)", (nombre,))
    conexion.commit()
    return cursor.lastrowid

def asegurar_marca(nombre):
    cursor.execute("SELECT id FROM marca WHERE nombre = %s", (nombre,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("INSERT INTO marca (nombre) VALUES (%s)", (nombre,))
    conexion.commit()
    return cursor.lastrowid

def asegurar_lapicera(modelo, id_marca):
    cursor.execute("SELECT id FROM lapicera WHERE modelo = %s AND id_marca = %s", (modelo, id_marca))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("INSERT INTO lapicera (modelo, id_marca) VALUES (%s, %s)", (modelo, id_marca))
    conexion.commit()
    return cursor.lastrowid

# -------------------------
# INDEX (login simple expected)
# -------------------------
@app.route("/")
def index():
    # index.html en tu repo tiene un "Ingresar" (no necesariamente un form)
    # Si querés que Ingresar haga POST, cambiá el template para enviar a /login
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    # intenta obtener usuario desde el formulario
    nombre = request.form.get("usuario")
    if not nombre:
        return redirect(url_for("index"))
    # aseguramos usuario en DB y guardamos en session
    asegurar_usuario(nombre)
    session["usuario"] = nombre
    return redirect(url_for("resenas"))

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("index"))

# -------------------------
# MENU PRINCIPAL (Reseñas)
# -------------------------
@app.route("/resenas")
def resenas():
    return render_template("resenas.html")

# -------------------------
# VER TODAS LAS RESEÑAS
# -------------------------
@app.route("/ver_resenas")
def ver_resenas():
    cursor.execute("""
        SELECT 
            usuario.user_name AS usuario,
            lapicera.modelo AS modelo,
            marca.nombre AS marca,
            review.puntuacion AS puntuacion,
            review.texto AS texto
        FROM review
        JOIN usuario ON review.id_usuario = usuario.id
        JOIN lapicera ON review.id_lapicera = lapicera.id
        JOIN marca ON lapicera.id_marca = marca.id
        ORDER BY review.id DESC
    """)
    datos = cursor.fetchall()
    return render_template("ver_resenas.html", reviews=datos)

# -------------------------
# MIS RESEÑAS
# -------------------------
@app.route("/mis_resenas")
def mis_resenas():
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("index"))
    uid = get_usuario_id(usuario)
    if not uid:
        return render_template("mis_resenas.html", reviews=[])
    cursor.execute("""
        SELECT 
            lapicera.modelo AS modelo,
            marca.nombre AS marca,
            review.puntuacion AS puntuacion,
            review.texto AS texto
        FROM review
        JOIN lapicera ON review.id_lapicera = lapicera.id
        JOIN marca ON lapicera.id_marca = marca.id
        WHERE review.id_usuario = %s
        ORDER BY review.id DESC
    """, (uid,))
    datos = cursor.fetchall()
    return render_template("mis_resenas.html", reviews=datos)

# -------------------------
# CREAR RESEÑA
# -------------------------
@app.route("/crear", methods=["GET", "POST"])
def crear():
    usuario = session.get("usuario")
    if request.method == "POST":
        # campos esperados (según los templates que armamos)
        marca = request.form.get("marca") or request.form.get("titulo") or ""
        modelo = request.form.get("modelo") or ""
        texto = request.form.get("texto") or request.form.get("reseña") or request.form.get("descripcion") or ""
        puntuacion = request.form.get("puntuacion") or request.form.get("puntuación") or None

        # convertimos puntuacion a int si viene
        try:
            puntuacion = int(puntuacion) if puntuacion is not None and puntuacion != "" else None
        except ValueError:
            puntuacion = None

        # si no hay usuario en sesión, lo dejamos 'Invitado' y lo creamos
        if not usuario:
            usuario = "Invitado"
            asegurar_usuario(usuario)

        uid = asegurar_usuario(usuario)
        mid = asegurar_marca(marca)
        lid = asegurar_lapicera(modelo, mid)

        # si no vino puntuacion, ponemos 0
        if puntuacion is None:
            puntuacion = 0

        cursor.execute("""
            INSERT INTO review (texto, puntuacion, id_usuario, id_lapicera)
            VALUES (%s, %s, %s, %s)
        """, (texto, puntuacion, uid, lid))
        conexion.commit()
        return redirect(url_for("ver_resenas"))

    # GET -> mostrar formulario. En algunos templates podrías querer pasar marcas existentes
    cursor.execute("SELECT id, nombre FROM marca ORDER BY nombre")
    marcas = cursor.fetchall()
    return render_template("crear.html", marcas=marcas)

# -------------------------
# VERMIA(S) - ver mis (mantengo endpoint que tenías)
# -------------------------
@app.route("/vermias")
def vermias():
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("index"))
    uid = get_usuario_id(usuario)
    if not uid:
        return render_template("vermias.html", reviews=[])
    cursor.execute("""
        SELECT 
            lapicera.modelo AS modelo,
            marca.nombre AS marca,
            review.puntuacion AS puntuacion,
            review.texto AS texto
        FROM review
        JOIN lapicera ON review.id_lapicera = lapicera.id
        JOIN marca ON lapicera.id_marca = marca.id
        WHERE review.id_usuario = %s
        ORDER BY review.id DESC
    """, (uid,))
    datos = cursor.fetchall()
    return render_template("vermias.html", reviews=datos)

# -------------------------
# BUSQUEDA POR MARCA
# -------------------------
@app.route("/busquedaMarca", methods=["GET", "POST"])
def busquedaMarca():
    resultados = []
    if request.method == "POST":
        marca = request.form.get("marca") or request.form.get("q") or ""
        cursor.execute("""
            SELECT 
                usuario.user_name AS usuario,
                lapicera.modelo AS modelo,
                marca.nombre AS marca,
                review.puntuacion AS puntuacion,
                review.texto AS texto
            FROM review
            JOIN usuario ON review.id_usuario = usuario.id
            JOIN lapicera ON review.id_lapicera = lapicera.id
            JOIN marca ON lapicera.id_marca = marca.id
            WHERE marca.nombre LIKE %s
            ORDER BY review.id DESC
        """, ("%" + marca + "%",))
        resultados = cursor.fetchall()
    return render_template("busquedaMarca.html", reviews=resultados)

# -------------------------
# BUSQUEDA POR USUARIO
# -------------------------
@app.route("/busquedaUsuario", methods=["GET", "POST"])
def busquedaUsuario():
    resultados = []
    if request.method == "POST":
        usuario = request.form.get("usuario") or request.form.get("q") or ""
        cursor.execute("""
            SELECT 
                usuario.user_name AS usuario,
                lapicera.modelo AS modelo,
                marca.nombre AS marca,
                review.puntuacion AS puntuacion,
                review.texto AS texto
            FROM review
            JOIN usuario ON review.id_usuario = usuario.id
            JOIN lapicera ON review.id_lapicera = lapicera.id
            JOIN marca ON lapicera.id_marca = marca.id
            WHERE usuario.user_name = %s
            ORDER BY review.id DESC
        """, (usuario,))
        resultados = cursor.fetchall()
    return render_template("busquedaUsuario.html", reviews=resultados)

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
