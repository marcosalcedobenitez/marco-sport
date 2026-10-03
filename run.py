from flask import Flask

from tienda.routes import tienda
from admin.routes import admin

from config.settings import SECRET_KEY


# ==========================================
# CREAR APLICACIÓN
# ==========================================

app = Flask(__name__)

app.secret_key = SECRET_KEY


# ==========================================
# REGISTRAR BLUEPRINTS
# ==========================================

app.register_blueprint(tienda)
app.register_blueprint(admin)


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )