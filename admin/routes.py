from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import sqlite3

from services.productos import (
    obtener_productos,
    obtener_producto,
    crear_producto,
    actualizar_producto,
    eliminar_producto,
    actualizar_stock,
    subir_imagen,
    eliminar_imagen
)


DATABASE = "admin.db"


admin = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    static_folder="static"
)


def conectar_db():

    conexion = sqlite3.connect(DATABASE)

    conexion.row_factory = sqlite3.Row

    return conexion


def crear_base_datos():

    conexion = conectar_db()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS administrador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conexion.commit()

    conexion.close()


def obtener_admin():

    conexion = conectar_db()

    administrador = conexion.execute(
        "SELECT * FROM administrador LIMIT 1"
    ).fetchone()

    conexion.close()

    return administrador


crear_base_datos()


def admin_logueado():

    return session.get("admin_id") is not None


def obtener_stock_formulario():

    stock = {}

    for talla in range(33, 46):

        cantidad = request.form.get(
            f"stock_{talla}",
            "0"
        )

        try:
            cantidad = int(cantidad)

        except (ValueError, TypeError):
            cantidad = 0

        if cantidad < 0:
            cantidad = 0

        stock[str(talla)] = cantidad

    return stock


@admin.route(
    "/configurar-admin",
    methods=["GET", "POST"]
)
def configurar_admin():

    if obtener_admin():

        return redirect(
            url_for("admin.login")
        )

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirmar = request.form.get(
            "confirmar",
            ""
        )

        if (
            not nombre
            or not telefono
            or not usuario
            or not password
            or not confirmar
        ):

            return render_template(
                "configurar_admin.html",
                error="Todos los campos son obligatorios."
            )

        if len(password) < 6:

            return render_template(
                "configurar_admin.html",
                error="La contraseña debe tener al menos 6 caracteres."
            )

        if password != confirmar:

            return render_template(
                "configurar_admin.html",
                error="Las contraseñas no coinciden."
            )

        password_hash = generate_password_hash(
            password
        )

        conexion = conectar_db()

        conexion.execute("""
            INSERT INTO administrador
            (nombre, telefono, usuario, password)
            VALUES (?, ?, ?, ?)
        """, (
            nombre,
            telefono,
            usuario,
            password_hash
        ))

        conexion.commit()

        conexion.close()

        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "configurar_admin.html"
    )


@admin.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if not obtener_admin():

        return redirect(
            url_for("admin.configurar_admin")
        )

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        administrador = obtener_admin()

        if (
            administrador
            and administrador["usuario"] == usuario
            and check_password_hash(
                administrador["password"],
                password
            )
        ):

            session["admin_id"] = administrador["id"]

            return redirect(
                url_for("admin.panel")
            )

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos."
        )

    return render_template(
        "login.html"
    )


@admin.route("/admin")
def panel():

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    productos = obtener_productos()

    return render_template(
        "admin.html",
        productos=productos
    )
@admin.route(
    "/agregar",
    methods=["POST"]
)
def agregar():

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    modelo = request.form.get(
        "modelo",
        ""
    ).strip()

    precio = request.form.get(
        "precio",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    stock = obtener_stock_formulario()

    archivo = request.files.get(
        "foto"
    )

    foto = None

    if archivo and archivo.filename:

        foto = subir_imagen(
            archivo
        )

    crear_producto(
        modelo=modelo,
        tallas="",
        stock=stock,
        precio=precio,
        descripcion=descripcion,
        foto=foto
    )

    return redirect(
        url_for("admin.panel")
    )


@admin.route(
    "/editar/<int:producto_id>",
    methods=["GET", "POST"]
)
def editar(producto_id):

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    producto = obtener_producto(
        producto_id
    )

    if not producto:

        return redirect(
            url_for("admin.panel")
        )

    if request.method == "POST":

        modelo = request.form.get(
            "modelo",
            ""
        ).strip()

        precio = request.form.get(
            "precio",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        stock = obtener_stock_formulario()

        foto = producto.get(
            "foto"
        )

        archivo = request.files.get(
            "foto"
        )

        if archivo and archivo.filename:

            nueva_foto = subir_imagen(
                archivo
            )

            if nueva_foto:

                eliminar_imagen(
                    foto
                )

                foto = nueva_foto

        actualizar_producto(
            producto_id=producto_id,
            modelo=modelo,
            tallas="",
            stock=stock,
            precio=precio,
            descripcion=descripcion,
            foto=foto
        )

        return redirect(
            url_for("admin.panel")
        )

    return render_template(
        "editar.html",
        producto=producto
    )


@admin.route(
    "/eliminar/<int:producto_id>"
)
def eliminar(producto_id):

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    producto = obtener_producto(
        producto_id
    )

    if not producto:

        return redirect(
            url_for("admin.panel")
        )

    foto = producto.get(
        "foto"
    )

    eliminar_producto(
        producto_id
    )

    eliminar_imagen(
        foto
    )

    return redirect(
        url_for("admin.panel")
    )


@admin.route(
    "/marcar-vendido",
    methods=["POST"]
)
def marcar_vendido():

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    producto_id = request.form.get(
        "producto_id"
    )

    talla = request.form.get(
        "talla"
    )

    cantidad = request.form.get(
        "cantidad",
        "1"
    )

    try:

        producto_id = int(
            producto_id
        )

        cantidad = int(
            cantidad
        )

    except (ValueError, TypeError):

        return redirect(
            url_for("admin.panel")
        )

    if cantidad <= 0:

        return redirect(
            url_for("admin.panel")
        )

    producto = obtener_producto(
        producto_id
    )

    if not producto:

        return redirect(
            url_for("admin.panel")
        )

    stock = producto.get(
        "stock"
    ) or {}

    try:

        stock_actual = int(
            stock.get(
                str(talla),
                0
            )
        )

    except (ValueError, TypeError):

        stock_actual = 0

    if cantidad > stock_actual:

        return redirect(
            url_for("admin.panel")
        )

    stock[str(talla)] = (
        stock_actual - cantidad
    )

    actualizar_stock(
        producto_id,
        stock
    )

    return redirect(
        url_for("admin.panel")
    )


@admin.route(
    "/procesar-pedido",
    methods=["POST"]
)
def procesar_pedido():

    datos = request.get_json(
        silent=True
    )

    if not isinstance(
        datos,
        list
    ) or not datos:

        return jsonify({
            "ok": False,
            "mensaje": "El carrito está vacío."
        }), 400

    productos = obtener_productos()

    for item in datos:

        modelo = str(
            item.get(
                "modelo",
                ""
            )
        ).strip()

        talla = str(
            item.get(
                "talla",
                ""
            )
        ).strip()

        try:

            cantidad = int(
                item.get(
                    "cantidad",
                    0
                )
            )

        except (ValueError, TypeError):

            cantidad = 0

        if (
            not modelo
            or not talla
            or cantidad <= 0
        ):

            return jsonify({
                "ok": False,
                "mensaje": (
                    "Hay un producto inválido "
                    "en el carrito."
                )
            }), 400

        producto_encontrado = None

        for producto in productos:

            modelo_producto = str(
                producto.get(
                    "modelo",
                    ""
                )
            ).strip()

            stock_producto = producto.get(
                "stock",
                {}
            )

            if not isinstance(
                stock_producto,
                dict
            ):

                stock_producto = {}

            if (
                modelo_producto == modelo
                and talla in stock_producto
            ):

                producto_encontrado = producto

                break

        if producto_encontrado is None:

            return jsonify({
                "ok": False,
                "mensaje": (
                    f"El producto '{modelo}' "
                    f"con talla {talla} "
                    "ya no está disponible."
                )
            }), 409

        stock = producto_encontrado.get(
            "stock",
            {}
        )

        try:

            disponible = int(
                stock.get(
                    talla,
                    0
                )
            )

        except (ValueError, TypeError):

            disponible = 0

        if cantidad > disponible:

            return jsonify({
                "ok": False,
                "mensaje": (
                    f"Solo quedan {disponible} "
                    f"par(es) de la talla {talla} "
                    f"del modelo {modelo}."
                )
            }), 409

    return jsonify({
        "ok": True,
        "mensaje": "Pedido enviado correctamente."
    })


@admin.route(
    "/configuracion",
    methods=["GET", "POST"]
)
def configuracion():

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    administrador = obtener_admin()

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        if (
            not nombre
            or not telefono
            or not usuario
        ):

            return render_template(
                "configuracion.html",
                admin=administrador,
                error="Todos los campos son obligatorios."
            )

        conexion = conectar_db()

        conexion.execute("""
            UPDATE administrador
            SET nombre = ?,
                telefono = ?,
                usuario = ?
            WHERE id = ?
        """, (
            nombre,
            telefono,
            usuario,
            administrador["id"]
        ))

        conexion.commit()

        conexion.close()

        return redirect(
            url_for("admin.configuracion")
        )

    return render_template(
        "configuracion.html",
        admin=administrador
    )


@admin.route(
    "/cambiar-password",
    methods=["POST"]
)
def cambiar_password():

    if not admin_logueado():

        return redirect(
            url_for("admin.login")
        )

    nueva_password = request.form.get(
        "password",
        ""
    )

    if not nueva_password:

        return redirect(
            url_for("admin.configuracion")
        )

    if len(nueva_password) < 6:

        return redirect(
            url_for("admin.configuracion")
        )

    password_hash = generate_password_hash(
        nueva_password
    )

    administrador = obtener_admin()

    conexion = conectar_db()

    conexion.execute("""
        UPDATE administrador
        SET password = ?
        WHERE id = ?
    """, (
        password_hash,
        administrador["id"]
    ))

    conexion.commit()

    conexion.close()

    return redirect(
        url_for("admin.configuracion")
    )


@admin.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("admin.login")
    )