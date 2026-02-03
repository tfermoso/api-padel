import sys
import os

project_path = "/home/tomasfermoso/api-padel"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Si usas variables de entorno, puedes ponerlas aquí
# os.environ["JWT_SECRET_KEY"] = "..."
# os.environ["DATABASE_URL"] = "sqlite:////home/tomasfermoso/api-padel/app.db"

from app import create_app  # app/__init__.py debe tener create_app()
application = create_app()
