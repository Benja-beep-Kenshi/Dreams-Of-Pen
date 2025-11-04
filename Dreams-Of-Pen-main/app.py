from flask import Flask, render_template

app = Flask(__name__)

#codigo a completar


@app.route('/')

def index():
    return render_template('index.html')

@app.route('/Reseñas')
def reseñas():
    return render_template('Reseñas.html')

@app.route('/Mis reseñas')
def mis_reseñas():
    return render_template('Mis reseñas.html')

@app.route('/Ver Reseñas')
def ver_reseñas():
    return render_template('Ver Reseñas.html')

@app.route('/crear')
def crear():
    return render_template('crear.html')

@app.route('/vermias')
def vermias():
    return render_template('vermias.html')

@app.route('/busquedaMarca')
def busquedamarca():
    return render_template('busquedaMarca.html')

@app.route('/busquedaUsuario')
def busquedausuario():
    return render_template('busquedaUsuario.html')

if __name__ == '__main__':
    app.run(debug=True)
