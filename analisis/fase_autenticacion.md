# Fase M01 — Autenticación, usuarios, roles y permisos

**Objetivo:** proporcionar registro, inicio de sesión, renovación de sesión y protección por roles para TallerMecanico.  
**Alcance documentado:** frontend de autenticación, API FastAPI, modelos SQLAlchemy y configuración prevista para MySQL.  
**Dependencias:** Vue 3/Vuetify/Axios; FastAPI/SQLAlchemy/PyMySQL; instancia MySQL local y variables de entorno.  
**Estado actual:** EN PROCESO.  
**Última actualización:** 2026-10-09.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-001 | Rutas SPA de login, registro y recuperación | COMPLETADO | `frontend/src/router.ts`; comprobación HTTP 200 de las tres rutas | La navegación está registrada en Vue Router. |
| M01-002 | Formularios visuales y validaciones cliente | NO VERIFICADO | `AuthForm.vue`, vistas de autenticación | Compilación Vite realizada; falta prueba manual de cada mensaje y adaptación visual. |
| M01-003 | Registro con nombre, apellidos, teléfono, correo y contraseña | NO VERIFICADO | `RegisterRequest`, `User`, endpoint `/api/auth/register` | Código presente; no existe prueba contra FastAPI/MySQL. |
| M01-004 | Rechazo de correo duplicado | NO VERIFICADO | Índice único `users.email` y manejo `IntegrityError` | Falta prueba concurrente e integración real. |
| M01-005 | Hash bcrypt, JWT y refresh token rotativo | NO VERIFICADO | `security.py`, `main.py`, `api.ts` | Implementado en código; sin prueba de sesión real. |
| M01-006 | Recuperación de contraseña por correo | PENDIENTE | `/api/auth/forgot-password` | El endpoint evita enumeración, pero no genera token ni envía correo. |
| M01-007 | Conexión y migración MySQL local | BLOQUEADO | `database.py`, `.env.example`, `migrations/001_add_user_personal_data.sql` | No se documentan credenciales ni una ejecución de migración verificada. |
| M01-008 | Administración de usuarios, roles y permisos desde dashboard | EN PROCESO | `DashboardView.vue`, `services/demoAuth.ts` | La vista usa almacenamiento local de demostración; no está integrada con la API de administración. |
| M01-009 | Estados de carga, alertas y snackbar de registro | NO VERIFICADO | `LoginView.vue`, `RegisterView.vue`, `ForgotPasswordView.vue` | Existe código visual; falta prueba ante respuestas reales. |

## Implementado e identificado

El frontend utiliza Vue 3 con Composition API, TypeScript, Vite, Vuetify 3, Vue Router y Axios. `api.ts` configura el encabezado Bearer y un intento de refresh ante `401`. Las vistas públicas son `LoginView.vue`, `RegisterView.vue` y `ForgotPasswordView.vue`; todas reutilizan `AuthShell.vue` y `AuthForm.vue`.

El backend declara entidades `User`, `Role`, `Permission` y `RefreshToken`, además de las tablas de asociación `user_roles` y `role_permissions`. El primer registro recibe el rol `administrador`; los posteriores, `tecnico`. Las contraseñas se procesan con bcrypt y los refresh tokens se guardan como hash SHA-256.

## Pruebas y evidencia disponible

- Se registró una compilación satisfactoria de `npm run build` el 2026-10-09.
- Se registró compilación sintáctica de `backend/app` con `python -m compileall` el 2026-10-09.
- Se comprobó respuesta HTTP 200 del servidor Vite para `/login`, `/registro` y `/recuperar-contrasena` el 2026-10-09.
- No hay evidencia de ejecución de FastAPI con dependencias instaladas, conexión autenticada a MySQL, creación de tablas, registro persistido, login real ni correo de recuperación.

## Errores, bloqueos y decisiones

- **Hecho:** la instancia MySQL local se identificó previamente como servicio `MySQL267`, puerto 3306; esta tarea documental no revalida ni conecta a ella.
- **Bloqueo:** para probar persistencia falta una configuración local utilizable y una ejecución controlada de FastAPI/migración. No se deben documentar como completadas las tablas ni el registro persistido hasta obtener evidencia.
- **Riesgo técnico:** `DashboardView.vue` importa `demoAuth.ts`, mientras que la autenticación principal usa Axios/FastAPI. Esta diferencia debe evaluarse antes de considerar administración de roles como integrada.
- **Decisión:** la migración `001_add_user_personal_data.sql` deja los nuevos datos personales como `NULL` para no invalidar usuarios históricos; el esquema de nuevos registros exige nombre, apellido paterno y teléfono, mientras apellido materno es opcional.

## Archivos involucrados

`frontend/src/components/AuthShell.vue`, `AuthForm.vue`; `frontend/src/views/LoginView.vue`, `RegisterView.vue`, `ForgotPasswordView.vue`; `frontend/src/services/api.ts`; `frontend/src/stores/auth.ts`; `backend/app/models.py`, `schemas.py`, `security.py`, `dependencies.py`, `main.py`, `database.py`; `backend/migrations/001_add_user_personal_data.sql`.

## Próxima actividad autorizable

Validar la configuración no sensible de MySQL local, instalar las dependencias Python en un entorno aislado, aplicar una migración no destructiva tras revisión y ejecutar pruebas controladas de registro, correo duplicado y login.
