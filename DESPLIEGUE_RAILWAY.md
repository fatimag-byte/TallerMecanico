# Despliegue en Railway

Esta guía prepara dos servicios Railway: FastAPI y el sitio estático de Vue. No se debe ejecutar `alembic downgrade` ni recrear la base de datos existente.

## 1. Servicio de base de datos

1. Crea un servicio MySQL administrado en el mismo proyecto Railway.
2. Conserva sus volúmenes administrados: ahí quedan tanto las tablas como las fotografías. Las fotos de vehículos se guardan en `MEDIUMBLOB`; la foto del taller se almacena en MySQL, por lo que no depende del disco efímero del contenedor.
3. No publiques ni confirmes sus credenciales. Railway expone la URL al servicio backend mediante una variable de referencia.

## 2. Servicio backend

1. Crea un servicio desde este repositorio y define `backend` como **Root Directory**.
2. Railway leerá `backend/railway.toml`: instala `requirements.txt`, aplica `alembic upgrade head` y arranca Uvicorn en `$PORT`.
3. Configura estas variables en Railway:

   | Variable | Valor de producción |
   | --- | --- |
   | `APP_ENV` | `production` |
   | `DATABASE_URL` | referencia a `MYSQL_URL` del servicio MySQL; se acepta `mysql://` o `mysql+pymysql://` |
   | `JWT_SECRET` | valor aleatorio de al menos 32 caracteres |
   | `ACCESS_TOKEN_MINUTES` | por ejemplo `15` |
   | `REFRESH_TOKEN_DAYS` | por ejemplo `7` |
   | `CORS_ORIGINS` | URL HTTPS exacta del frontend, sin rutas; separa varios orígenes con comas. No incluyas orígenes locales en producción. |

   `MIGRATION_DATABASE_URL` es opcional. Si se define, Alembic la usa en vez de `DATABASE_URL`; ambas aceptan las formas `mysql://` y `mysql+pymysql://`. En Railway no la definas salvo que vayas a usar una cuenta separada para migraciones.

4. Después de que Railway asigne dominio, confirma `GET /api/health`. Responde `{"status":"ok"}` sólo cuando FastAPI y MySQL pueden atender consultas.

## 3. Servicio frontend

1. Crea un segundo servicio Static desde el mismo repositorio con `frontend` como **Root Directory**.
2. Usa `npm ci && npm run build` como comando de compilación y publica el directorio `dist`.
3. Define en el entorno de compilación `VITE_API_URL=https://<dominio-backend>/api` antes de compilar. Vite incorpora este valor en el artefacto, por lo que cambiarlo exige una nueva compilación.
4. Copia el dominio HTTPS del frontend a `CORS_ORIGINS` del backend y vuelve a desplegar el backend.

## Verificación posterior al despliegue

- Comprueba inicio de sesión, renovación y cierre de sesión.
- Confirma que un usuario sin permiso recibe `403` en roles, clientes, talleres y vehículos.
- Crea una foto de vehículo y recupera la ficha tras reiniciar el servicio backend; la imagen debe seguir disponible porque vive en MySQL.
- Revisa que el navegador sólo use HTTPS y que CORS no permita orígenes locales en producción.

## Desarrollo local

La configuración local continúa usando `backend/.env` y `frontend/.env.local`, que están excluidos de Git. Copia los ejemplos si necesitas configurar una máquina nueva, sin introducir secretos en los archivos versionados.
