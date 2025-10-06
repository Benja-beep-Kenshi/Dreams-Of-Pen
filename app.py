from flask import Flask, render_template

app = Flask(__name__, template_folder="Templates", static_folder="Static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/Reseñas")
def reseñas():
    return render_template("Reseñas.html")


@app.route("/Mis reseñas")
def misr():
    return render_template("Mis reseñas.html")


@app.route("/Ver Reseñas")
def verRe():
    return render_template("Ver Reseñas.html")


@app.route("/crear")
def crear():
    return render_template("crear.html")


@app.route("/vermias")
def verMias():
    return render_template("vermias.html")


@app.route("/busquedaMarca")
def BusM():
    return render_template("busquedaMarca.html")


@app.route("/busquedaUsuario")
def BusU():
    return render_template("busquedaUsuario.html")


if __name__ == "__main__":
    app.run(debug=True)
