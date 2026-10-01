from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "MarcoSport_clave_2026_847291"

UPLOAD_FOLDER = "static/uploads"
PRODUCTOS_FILE = "productos.json"
DATABASE = "admin.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# BASE DE DATOS
# =========================

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


crear_base_datos()


# =========================
# PRODUCTOS
# =========================

if not os.path.exists(PRODUCTOS_FILE):
    with open(PRODUCTOS_FILE, "w", encoding="utf-8") as archivo:
        json.dump([], archivo)


def cargar_productos():
    with open(PRODUCTOS_FILE, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_productos(productos):
    with open(PRODUCTOS_FILE, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=4)


# =========================
# ADMIN
# =========================

def obtener_admin():
    conexion = conectar_db()

    admin = conexion.execute(
        "SELECT * FROM administrador LIMIT 1"
    ).fetchone()

    conexion.close()

    return admin


# =========================
# TIENDA
# =========================

@app.route("/")
def inicio():

    productos = cargar_productos()

    for producto in productos:
        if "stock" not in producto:
            producto["stock"] = {}

    return render_template(
        "tienda.html",
        productos=productos
    )


# =========================
# CONFIGURAR ADMIN
# =========================

@app.route("/configurar-admin", methods=["GET", "POST"])
def configurar_admin():

    admin = obtener_admin()

    if admin:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar", "")

        if not nombre or not telefono or not usuario or not password:

            error = "Todos los campos son obligatorios."

        elif len(password) < 6:

            error = "La contraseña debe tener mínimo 6 caracteres."

        elif password != confirmar:

            error = "Las contraseñas no coinciden."

        else:

            password_hash = generate_password_hash(password)

            try:

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

                return redirect(url_for("login"))

            except sqlite3.IntegrityError:

                error = "Ese usuario ya existe."

    return render_template(
        "configurar_admin.html",
        error=error
    )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin_id"):
        return redirect(url_for("admin"))

    admin = obtener_admin()

    if not admin:
        return redirect(url_for("configurar_admin"))

    error = None

    if request.method == "POST":

        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")

        conexion = conectar_db()

        admin = conexion.execute("""
            SELECT *
            FROM administrador
            WHERE usuario = ?
        """, (usuario,)).fetchone()

        conexion.close()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session.clear()
            session["admin_id"] = admin["id"]

            return redirect(url_for("admin"))

        error = "Usuario o contraseña incorrectos."

    return render_template(
        "login.html",
        error=error
    )


# =========================
# PANEL ADMIN
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    productos = cargar_productos()
    admin = obtener_admin()

    for producto in productos:

        if "stock" not in producto:
            producto["stock"] = {}

    return render_template(
        "admin.html",
        productos=productos,
        admin=admin
    )


# =========================
# CONFIGURACION
# =========================

@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    admin = obtener_admin()

    mensaje = None
    error = None

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        usuario = request.form.get("usuario", "").strip()

        if not nombre or not telefono or not usuario:

            error = "Todos los campos son obligatorios."

        else:

            try:

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
                    admin["id"]
                ))

                conexion.commit()
                conexion.close()

                mensaje = "Datos actualizados correctamente."

                admin = obtener_admin()

            except sqlite3.IntegrityError:

                error = "Ese usuario ya está siendo utilizado."

    return render_template(
        "configuracion.html",
        admin=admin,
        mensaje=mensaje,
        error=error
    )


# =========================
# CAMBIAR PASSWORD
# =========================

@app.route("/cambiar-password", methods=["POST"])
def cambiar_password():

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    password_actual = request.form.get(
        "password_actual",
        ""
    )

    password_nueva = request.form.get(
        "password_nueva",
        ""
    )

    confirmar = request.form.get(
        "confirmar",
        ""
    )

    admin = obtener_admin()

    error = None

    if not check_password_hash(
        admin["password"],
        password_actual
    ):

        error = "La contraseña actual es incorrecta."

    elif len(password_nueva) < 6:

        error = "La nueva contraseña debe tener mínimo 6 caracteres."

    elif password_nueva != confirmar:

        error = "Las nuevas contraseñas no coinciden."

    else:

        nueva_password = generate_password_hash(
            password_nueva
        )

        conexion = conectar_db()

        conexion.execute("""
            UPDATE administrador
            SET password = ?
            WHERE id = ?
        """, (
            nueva_password,
            admin["id"]
        ))

        conexion.commit()
        conexion.close()

        return redirect(
            url_for("configuracion")
        )

    return render_template(
        "configuracion.html",
        admin=admin,
        error=error
    )


# =========================
# STOCK DEL FORMULARIO
# =========================

def obtener_stock_formulario():

    stock = {}

    for talla in range(33, 46):

        cantidad = request.form.get(
            f"stock_{talla}",
            "0"
        )

        try:
            cantidad = int(cantidad)

        except ValueError:
            cantidad = 0

        if cantidad < 0:
            cantidad = 0

        if cantidad > 0:
            stock[str(talla)] = cantidad

    return stock


# =========================
# AGREGAR PRODUCTO
# =========================

@app.route("/agregar", methods=["POST"])
def agregar():

    if not session.get("admin_id"):
        return redirect(url_for("login"))

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

    foto = request.files.get("foto")

    stock = obtener_stock_formulario()

    if not modelo or not precio or not descripcion:
        return redirect(url_for("admin"))

    if not foto or foto.filename == "":
        return redirect(url_for("admin"))

    nombre_foto = secure_filename(
        foto.filename
    )

    ruta_foto = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nombre_foto
    )

    foto.save(ruta_foto)

    productos = cargar_productos()

    nuevo_producto = {

        "modelo": modelo,

        "tallas": ", ".join(
            stock.keys()
        ),

        "stock": stock,

        "precio": precio,

        "descripcion": descripcion,

        "foto": nombre_foto
    }

    productos.append(
        nuevo_producto
    )

    guardar_productos(productos)

    return redirect(
        url_for("admin")
    )


# =========================
# EDITAR PRODUCTO
# =========================

@app.route(
    "/editar/<int:indice>",
    methods=["GET", "POST"]
)
def editar(indice):

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    productos = cargar_productos()

    if indice < 0 or indice >= len(productos):
        return redirect(url_for("admin"))

    producto = productos[indice]

    if "stock" not in producto:

        producto["stock"] = {}

        tallas_antiguas = producto.get(
            "tallas",
            ""
        )

        for talla in tallas_antiguas.split(","):

            talla = talla.strip()

            if talla:
                producto["stock"][talla] = 1

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

        foto = request.files.get("foto")

        stock = obtener_stock_formulario()

        if not modelo or not precio or not descripcion:

            return render_template(
                "editar.html",
                producto=producto,
                indice=indice,
                error="Todos los campos son obligatorios."
            )

        if foto and foto.filename != "":

            nueva_foto = secure_filename(
                foto.filename
            )

            ruta_nueva = os.path.join(
                app.config["UPLOAD_FOLDER"],
                nueva_foto
            )

            foto.save(ruta_nueva)

            foto_anterior = producto.get(
                "foto"
            )

            if foto_anterior:

                ruta_anterior = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    foto_anterior
                )

                if (
                    os.path.exists(ruta_anterior)
                    and foto_anterior != nueva_foto
                ):
                    os.remove(ruta_anterior)

            producto["foto"] = nueva_foto

        producto["modelo"] = modelo

        producto["tallas"] = ", ".join(
            stock.keys()
        )

        producto["stock"] = stock

        producto["precio"] = precio

        producto["descripcion"] = descripcion

        guardar_productos(productos)

        return redirect(
            url_for("admin")
        )

    return render_template(
        "editar.html",
        producto=producto,
        indice=indice,
        error=None
    )


# =========================
# ELIMINAR PRODUCTO
# =========================

@app.route("/eliminar/<int:indice>")
def eliminar(indice):

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    productos = cargar_productos()

    if 0 <= indice < len(productos):

        producto = productos[indice]

        ruta_foto = os.path.join(
            app.config["UPLOAD_FOLDER"],
            producto["foto"]
        )

        if os.path.exists(ruta_foto):
            os.remove(ruta_foto)

        productos.pop(indice)

        guardar_productos(productos)

    return redirect(
        url_for("admin")
    )


# ==================================================
# PEDIDO DE WHATSAPP
# ==================================================
# IMPORTANTE:
# AQUÍ YA NO SE DESCUENTA EL STOCK.
# SOLO COMPROBAMOS QUE EL PEDIDO SEA POSIBLE.
# ==================================================

@app.route(
    "/procesar-pedido",
    methods=["POST"]
)
def procesar_pedido():

    datos = request.get_json(
        silent=True
    )

    if not isinstance(datos, list) or not datos:

        return jsonify({
            "ok": False,
            "mensaje": "El carrito está vacío."
        }), 400

    productos = cargar_productos()

    # COMPROBAR QUE TODO EXISTA
    for item in datos:

        modelo = str(
            item.get("modelo", "")
        ).strip()

        talla = str(
            item.get("talla", "")
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
                "mensaje": "Hay un producto inválido en el carrito."
            }), 400

        producto_encontrado = None

        for producto in productos:

            if (
                producto.get(
                    "modelo",
                    ""
                ).strip() == modelo
            ):

                producto_encontrado = producto
                break

        if producto_encontrado is None:

            return jsonify({
                "ok": False,
                "mensaje": f"El guayo '{modelo}' ya no está disponible."
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

    # 🚨 AQUÍ NO SE MODIFICA EL STOCK 🚨

    return jsonify({
        "ok": True,
        "mensaje": "Pedido enviado correctamente."
    })


# ==================================================
# MARCAR VENTA MANUALMENTE
# ==================================================

@app.route(
    "/marcar-vendido",
    methods=["POST"]
)
def marcar_vendido():

    if not session.get("admin_id"):
        return redirect(url_for("login"))

    try:

        indice = int(
            request.form.get(
                "indice",
                -1
            )
        )

        talla = str(
            request.form.get(
                "talla",
                ""
            )
        ).strip()

        cantidad = int(
            request.form.get(
                "cantidad",
                0
            )
        )

    except (ValueError, TypeError):

        return redirect(
            url_for("admin")
        )

    if cantidad <= 0:
        return redirect(
            url_for("admin")
        )

    productos = cargar_productos()

    if indice < 0 or indice >= len(productos):

        return redirect(
            url_for("admin")
        )

    producto = productos[indice]

    stock = producto.setdefault(
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

    if disponible < cantidad:

        return redirect(
            url_for("admin")
        )

    # AHORA SÍ DESCONTAMOS
    stock[talla] = disponible - cantidad

    if stock[talla] <= 0:

        del stock[talla]

    producto["tallas"] = ", ".join(
        sorted(
            stock.keys(),
            key=lambda x: int(x)
        )
    )

    guardar_productos(productos)

    return redirect(
        url_for("admin")
    )


# =========================
# CERRAR SESIÓN
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# INICIAR SERVIDOR
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )