import json
import os
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import urlparse

from config.settings import PRODUCTOS_DATABASE, PRODUCTOS_DIR


def conectar_db():
    Path(PRODUCTOS_DATABASE).parent.mkdir(
        parents=True, exist_ok=True
    )
    conexion = sqlite3.connect(PRODUCTOS_DATABASE)
    conexion.row_factory = sqlite3.Row

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT,
            tallas TEXT,
            stock TEXT,
            precio TEXT,
            descripcion TEXT,
            foto TEXT
        )
    """)

    return conexion


def convertir_json(valor, predeterminado=None):
    if valor is None or valor == "":
        return predeterminado

    if isinstance(valor, (dict, list)):
        return valor

    try:
        return json.loads(valor)
    except (ValueError, TypeError):
        return predeterminado if predeterminado is not None else valor


def preparar_producto(fila):
    if not fila:
        return None

    producto = dict(fila)
    producto["tallas"] = convertir_json(
        producto.get("tallas"), ""
    )
    producto["stock"] = convertir_json(
        producto.get("stock"), {}
    )

    foto = producto.get("foto")

    if foto and not foto.startswith(("http://", "https://", "/media/")):
        foto = "/media/" + foto.lstrip("/")

    producto["foto"] = foto

    return producto


def guardar_valor(valor):
    if isinstance(valor, (dict, list)):
        return json.dumps(valor, ensure_ascii=False)

    return valor


def obtener_productos():
    conexion = conectar_db()

    try:
        filas = conexion.execute(
            "SELECT * FROM productos ORDER BY id"
        ).fetchall()

        return [
            preparar_producto(fila)
            for fila in filas
        ]
    finally:
        conexion.close()


def obtener_producto(producto_id):
    conexion = conectar_db()

    try:
        fila = conexion.execute(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

        return preparar_producto(fila)
    finally:
        conexion.close()


def crear_producto(
    modelo,
    tallas,
    stock,
    precio,
    descripcion,
    foto
):
    conexion = conectar_db()

    try:
        cursor = conexion.execute("""
            INSERT INTO productos
            (modelo, tallas, stock, precio, descripcion, foto)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            modelo,
            guardar_valor(tallas),
            guardar_valor(stock),
            precio,
            descripcion,
            guardar_foto(foto)
        ))

        conexion.commit()

        fila = conexion.execute(
            "SELECT * FROM productos WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        return preparar_producto(fila)
    finally:
        conexion.close()


def actualizar_producto(
    producto_id,
    modelo,
    tallas,
    stock,
    precio,
    descripcion,
    foto
):
    conexion = conectar_db()

    try:
        conexion.execute("""
            UPDATE productos
            SET modelo = ?,
                tallas = ?,
                stock = ?,
                precio = ?,
                descripcion = ?,
                foto = ?
            WHERE id = ?
        """, (
            modelo,
            guardar_valor(tallas),
            guardar_valor(stock),
            precio,
            descripcion,
            guardar_foto(foto),
            producto_id
        ))

        conexion.commit()

        fila = conexion.execute(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

        return preparar_producto(fila)
    finally:
        conexion.close()


def eliminar_producto(producto_id):
    conexion = conectar_db()

    try:
        conexion.execute(
            "DELETE FROM productos WHERE id = ?",
            (producto_id,)
        )
        conexion.commit()
    finally:
        conexion.close()


def actualizar_stock(producto_id, stock):
    conexion = conectar_db()

    try:
        conexion.execute(
            "UPDATE productos SET stock = ? WHERE id = ?",
            (guardar_valor(stock), producto_id)
        )
        conexion.commit()

        fila = conexion.execute(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

        return preparar_producto(fila)
    finally:
        conexion.close()


def guardar_foto(foto):
    if not foto:
        return None

    if foto.startswith(("http://", "https://")):
        return foto

    if foto.startswith("/media/"):
        return foto.removeprefix("/media/")

    return foto.lstrip("/")


def subir_imagen(archivo):
    if not archivo or not archivo.filename:
        return None

    extensiones = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    extension = Path(archivo.filename).suffix.lower()

    if extension not in extensiones:
        extension = ".jpg"

    Path(PRODUCTOS_DIR).mkdir(parents=True, exist_ok=True)

    nombre = f"{uuid.uuid4().hex}{extension}"
    destino = Path(PRODUCTOS_DIR) / nombre

    archivo.save(destino)

    return f"/media/{nombre}"


def eliminar_imagen(url_imagen):
    if not url_imagen:
        return

    if url_imagen.startswith(("http://", "https://")):
        return

    nombre = url_imagen.removeprefix("/media/").lstrip("/")
    nombre = os.path.basename(nombre)

    if not nombre:
        return

    destino = Path(PRODUCTOS_DIR) / nombre

    try:
        if destino.is_file():
            destino.unlink()
    except OSError as error:
        print(f"No se pudo eliminar la imagen: {error}")
