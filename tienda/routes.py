from flask import Blueprint, render_template

from services.productos import obtener_productos


# ==========================================
# BLUEPRINT DE LA TIENDA
# ==========================================

tienda = Blueprint(
    "tienda",
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@tienda.route("/")
def inicio():
    productos = obtener_productos()

    return render_template(
        "tienda.html",
        productos=productos
    )