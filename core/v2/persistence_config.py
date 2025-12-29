import os

def get_v2_db_path():
    env_path = os.getenv("DEMOBOT_V2_SQLITE_PATH")
    if env_path:
        return env_path
    # אם רץ בטסטים, השתמש ב-/tmp
    if "PYTEST_CURRENT_TEST" in os.environ:
        return "/tmp/demobot_v2_tests.sqlite"
    return "var/demobot_v2.sqlite"

def ensure_var_dir_exists(path: str) -> None:
    var_dir = os.path.dirname(path)
    if var_dir and not os.path.exists(var_dir):
        os.makedirs(var_dir, exist_ok=True)
