# Fase M01 — Creación de roles y permisos

**Objetivo:** definir roles y permisos base para controlar el acceso del módulo M01.  
**Alcance documentado:** modelos, relaciones, semilla de roles y dependencias de interfaz.  
**Dependencias:** tablas `users`, `roles`, `permissions`, asociaciones y conexión MySQL verificada.  
**Estado actual:** COMPLETADO.
**Última actualización:** 2026-11-11.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-RC-001 | Modelo de roles, permisos y asociaciones | COMPLETADO | `backend/app/models.py`, MySQL local | Tablas `roles`, `permissions`, `user_roles` y `role_permissions` verificadas tras Alembic. |
| M01-RC-002 | Semilla de roles administrador y tecnico | COMPLETADO | `seed_roles()` y MySQL local | Roles `administrador` y `tecnico`, con cuatro permisos base, presentes sin duplicación. |
| M01-RC-003 | Asignación automática de rol al registrar | COMPLETADO | pruebas reales de registro M01 | Registro público conserva el rol técnico; no recibe permisos administrativos. |
| M01-RC-004 | Flujo UI para crear roles personalizados | COMPLETADO | `CreateRoleView.vue`, `GET /api/roles/check-name`, `POST /api/roles` | Diseño administrativo de dos tarjetas; la disponibilidad se consulta en FastAPI/MySQL y la creación persiste roles sin privilegios implícitos. |
| M01-RC-005 | Rediseño de alta y asignación de permisos | COMPLETADO | CreateRoleView.vue, ManageRolesView.vue, npm run build, 2026-11-11 | La alta usa dos columnas, tarjetas, acordeones por módulo, selección total/parcial y validación de nombre único, permisos y descripción de hasta 200 caracteres. Tras crear por API redirige a Administración de roles y muestra la alerta verde solicitada durante 5 s. |

## Estado técnico

Los roles actuales están definidos por código: `administrador` y `tecnico`. Los permisos base son `users:read`, `users:manage`, `workorders:read` y `workorders:write`. `Role.permissions` y `User.roles` utilizan tablas de asociación con claves foráneas y borrado en cascada.

La siembra es idempotente y se ejecuta sin `Base.metadata.create_all`; las estructuras se administran exclusivamente con Alembic. Las tablas y los datos base fueron verificados contra MySQL local. Tras la depuración autorizada de usuarios del 2026-10-09, existe una sola cuenta administradora activa asociada al rol `administrador`.

## Pendientes y dependencias

La API disponible expone permisos de consulta, escritura y administración por módulo; la interfaz los asigna de forma individual y no inventa permisos CRUD que el contrato no persiste.
