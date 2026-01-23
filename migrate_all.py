import os
import sys
import subprocess
from pathlib import Path

def run(*args):
    subprocess.check_call([sys.executable, "-m", "flask", *args])

def main():
    # Esto indica a Flask CLI cómo crear tu app
    os.environ["FLASK_APP"] = "app:create_app"

    # 1) init solo la primera vez
    if not Path("migrations").exists():
        run("db", "init")

    # 2) generar migración
    msg = "auto"
    if len(sys.argv) > 1:
        msg = sys.argv[1]
    run("db", "migrate", "-m", msg)

    # 3) aplicar migración
    run("db", "upgrade")

    print("OK: migración generada y aplicada.")

if __name__ == "__main__":
    main()
