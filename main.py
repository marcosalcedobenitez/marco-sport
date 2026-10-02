from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sqlite3
import uuid

from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client


app = Flask(__name__)

# ==================================================
# CONFIGURACIÓN
# ==================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "MarcoSport_clave_2026_847291"
)

PRODUCTOS_FILE = "productos.json"
DATABASE = "admin.db"

STORAGE_BUCKET = "productos"

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==================================================
# SUPABASE
# ==================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltan las variables SUPABASE_URL y SUPABASE_KEY."
    )

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==================================================
# FUNCIONES PARA IMÁGENES
# ==================================================

def subir_imagen_supabase(archivo):

    if not archivo or archivo.filename == "":
        return None

    extension = os.path.splitext(
        archivo.filename
    )[1].lower()

    if not extension:
        extension = ".jpg"

    nombre_unico = (
        uuid.uuid4().hex + extension
    )

    ruta_storage = nombre_unico

    contenido = archivo.read()

    if not contenido:
        return None

    tipo_mime = (
        archivo.mimetype
        or "application/octet-stream"
    )

    respuesta = supabase.storage.from_(
        STORAGE_BUCKET
    ).upload(
        ruta_storage,
        contenido,
        {
            "content-type": tipo_mime,
            "cache-control": "3600",
            "upsert": "false"
        }
    )

    print(
        "Imagen subida a Supabase Storage:",
        ruta_storage
    )

    print(
        "Respuesta de Supabase:",
        respuesta
    )

    url_publica = supabase.storage.from_(
        STORAGE_BUCKET
    ).get_public_url(
        ruta_storage
    )

    print(
        "URL pública de la imagen:",
        url_publica
    )

    return url_publica


def eliminar_imagen_supabase(url_imagen):

    if not url_imagen:
        return

    if not isinstance(url_imagen, str):
        return

    parte = (
        "storage/v1/object/public/"
        + STORAGE_BUCKET
        + "/"
    )

    if parte not in url_imagen:
        return

    try:

        ruta = url_imagen.split(
            parte,
            1
        )[1]

        if ruta:

            supabase.storage.from_(
                STORAGE_BUCKET
            ).remove([
                ruta
            ])

            print(
                "Imagen eliminada de Supabase:",
                ruta
            )

    except Exception as error:

        print(
            "No se pudo eliminar la imagen:",
            error
        )


# ==================================================
# BASE DE DATOS DEL ADMIN
# ==================================================

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


# ==================================================
# PRODUCTOS
# ==================================================

def importar_productos_json():

    try:

        respuesta = supabase.table(
            "productos"
        ).select("*").execute()

        productos_supabase = respuesta.data or []

        if productos_supabase:
            return

        if not os.path.exists(PRODUCTOS_FILE):
            return

        with open(
            PRODUCTOS_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            productos = json.load(archivo)

        if not productos:
            return

        datos = []

        for producto in productos:

            datos.append({
                "modelo": producto.get(
                    "modelo",
                    ""
                ),

                "tallas": producto.get(
                    "tallas",
                    ""
                ),

                "stock": producto.get(
                    "stock",
                    {}
                ),

                "precio": producto.get(
                    "precio",
                    ""
                ),

                "descripcion": producto.get(
                    "descripcion",
                    ""
                ),

                "foto": producto.get(
                    "foto",
                    ""
                )
            })

        supabase.table(
            "productos"
        ).insert(datos).execute()

        print(
            "Productos antiguos importados a Supabase."
        )

    except Exception as error:

        print(
            "Error importando productos:",
            error
        )


def cargar_productos():

    importar_productos_json()

    respuesta = supabase.table(
        "productos"
    ).select("*").order(
        "id"
    ).execute()

    return respuesta.data or []


def guardar_productos(productos):

    try:

        supabase.table(
            "productos"
        ).delete().neq(
            "id",
            0
        ).execute()

        if not productos:
            return

        datos = []

        for producto in productos:

            datos.append({
                "modelo": producto.get(
                    "modelo",
                    ""
                ),

                "tallas": producto.get(
                    "tallas",
                    ""
                ),

                "stock": producto.get(
                    "stock",
                    {}
                ),

                "precio": producto.get(
                    "precio",
                    ""
                ),

                "descripcion": producto.get(
                    "descripcion",
                    ""
                ),

                "foto": producto.get(
                    "foto",
                    ""
                )
            })

        supabase.table(
            "productos"
        ).insert(datos).execute()

    except Exception as error:

        print(
            "Error guardando productos:",
            error
        )


# ==================================================
# ADMIN
# ==================================================

def obtener_admin():

    conexion = conectar_db()

    admin = conexion.execute(
        "SELECT * FROM administrador LIMIT 1"
    ).fetchone()

    conexion.close()

    return admin


# ==================================================
# TIENDA
# ==================================================

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


# ==================================================
# CONFIGURAR ADMIN
# ==================================================

@app.route(
    "/configurar-admin",
    methods=["GET", "POST"]
)
def configurar_admin():

    admin = obtener_admin()

    if admin:

        return redirect(
            url_for("login")
        )

    error = None

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

        if not nombre or not telefono or not usuario or not password:

            error = (
                "Todos los campos son obligatorios."
            )

        elif len(password) < 6:

            error = (
                "La contraseña debe tener mínimo 6 caracteres."
            )

        elif password != confirmar:

            error = (
                "Las contraseñas no coinciden."
            )

        else:

            password_hash = generate_password_hash(
                password
            )

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

                return redirect(
                    url_for("login")
                )

            except sqlite3.IntegrityError:

                error = (
                    "Ese usuario ya existe."
                )

    return render_template(
        "configurar_admin.html",
        error=error
    )


# ==================================================
# LOGIN
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if session.get("admin_id"):

        return redirect(
            url_for("admin")
        )

    admin = obtener_admin()

    if not admin:

        return redirect(
            url_for("configurar_admin")
        )

    error = None

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conexion = conectar_db()

        admin = conexion.execute("""
            SELECT *
            FROM administrador
            WHERE usuario = ?
        """, (
            usuario,
        )).fetchone()

        conexion.close()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session.clear()

            session["admin_id"] = admin["id"]

            return redirect(
                url_for("admin")
            )

        error = (
            "Usuario o contraseña incorrectos."
        )

    return render_template(
        "login.html",
        error=error
    )


# ==================================================
# PANEL ADMIN
# ==================================================

@app.route("/admin")
def admin():

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
        )

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


# ==================================================
# CONFIGURACIÓN
# ==================================================

@app.route(
    "/configuracion",
    methods=["GET", "POST"]
)
def configuracion():

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
        )

    admin = obtener_admin()

    mensaje = None
    error = None

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

        if not nombre or not telefono or not usuario:

            error = (
                "Todos los campos son obligatorios."
            )

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

                mensaje = (
                    "Datos actualizados correctamente."
                )

                admin = obtener_admin()

            except sqlite3.IntegrityError:

                error = (
                    "Ese usuario ya está siendo utilizado."
                )

    return render_template(
        "configuracion.html",
        admin=admin,
        mensaje=mensaje,
        error=error
    )


# ==================================================
# CAMBIAR PASSWORD
# ==================================================

@app.route(
    "/cambiar-password",
    methods=["POST"]
)
def cambiar_password():

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
        )

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

        error = (
            "La contraseña actual es incorrecta."
        )

    elif len(password_nueva) < 6:

        error = (
            "La nueva contraseña debe tener mínimo 6 caracteres."
        )

    elif password_nueva != confirmar:

        error = (
            "Las nuevas contraseñas no coinciden."
        )

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


# ==================================================
# STOCK DEL FORMULARIO
# ==================================================

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


# ==================================================
# AGREGAR PRODUCTO
# ==================================================

@app.route(
    "/agregar",
    methods=["POST"]
)
def agregar():

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
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

    foto = request.files.get(
        "foto"
    )

    stock = obtener_stock_formulario()

    if not modelo or not precio or not descripcion:

        return redirect(
            url_for("admin")
        )

    if not foto or foto.filename == "":

        return redirect(
            url_for("admin")
        )

    try:

        url_foto = subir_imagen_supabase(
            foto
        )

    except Exception as error:

        print(
            "ERROR SUBIENDO IMAGEN A SUPABASE:",
            error
        )

        return redirect(
            url_for("admin")
        )

    if not url_foto:

        print(
            "La imagen no devolvió una URL pública."
        )

        return redirect(
            url_for("admin")
        )

    productos = cargar_productos()

    nuevo_producto = {

        "modelo": modelo,

        "tallas": ", ".join(
            sorted(
                stock.keys(),
                key=lambda x: int(x)
            )
        ),

        "stock": stock,

        "precio": precio,

        "descripcion": descripcion,

        "foto": url_foto
    }

    productos.append(
        nuevo_producto
    )

    guardar_productos(
        productos
    )

    return redirect(
        url_for("admin")
    )


# ==================================================
# EDITAR PRODUCTO
# ==================================================

@app.route(
    "/editar/<int:indice>",
    methods=["GET", "POST"]
)
def editar(indice):

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
        )

    productos = cargar_productos()

    if indice < 0 or indice >= len(productos):

        return redirect(
            url_for("admin")
        )

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

        foto = request.files.get(
            "foto"
        )

        stock = obtener_stock_formulario()

        if not modelo or not precio or not descripcion:

            return render_template(
                "editar.html",
                producto=producto,
                indice=indice,
                error=(
                    "Todos los campos son obligatorios."
                )
            )

        if foto and foto.filename != "":

            foto_anterior = producto.get(
                "foto"
            )

            try:

                nueva_foto = subir_imagen_supabase(
                    foto
                )

                if not nueva_foto:

                    return render_template(
                        "editar.html",
                        producto=producto,
                        indice=indice,
                        error=(
                            "No se pudo subir la nueva imagen."
                        )
                    )

                producto["foto"] = nueva_foto

                if foto_anterior:

                    eliminar_imagen_supabase(
                        foto_anterior
                    )

            except Exception as error:

                print(
                    "ERROR CAMBIANDO IMAGEN:",
                    error
                )

                return render_template(
                    "editar.html",
                    producto=producto,
                    indice=indice,
                    error=(
                        "No se pudo subir la nueva imagen."
                    )
                )

        producto["modelo"] = modelo

        producto["tallas"] = ", ".join(
            sorted(
                stock.keys(),
                key=lambda x: int(x)
            )
        )

        producto["stock"] = stock

        producto["precio"] = precio

        producto["descripcion"] = descripcion

        guardar_productos(
            productos
        )

        return redirect(
            url_for("admin")
        )

    return render_template(
        "editar.html",
        producto=producto,
        indice=indice,
        error=None
    )


# ==================================================
# ELIMINAR PRODUCTO
# ==================================================

@app.route(
    "/eliminar/<int:indice>"
)
def eliminar(indice):

    if not session.get("admin_id"):

        return redirect(
            url_for("login")
        )

    productos = cargar_productos()

    if 0 <= indice < len(productos):

        producto = productos[indice]

        foto = producto.get(
            "foto",
            ""
        )

        eliminar_imagen_supabase(
            foto
        )

        productos.pop(indice)

        guardar_productos(
            productos
        )

    return redirect(
        url_for("admin")
    )


# ==================================================
# PEDIDO DE WHATSAPP
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

        except (
            ValueError,
            TypeError
        ):

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

        # ==========================================
        # BUSCAR POR MODELO + TALLA
        # ==========================================

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

        except (
            ValueError,
            TypeError
        ):

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

    # IMPORTANTE:
    # EL PEDIDO DE WHATSAPP NO DESCUENTA STOCK.

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

        return redirect(
            url_for("login")
        )

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

    except (
        ValueError,
        TypeError
    ):

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

    except (
        ValueError,
        TypeError
    ):

        disponible = 0

    if disponible < cantidad:

        return redirect(
            url_for("admin")
        )

    stock[talla] = (
        disponible - cantidad
    )

    if stock[talla] <= 0:

        del stock[talla]

    producto["tallas"] = ", ".join(
        sorted(
            stock.keys(),
            key=lambda x: int(x)
        )
    )

    guardar_productos(
        productos
    )

    return redirect(
        url_for("admin")
    )


# ==================================================
# CERRAR SESIÓN
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# INICIAR SERVIDOR
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )