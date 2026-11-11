# Fase M01 — Autenticación, usuarios, roles y permisos

**Objetivo:** proporcionar registro, inicio de sesión, renovación de sesión y protección por roles para TallerMecanico.  
**Alcance documentado:** frontend de autenticación, API FastAPI, modelos SQLAlchemy y configuración prevista para MySQL.  
**Dependencias:** Vue 3/Vuetify/Axios; FastAPI/SQLAlchemy/PyMySQL; instancia MySQL local y variables de entorno.  
**Estado actual:** EN PROCESO.  
**Última actualización:** 2026-10-09.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-001 | Rutas SPA de login, registro y recuperación | COMPLETADO | `frontend/src/router.ts`; comprobación HTTP 200 de las tres rutas | La navegación está registrada en Vue Router. |
| M01-002 | Formularios visuales y validaciones cliente | COMPLETADO | Prueba E2E en navegador de registro y login, 2026-10-09 | Campos, navegación, mensaje de conexión y flujo exitoso se verificaron en la SPA; las reglas de cliente se mantienen. |
| M01-003 | Registro con nombre, apellidos, teléfono, correo y contraseña | COMPLETADO | Prueba E2E de `/registro` y consulta MySQL, 2026-10-09 | La cuenta creada desde Vue se persistió activa con apellido materno `NULL` y hash bcrypt. |
| M01-004 | Rechazo de correo duplicado | COMPLETADO | Registro repetido con correo normalizado, HTTP 409, 2026-10-09 | La restricción única de MySQL y el endpoint impidieron el duplicado. |
| M01-005 | Hash bcrypt, JWT y refresh token rotativo | COMPLETADO | Hash almacenado y verificado; `/me`, `/refresh` y reutilización de refresh, 2026-10-09 | Hash bcrypt no contiene la contraseña de prueba; JWT válido autorizado y refresh reutilizado rechazado con 401. |
| M01-006 | Recuperación de contraseña por correo | PENDIENTE | `/api/auth/forgot-password` | El endpoint evita enumeración, pero no genera token ni envía correo. |
| M01-007 | Conexión y migración MySQL local | COMPLETADO | `SELECT 1`, `SHOW GRANTS`, Alembic y verificación de tablas, 2026-10-09 | `taller_migrator` aplicó la revisión y `taller_app` quedó confirmado sin privilegios DDL. |
| M01-008 | Administración de usuarios, roles y permisos desde dashboard | EN PROCESO | `DashboardView.vue`, `services/api.ts` | Identidad y lista administrativa provienen de FastAPI; los controles de escritura simulados se retiraron por no existir endpoints reales. |
| M01-009 | Estados de carga, alertas y snackbar de registro | COMPLETADO | Prueba E2E de registro, 2026-10-09 | El snackbar exacto apareció únicamente después de HTTP 201 y redirigió al dashboard. |
| M01-010 | Migración Alembic inicial de M01 | COMPLETADO | `alembic upgrade head`, `SHOW TABLES`, `alembic_version`, 2026-10-09 | Revisión `20261009_0001` aplicada exclusivamente con la conexión temporal de migraciones a una base vacía. |
| M01-011 | Compatibilidad ORM con Python instalado | COMPLETADO | Importación de `app.models` y compilación `compileall`, 2026-10-09 | SQLAlchemy se actualizó a 2.0.45 y se sustituyeron anotaciones ORM opcionales para compatibilidad con Python 3.14. |
| M01-012 | Autenticación MySQL local de la aplicación | COMPLETADO | `SELECT 1 = 1`, `SELECT DATABASE() = taller_mecanico_db`, 2026-10-09 | La URL configurada usa host IPv4 local y `utf8mb4`; no se expusieron credenciales. |
| M01-013 | Corrección visual de Login y Registro en modo oscuro | COMPLETADO | `AuthShell.vue`, `AuthForm.vue`, `styles/theme.css`; `vue-tsc -b`, `vite build` y revisión visual local el 2026-11-09 | Se retiraron fondos heredados de `v-input` y `v-field__outline`; inputs usan `#30363D`, iconos y cursor mantienen contraste, validaciones siguen visibles sin espacio vacío adicional y el tema conserva el texto al alternarse. |
| M01-014 | Alineación de Registro y aviso de credenciales | COMPLETADO | `AuthForm.vue`, `LoginView.vue`, `RegisterView.vue`, `styles/theme.css`; `vue-tsc -b`, `vite build` y revisión visual claro/oscuro en `/login` y `/registro`, 2026-11-09 | La cuadrícula evita que ayudas o errores estiren campos contiguos; apellido materno conserva su validación opcional. El aviso usa una superficie roja tenue, icono sin fondo adicional y cierre discreto. |
| M01-015 | Validación opcional de apellido materno | COMPLETADO | `AuthForm.vue`, `RegisterView.vue`, `backend/app/schemas.py`; Pydantic valida vacío como `None` y rechaza `123abc`; `vue-tsc -b` y `vite build`, 2026-11-09 | El campo no es obligatorio. Si contiene valor se exige nombre español válido; vacío o espacios se normalizan a `NULL` sin mostrar error. |
| M01-016 | Superficie continua de campos de acceso | COMPLETADO | `styles/theme.css`; revisión visual de Login y Registro en claro/oscuro, `vue-tsc -b`, `vite build`, 2026-11-09 | El autofill de Chromium comparte superficie con el contenedor Vuetify, iconos y ojo; se eliminan huecos claros y se conserva contraste por tema. |
| M01-017 | Inicio de sesión real de administrador | BLOQUEADO | Conteo local: 2 administradores; sin credenciales de prueba autorizadas disponibles, 2026-11-09 | No se adivinaron contraseñas ni se crearon, modificaron o expusieron cuentas. Requiere que el usuario proporcione una credencial autorizada para la prueba E2E. |
| M01-018 | Visibilidad de etiquetas flotantes en Login y Registro | COMPLETADO | `frontend/src/styles/theme.css`; `vue-tsc -b`, `vite build` y revisión visual en `/login` y `/registro`, claro/oscuro, 2026-11-09 | Se eliminó el recorte del contenedor `v-field`; las etiquetas se conservan sobre el borde y la superficie de autofill continúa cubriendo el campo completo. No se alteraron validaciones ni el comportamiento de apellido materno. |
| M01-019 | Cuenta local Administrador solicitada | COMPLETADO | Usuario activo asociado al rol `administrador`; `POST /api/auth/login` validado localmente, 2026-11-09 | La contraseña fue procesada exclusivamente mediante bcrypt y no se registra en archivos de seguimiento. |
| M01-020 | Confirmación de cierre de sesión | COMPLETADO | `frontend/src/App.vue`; inspección visual local y `npm run build`, 2026-11-11 | “Salir” abre un diálogo de confirmación. Cancelar y X conservan la sesión; confirmar reutiliza `logout()` para revocar/limpiar el refresh token y redirigir a login. |
| M01-021 | Composición centrada de confirmación de salida | COMPLETADO | `frontend/src/App.vue`; inspección visual local y `npm run build`, 2026-11-11 | Icono, título, descripción y acciones se centraron; los botones comparten altura y la X se conserva en la esquina superior derecha. No cambió el flujo de sesión. |

## Implementado e identificado

El frontend utiliza Vue 3 con Composition API, TypeScript, Vite, Vuetify 3, Vue Router y Axios. `api.ts` configura el encabezado Bearer y un intento de refresh ante `401`. Las vistas públicas son `LoginView.vue`, `RegisterView.vue` y `ForgotPasswordView.vue`; todas reutilizan `AuthShell.vue` y `AuthForm.vue`.

El backend declara entidades `User`, `Role`, `Permission` y `RefreshToken`, además de las tablas de asociación `user_roles` y `role_permissions`. El primer registro recibe el rol `administrador`; los posteriores, `tecnico`. Las contraseñas se procesan con bcrypt y los refresh tokens se guardan como hash SHA-256.

## Pruebas y evidencia disponible

- Se registró una compilación satisfactoria de `npm run build` el 2026-10-09, repetida durante Fase 1.3 sin errores. La primera ejecución dentro del sandbox falló por permisos de lectura de Vite; la repetición autorizada fuera del sandbox completó correctamente.
- Vite se inició para esta sesión en `http://127.0.0.1:5176`; las rutas `/login`, `/registro` y `/recuperar-contrasena` respondieron HTTP 200. FastAPI se inició en `http://127.0.0.1:8000`; `/openapi.json` respondió HTTP 200 y el login inválido respondió 401. La comprobación CORS autorizó el origen de desarrollo configurado.
- Se registró compilación sintáctica de `backend/app` con `python -m compileall` el 2026-10-09. También se cargaron FastAPI y los modelos ORM, se validaron solicitudes de registro con y sin apellido materno y se comprobó localmente hash/verificación bcrypt correcta y rechazo de una contraseña distinta. Esta prueba no persiste ni emite JWT porque MySQL sigue bloqueado.
- Se comprobó respuesta HTTP 200 del servidor Vite para `/login`, `/registro` y `/recuperar-contrasena` el 2026-10-09.
- Se creó `backend/.venv` e instalaron las dependencias declaradas para esta verificación. La consulta `SELECT 1` mediante SQLAlchemy alcanzó MySQL local, pero la autenticación fue rechazada con error 1045. Se comprobó sin exponer secretos que usuario, host y base de la URL son los esperados, mientras la contraseña difiere de la credencial confirmada. No hay evidencia de creación de tablas, registro persistido, login real ni correo de recuperación.
- Se retiró `Base.metadata.create_all` del evento de inicio de FastAPI. Alembic 1.14.1 y la revisión inicial no destructiva de M01 se prepararon, revisaron como SQL estático y aplicaron con `taller_migrator`; Uvicorn inició correctamente con `taller_app` y sembró los roles iniciales.
- La cuenta migradora ejecutó `SELECT 1`, confirmó una base vacía y contó con `SELECT`, `INSERT`, `CREATE`, `INDEX` y `REFERENCES`. Después de Alembic se verificaron `alembic_version`, `users`, `roles`, `permissions`, `user_roles`, `role_permissions` y `refresh_tokens`; la versión almacenada es `20261009_0001`.
- Las pruebas de integración reales registraron un administrador con apellido materno y un técnico sin él, verificaron `NULL` persistido, correo duplicado (409), hash bcrypt, login válido e inválido (200/401), JWT en `/me`, autorización (200/401/403) y refresh rotativo (200/401 al reutilizarlo).
- Prueba E2E de navegador: se creó una cuenta técnica desde `http://127.0.0.1:5177/registro` con apellido materno vacío; apareció exactamente `La cuenta ha sido creada correctamente.`, se navegó al dashboard, se cerró sesión y se inició sesión otra vez con la misma cuenta. MySQL confirmó que el último registro está activo, que el apellido materno es `NULL` y que el hash bcrypt está almacenado.
- Se corrigió la conexión local de la SPA: Axios usa `127.0.0.1` como valor por defecto y `frontend/.env.local` (ignorado por Git) apuntó la instancia de prueba a FastAPI en el puerto 8001. CORS autoriza el origen Vite activo. El build final `npm run build` terminó correctamente.

## Errores, bloqueos y decisiones

- **Hecho:** MySQL local está accesible en `127.0.0.1:3306` y SQLAlchemy alcanzó el servidor el 2026-10-09.
- **Resuelto:** la autenticación de la cuenta configurada se corrigió y MySQL local aceptó la conexión el 2026-10-09.
- **Decisión de privilegios:** `taller_migrator` se usó solamente para Alembic mediante `backend/.env.migration`, ignorado por Git. `taller_app` se verificó sin privilegios DDL y atendió las pruebas de negocio.
- **Advertencia no bloqueante:** Passlib 1.7.4 emitió una advertencia de metadatos al cargar bcrypt 4.3.0. Las pruebas reales de hash y verificación bcrypt finalizaron correctamente; revisar una actualización futura de la librería sin modificar este flujo ya validado.
- **Riesgo técnico:** `DashboardView.vue` importa `demoAuth.ts`, mientras que la autenticación principal usa Axios/FastAPI. Esta diferencia debe evaluarse antes de considerar administración de roles como integrada.
- **Decisión:** la migración `001_add_user_personal_data.sql` deja los nuevos datos personales como `NULL` para no invalidar usuarios históricos; el esquema de nuevos registros exige nombre, apellido paterno y teléfono, mientras apellido materno es opcional.

## Archivos involucrados

`frontend/src/components/AuthShell.vue`, `AuthForm.vue`; `frontend/src/views/LoginView.vue`, `RegisterView.vue`, `ForgotPasswordView.vue`; `frontend/src/services/api.ts`; `frontend/src/stores/auth.ts`; `backend/app/models.py`, `schemas.py`, `security.py`, `dependencies.py`, `main.py`, `database.py`; `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/20261009_0001_create_m01_identity_schema.py`; `backend/migrations/001_add_user_personal_data.sql`.

## Próxima actividad autorizable

Crear endpoints reales para la gestión administrativa avanzada del dashboard o diseñar la recuperación de contraseña real con token de un solo uso y proveedor de correo, en fases autorizadas.
