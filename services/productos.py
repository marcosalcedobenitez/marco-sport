import uuid

from services.supabase import supabase
from config.settings import STORAGE_BUCKET


# ==========================================
# OBTENER TODOS LOS PRODUCTOS
# ==========================================

def obtener_productos():

    respuesta = (
        supabase
        .table("productos")
        .select("*")
        .order("id")
        .execute()
    )

    return respuesta.data or []


# ==========================================
# OBTENER UN PRODUCTO
# ==========================================

def obtener_producto(producto_id):

    respuesta = (
        supabase
        .table("productos")
        .select("*")
        .eq("id", producto_id)
        .execute()
    )

    if not respuesta.data:
        return None

    return respuesta.data[0]


# ==========================================
# CREAR PRODUCTO
# ==========================================

def crear_producto(
    modelo,
    tallas,
    stock,
    precio,
    descripcion,
    foto
):

    producto = {
        "modelo": modelo,
        "tallas": tallas,
        "stock": stock,
        "precio": precio,
        "descripcion": descripcion,
        "foto": foto
    }

    respuesta = (
        supabase
        .table("productos")
        .insert(producto)
        .execute()
    )

    if not respuesta.data:
        return None

    return respuesta.data[0]


# ==========================================
# ACTUALIZAR PRODUCTO
# ==========================================

def actualizar_producto(
    producto_id,
    modelo,
    tallas,
    stock,
    precio,
    descripcion,
    foto
):

    producto = {
        "modelo": modelo,
        "tallas": tallas,
        "stock": stock,
        "precio": precio,
        "descripcion": descripcion,
        "foto": foto
    }

    respuesta = (
        supabase
        .table("productos")
        .update(producto)
        .eq("id", producto_id)
        .execute()
    )

    if not respuesta.data:
        return None

    return respuesta.data[0]


# ==========================================
# ELIMINAR PRODUCTO
# ==========================================

def eliminar_producto(producto_id):

    (
        supabase
        .table("productos")
        .delete()
        .eq("id", producto_id)
        .execute()
    )


# ==========================================
# ACTUALIZAR STOCK
# ==========================================

def actualizar_stock(producto_id, stock):

    respuesta = (
        supabase
        .table("productos")
        .update({
            "stock": stock
        })
        .eq("id", producto_id)
        .execute()
    )

    if not respuesta.data:
        return None

    return respuesta.data[0]


# ==========================================
# SUBIR IMAGEN
# ==========================================

def subir_imagen(archivo):

    if not archivo or not archivo.filename:
        return None

    extension = ""

    if "." in archivo.filename:

        extension = (
            "."
            + archivo.filename.rsplit(
                ".",
                1
            )[1].lower()
        )

    nombre_archivo = (
        f"{uuid.uuid4().hex}{extension}"
    )

    contenido = archivo.read()

    supabase.storage.from_(
        STORAGE_BUCKET
    ).upload(
        nombre_archivo,
        contenido,
        {
            "content-type": archivo.content_type
        }
    )

    url_publica = (
        supabase
        .storage
        .from_(STORAGE_BUCKET)
        .get_public_url(
            nombre_archivo
        )
    )

    return url_publica


# ==========================================
# ELIMINAR IMAGEN
# ==========================================

def eliminar_imagen(url_imagen):

    if not url_imagen:
        return

    try:

        parte = (
            f"/storage/v1/object/public/"
            f"{STORAGE_BUCKET}/"
        )

        if parte not in url_imagen:
            return

        nombre_archivo = (
            url_imagen.split(
                parte,
                1
            )[1]
        )

        supabase.storage.from_(
            STORAGE_BUCKET
        ).remove([
            nombre_archivo
        ])

    except Exception as error:

        print(
            f"No se pudo eliminar la imagen: {error}"
        )