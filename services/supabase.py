from supabase import create_client

from config.settings import (
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# CONEXIÓN CON SUPABASE
# ==========================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)