# Fase M01 — Administración de roles y permisos

**Objetivo:** permitir consultar y administrar el acceso de usuarios conforme a roles y permisos.  
**Alcance documentado:** protección de endpoints y dashboard actual.  
**Dependencias:** autenticación real, persistencia MySQL, permiso `users:manage` y endpoints de administración.  
**Estado actual:** COMPLETADO PARA ROLES Y PERMISOS.
**Última actualización:** 2026-11-11.

| ID | Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|---|
| M01-RA-001 | Lectura protegida de usuarios | NO VERIFICADO | `GET /api/users`, `require_permission('users:read')` | Endpoint presente; falta prueba autenticada. |
| M01-RA-002 | Validación de token y permisos | COMPLETADO | `dependencies.py`, `security.py`, prueba MySQL/API | JWT de usuario técnico recibió `403` al consultar roles; rutas exigen `users:manage`. |
| M01-RA-003 | Interfaz de administración de usuarios/roles | COMPLETADO PARA ROLES | `ManageRolesView.vue`, `CreateRoleView.vue` | Catálogo, estadísticas reales, selección de rol, detalle, edición, asociación y retiro de usuarios conectan a FastAPI. |
| M01-RA-004 | API para modificar roles o permisos | COMPLETADO | `GET/POST/PUT/DELETE /api/roles`, `GET /api/roles/{id}/users` | CRUD real, disponibilidad de nombre, asociación/retiro de usuarios, conflicto `409` y protección del último administrador activo. |
| M01-RA-005 | Rediseño de Retirar usuario | COMPLETADO | ManageRolesView.vue; npm run build, 2026-11-11 | El diálogo conserva confirmRemoveUser y se alinea visualmente con Desactivar taller: encabezado rosa, advertencia roja centrada, identificación de usuario/rol, acciones gris y roja degradada, y variantes responsivas claro/oscuro. |
| M01-RA-006 | Confirmación única de operaciones | COMPLETADO | ManageRolesView.vue; npm run build, 2026-11-11 | Se eliminó el snackbar flotante. Todas las operaciones exitosas reutilizan la alerta horizontal bajo el encabezado y reinician un único temporizador de 3000 ms. |
| M01-RA-007 | Rediseño de Permisos asignados | COMPLETADO | ManageRolesView.vue; npm run build, 2026-11-11 | El detalle conserva permisos dinámicos reales y los presenta en tarjetas de dos columnas, con encabezado de rol, desplazamiento interno, acción de cierre y variantes claro/oscuro. |
| M01-RA-008 | Icono de rol en Permisos asignados | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Se sustituyó únicamente la corona por `mdi-account-outline` azul; se conservaron fondo dorado, tamaño, posición y diseño del modal. |
| M01-RA-009 | Acciones visuales de Permisos asignados | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Cerrar usa fondo blanco, borde gris y texto oscuro; hover, foco y pulsación cambian a rojo suave. Acceso completo usa fondo gris claro y texto azul. |
| M01-RA-010 | Rediseño de Eliminar rol | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | El diálogo reutiliza el patrón de advertencia de Retirar usuario: cabecera rosa, escudo azul, advertencia roja, rol dinámico en cápsula y acciones neutra/roja. `remove()` y sus protecciones se conservaron. |
| M01-RA-011 | Rediseño de Editar rol | COMPLETADO | `ManageRolesView.vue`; `npm run build`, 2026-11-11 | Modal compacto de dos columnas con cabecera/pie fijos, única zona de desplazamiento, seis grupos de permisos, selección individual/grupal y variantes claro/oscuro. Conserva `PUT /api/roles/{id}` y se habilita sólo ante cambios válidos. |
| M01-RA-012 | Ajuste de campos y etiquetas de Editar rol | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Nombre y descripción usan columnas equivalentes. Las etiquetas de permisos son negras y en negritas en claro, conservando sus checkboxes y estados; oscuro conserva contraste alto. |

| M01-RA-013 | Ajuste visual de Editar rol a referencia | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Cabecera azul clara con escudo/divisor dorados, permisos y tarjetas compactas a dos columnas, scroll central único y acción primaria gris/azul según validez. Se conservaron permisos reales y `PUT /api/roles/{id}`. |
| M01-RA-014 | Composición alternativa de Editar rol | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Se aplicó la referencia más reciente: cabecera blanca, icono azul sobre azul claro, divisor dorado y franja azul de permisos separada de las tarjetas. La funcionalidad permanece intacta. |
| M01-RA-015 | Fondo dorado de icono en Editar rol | COMPLETADO | `ManageRolesView.vue`; inspección visual local; `npm run build`, 2026-11-11 | Se cambió exclusivamente el fondo del icono de escudo de la cabecera a dorado suave `#F8E9CE`; el icono continúa azul. |
| M01-RA-016 | Host permitido en preview de Railway | COMPLETADO | `frontend/vite.config.ts`; inspección de configuración y `npm run build`, 2026-11-11 | `preview.allowedHosts` permite exclusivamente `just-clarity-production-3a213deb.up.railway.app`; se conservan el puerto local y las rutas SPA. |
| M01-RA-017 | Codificación de iconos en producción | COMPLETADO | `frontend/index.html`, `src/main.ts`, artefacto `dist/assets`; `npm run build`, 2026-11-11 | Se declaró UTF-8 para que los codepoints de Material Design Icons no se decodifiquen como caracteres como `ó°`. Se conservaron todos los iconos y el diseño. |

## Observaciones

El dashboard anterior puede conservar controles de demostración para usuarios; no se emplea para estas vistas. La navegación de roles se habilita únicamente con `users:manage` y las operaciones se realizan mediante Axios/FastAPI, nunca desde el navegador hacia MySQL. El modelo no tiene estado ni fecha de actualización para roles, por lo que la tabla muestra un guion en esas columnas en vez de inventar datos.
