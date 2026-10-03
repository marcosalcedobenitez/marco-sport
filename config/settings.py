import os


# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "MarcoSport_clave_2026_847291"
)


# ==========================================
# BASE DE DATOS DEL ADMINISTRADOR
# ==========================================

DATABASE = "admin.db"


# ==========================================
# SUPABASE
# ==========================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

STORAGE_BUCKET = "productos"


if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltan las variables SUPABASE_URL y SUPABASE_KEY."
    )