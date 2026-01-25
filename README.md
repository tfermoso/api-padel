# API Pádel (Flask) – Documentación para alumnos

Este proyecto es una **API REST** desarrollada con **Flask** para gestionar un sistema de pádel (usuarios, pistas, horarios y reservas).  
La API utiliza **ORM (SQLAlchemy)** para la base de datos y **JWT** para autenticación.

---

## 1) Arquitectura del proyecto

La aplicación está organizada siguiendo un patrón habitual en Flask para proyectos medianos:

- **Paquete `app/`** con `__init__.py`
- **Application Factory**: `create_app()` dentro de `app/__init__.py`
- **Blueprints** para separar rutas por módulos (`auth.py`, `api.py`, `media.py`)
- **Extensiones desacopladas** en `extensions.py` (`db`, `migrate`, `jwt`) y conectadas en `create_app()`

### Estructura de carpetas

```
api-padel/
  app/
    __init__.py
    config.py
    extensions.py
    models.py
    auth.py
    api.py
    media.py
    utils.py (opcional)
  migrations/
  run.py
  .env (NO subir a GitHub)
  requirements.txt
```

---

## 2) ¿Qué pasa cuando ejecutamos `run.py`?

`run.py` es el punto de entrada del proyecto:

```py
from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

### Flujo de ejecución

1. **Python ejecuta `run.py`**
2. `from app import create_app` importa el paquete `app/`  
   - Como `app/` tiene `__init__.py`, se considera un **paquete** en Python.
3. `create_app()` **construye** la aplicación Flask:
   - Carga variables de entorno (`.env`)
   - Aplica configuración (`Config`)
   - Inicializa extensiones (`db`, `migrate`, `jwt`)
   - Registra Blueprints (`/auth`, `/api`, `/media`)
4. `app.run(debug=True)` arranca el servidor en `http://127.0.0.1:5000`

---

## 3) Application Factory (`create_app()`)

La función `create_app()` vive en `app/__init__.py` y se encarga de:

- Crear la instancia Flask: `app = Flask(__name__)`
- Cargar configuración: `app.config.from_object(Config)`
- Inicializar extensiones:  
  - `db.init_app(app)`
  - `migrate.init_app(app, db)`
  - `jwt.init_app(app)`
- Registrar Blueprints:
  - `auth_bp` → `/auth`
  - `api_bp` → `/api`
  - `media_bp` → `/media`

**Ventajas del factory:**
- Permite separar configuración (dev/test/prod)
- Facilita tests (crear app “limpia”)
- Evita imports circulares
- Escala mejor cuando crece el proyecto

---

## 4) Blueprints (separación de rutas)

Los Blueprints agrupan rutas relacionadas:

- `auth.py` → autenticación y endpoints de usuario (register/login/me, etc.)
- `api.py` → endpoints del dominio (pistas, horarios, reservas…)
- `media.py` → servir archivos (por ejemplo, fotos de perfil)

Ejemplo de registro en `create_app()`:

```py
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(media_bp, url_prefix="/media")
```

---

## 5) Extensiones desacopladas (ORM / Migraciones / JWT)

En `app/extensions.py` se definen extensiones sin depender de una app concreta:

```py
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
```

Luego, en `create_app()` se conectan:

```py
db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
```

**¿Dónde se “guarda” esa relación?**  
Flask mantiene un registro interno de extensiones en `app.extensions` (un diccionario interno donde las extensiones guardan su estado asociado a esa app).

---

## 6) Base de datos y migraciones
Migraciones de base de datos (Flask-Migrate / Alembic)

Este proyecto usa migraciones para **versionar** los cambios del modelo (tablas/columnas/índices) y aplicarlos a la base de datos.

### ¿Qué hace cada comando?

- `flask db init`  
  Crea la carpeta `migrations/` y los archivos de Alembic. **Solo se ejecuta la primera vez** en un proyecto.

- `flask db migrate -m "mensaje"`  
  Genera un archivo de migración comparando los modelos (`models.py`) con la base de datos actual.  
  Guarda el script en `migrations/versions/`.

- `flask db upgrade`  
  Aplica las migraciones pendientes a la base de datos (crea/actualiza tablas).

> Idea simple:  
> `db init` = preparar el sistema de migraciones (como `git init`)  
> `db migrate` = generar el “cambio” (como un commit)  
> `db upgrade` = aplicar el cambio a la BD



## Script de ayuda: `migrate_all.py`

Para no ejecutar 3 comandos cada vez, usamos `migrate_all.py`, que automatiza:

1. `db init` (solo si no existe `migrations/`)
2. `db migrate -m "<mensaje>"`
3. `db upgrade`

--

### Uso

**Primera vez (proyecto nuevo):**
```bash
python migrate_all.py "init"
```
---


## 7) Autenticación JWT

- El login devuelve un token:
  - `Authorization: Bearer <token>`
- Las rutas protegidas exigen `@jwt_required()`

Ejemplo:
```http
Authorization: Bearer eyJhbGciOi...
```

---

## 8) Fotos de perfil (upload y acceso)

El proyecto permite subir foto de perfil desde Auth (ejemplo):

- `POST /auth/profile-image` (multipart/form-data)
- Guarda el archivo en el servidor y registra el nombre en BD.

Para **poder verla** desde el navegador/React, se recomienda servirla por URL:

- `GET /media/<filename>`

Así el backend puede devolver al subir:

```json
{
  "image_url": "/media/mi_foto.jpg"
}
```

Y React lo usaría así:
```jsx
<img src={`${BASE_URL}${image_url}`} />
```

---

## 9) Arranque del proyecto

### Crear entorno virtual
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate
```

### Instalar dependencias
```bash
pip install -r requirements.txt
```

### Migraciones
```bash
flask --app run.py db upgrade
```

### Ejecutar
```bash
python run.py
```

---

## 10) Recomendaciones para repositorio

No subir a GitHub:
- `.env`
- `__pycache__/`
- `*.db` (si se puede regenerar)

Crea un `.env.example` con variables necesarias para que cualquiera pueda ejecutar el proyecto.

---

## 11) Checklist (antes de entregar)

- ✅ Migraciones aplicadas (`flask db upgrade`)
- ✅ Login funciona y devuelve token
- ✅ Endpoints protegidos exigen Bearer token
- ✅ Subida de imagen funciona
- ✅ URL pública para imagen funciona (`/media/<filename>`)
