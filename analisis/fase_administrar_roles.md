# Fase M01 — Administración de roles y permisos

**Objetivo:** permitir consultar y administrar el acceso de usuarios conforme a roles y permisos.  
**Alcance documentado:** protección de endpoints y dashboard actual.  
**Dependencias:** autenticación real, persistencia MySQL, permiso `users:manage` y endpoints de administración.  
**Estado actual:** EN PROCESO.  
**Última actualización:** 2026-10-09.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-RA-001 | Lectura protegida de usuarios | NO VERIFICADO | `GET /api/users`, `require_permission('users:read')` | Endpoint presente; falta prueba autenticada. |
| M01-RA-002 | Validación de token y permisos | NO VERIFICADO | `dependencies.py`, `security.py` | Código presente; no hay prueba de rechazo 401/403. |
| M01-RA-003 | Interfaz de administración de usuarios/roles | EN PROCESO | `frontend/src/views/DashboardView.vue` | La vista usa `demoAuth.ts`, no el endpoint real; no debe considerarse integrada. |
| M01-RA-004 | API para modificar roles o permisos | PENDIENTE | No se identificó endpoint de escritura | Requiere autorización de alcance y pruebas posteriores. |

## Observaciones

El backend contiene una autorización por permiso para consultar usuarios, pero no expone operaciones de actualización de roles/permisos. El dashboard presenta controles de edición sobre almacenamiento local de demostración; existe una inconsistencia con el uso de Axios/FastAPI en el módulo de login que debe resolverse en una fase de integración, no durante esta documentación.
