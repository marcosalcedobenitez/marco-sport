import os
from pathlib import Path

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "MarcoSport_clave_2026_847291"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DISCO_RENDER = Path("/var/data")

if DISCO_RENDER.is_dir():
    RUTA_DATOS = DISCO_RENDER
else:
    RUTA_DATOS = BASE_DIR

ADMIN_DATABASE = os.environ.get(
    "ADMIN_DATABASE_PATH",
    str(RUTA_DATOS / "admin.db")
)

PRODUCTOS_DATABASE = os.environ.get(
    "PRODUCTOS_DATABASE_PATH",
    str(RUTA_DATOS / "productos.db")
)

PRODUCTOS_DIR = os.environ.get(
    "PRODUCTOS_DIR",
    str(RUTA_DATOS / "productos")
)
