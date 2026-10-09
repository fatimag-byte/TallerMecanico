# Fase M01 — Creación de roles y permisos

**Objetivo:** definir roles y permisos base para controlar el acceso del módulo M01.  
**Alcance documentado:** modelos, relaciones, semilla de roles y dependencias de interfaz.  
**Dependencias:** tablas `users`, `roles`, `permissions`, asociaciones y conexión MySQL verificada.  
**Estado actual:** EN PROCESO.  
**Última actualización:** 2026-10-09.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-RC-001 | Modelo de roles, permisos y asociaciones | NO VERIFICADO | `backend/app/models.py` | Entidades y FKs declaradas; falta creación comprobada en MySQL. |
| M01-RC-002 | Semilla de roles administrador y tecnico | NO VERIFICADO | `seed_roles()` en `backend/app/main.py` | Define cuatro permisos base; no hay ejecución demostrada. |
| M01-RC-003 | Asignación automática de rol al registrar | NO VERIFICADO | `/api/auth/register` | El primer usuario obtiene administrador; falta prueba real. |
| M01-RC-004 | Flujo UI para crear roles personalizados | PENDIENTE | Sin componente o endpoint específico identificado | No debe implementarse fuera de una solicitud posterior. |

## Estado técnico

Los roles actuales están definidos por código: `administrador` y `tecnico`. Los permisos base son `users:read`, `users:manage`, `workorders:read` y `workorders:write`. `Role.permissions` y `User.roles` utilizan tablas de asociación con claves foráneas y borrado en cascada.

La semilla se ejecutaría durante el evento de arranque de FastAPI después de `Base.metadata.create_all`. Su resultado no está verificado porque no hay ejecución real documentada contra MySQL.

## Pendientes y dependencias

La creación de roles adicionales y asignación granular vía API no aparecen implementadas. Antes de ampliar este alcance se requiere tener la base M01 disponible y validar los roles semilla existentes.
