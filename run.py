import os

from flask import Flask, send_from_directory

from tienda.routes import tienda
from admin.routes import admin
from config.settings import SECRET_KEY, PRODUCTOS_DIR

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(tienda)
app.register_blueprint(admin)


@app.route("/media/<path:nombre_archivo>")
def servir_imagen(nombre_archivo):
    return send_from_directory(
        PRODUCTOS_DIR,
        nombre_archivo
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
