from flask import Blueprint, render_template, request, abort

from services.productos import (
    obtener_productos,
    obtener_producto
)


tienda = Blueprint(
    "tienda",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/tienda-static"
)


def convertir_precio(precio):
    try:
        texto = str(precio or "")

        numeros = "".join(
            caracter
            for caracter in texto
            if caracter.isdigit()
        )

        if not numeros:
            return 0

        return int(numeros)

    except Exception:
        return 0


def preparar_tallas(producto):
    stock = producto.get("stock") or {}

    tallas = []

    for talla, cantidad in stock.items():

        try:
            if int(cantidad) > 0:
                tallas.append(str(talla))

        except (ValueError, TypeError):
            continue

    tallas.sort(
        key=lambda talla:
        float(talla)
        if talla.replace(".", "", 1).isdigit()
        else 999
    )

    producto["tallas_disponibles"] = tallas

    return producto


@tienda.route("/")
def inicio():

    productos = obtener_productos()

    for producto in productos:
        preparar_tallas(producto)

    orden = request.args.get(
        "orden",
        "recientes"
    )

    if orden == "recientes":

        productos.sort(
            key=lambda producto:
            int(producto.get("id", 0)),
            reverse=True
        )

    elif orden == "menor":

        productos.sort(
            key=lambda producto:
            convertir_precio(
                producto.get("precio")
            )
        )

    elif orden == "mayor":

        productos.sort(
            key=lambda producto:
            convertir_precio(
                producto.get("precio")
            ),
            reverse=True
        )

    return render_template(
        "tienda.html",
        productos=productos,
        orden=orden
    )


@tienda.route("/producto/<int:producto_id>")
def ver_producto(producto_id):

    producto = obtener_producto(
        producto_id
    )

    if not producto:
        abort(404)

    preparar_tallas(producto)

    return render_template(
        "producto.html",
        producto=producto
    )