import os

V2_DB_PATH = os.getenv("V2_DB_PATH", "var/v2.db")

def ensure_var_dir_exists():
    var_dir = os.path.dirname(V2_DB_PATH)
    if var_dir and not os.path.exists(var_dir):
        os.makedirs(var_dir, exist_ok=True)
