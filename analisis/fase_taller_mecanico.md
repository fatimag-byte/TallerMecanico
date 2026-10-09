# Seguimiento general — TallerMecanico

**Descripción:** aplicación SPA para gestión de talleres mecánicos. El código actual se concentra en M01 — Identidad, Usuarios, Roles y Permisos.  
**Arquitectura identificada:** Vue 3 + TypeScript + Vite + Vuetify 3 + Vue Router/Axios en frontend; FastAPI + SQLAlchemy + PyMySQL en backend; MySQL configurado como persistencia objetivo.  
**Fase activa:** M01, validación pendiente de integración real con MySQL.  
**Última actualización:** 2026-10-09.

## Tecnologías comprobables

- Frontend: Vue `^3.5.13`, Vue Router `^4.5.0`, Vuetify `^3.7.6`, Axios `^1.7.9`, Vite `^6.0.5`, TypeScript `~5.6.3`.
- Backend declarado: FastAPI `0.115.6`, SQLAlchemy `2.0.36`, PyMySQL `1.1.1`, passlib bcrypt `1.7.4`, python-jose `3.3.0`.

## Fases registradas

| Fase | Completado | En proceso | Pendiente | Fallido | Bloqueado | No verificado | Última actualización |
|---|---:|---:|---:|---:|---:|---:|---|
| M01 — Autenticación | 1 | 1 | 1 | 0 | 1 | 5 | 2026-10-09 |
| M01 — Crear roles | 0 | 0 | 1 | 0 | 0 | 3 | 2026-10-09 |
| M01 — Administrar roles | 0 | 1 | 1 | 0 | 0 | 2 | 2026-10-09 |

Los conteos provienen de las tablas de las tres bitácoras de fase.

## Módulos identificados

- **M01:** autenticación, registro, recuperación inicial, usuarios, roles, permisos y refresh tokens.
- **Futuros sin código identificado:** clientes, vehículos, órdenes de reparación, diagnósticos, refacciones e inventario.

## Riesgos técnicos principales

1. La persistencia MySQL, migraciones y pruebas de API no cuentan con evidencia de ejecución satisfactoria.
2. Recuperación de contraseña no envía correo ni implementa token de restablecimiento.
3. El dashboard usa almacenamiento local de demostración para usuarios/roles, distinto al backend real.
4. No existe repositorio Git inicializado ni remoto GitHub configurado en la raíz actual.

## RESUMEN DE CONTINUIDAD

- **Dónde quedó el proyecto:** M01, después de preparar visualmente autenticación y extender el contrato de registro con apellidos y teléfono.
- **Terminado y verificado:** build de frontend y disponibilidad HTTP de rutas SPA fueron registrados; no equivalen a prueba de negocio.
- **Pendiente o no verificado:** FastAPI en ejecución, configuración real de MySQL, migración, persistencia, duplicados, login real, refresh y recuperación por correo.
- **Bloqueos abiertos:** falta evidencia/configuración utilizable para pruebas de MySQL y dependencias Python en tiempo de ejecución.
- **Últimos archivos funcionales identificados:** `AuthForm.vue`, vistas de autenticación, `auth.ts`, `models.py`, `schemas.py`, `main.py`, `001_add_user_personal_data.sql`.
- **Git:** no existe commit ni rama disponible porque la raíz no es un repositorio Git; no hay remoto GitHub.
- **Siguiente sesión:** revisar variables locales sin exponer secretos, validar MySQL y dependencias, aplicar sólo migraciones no destructivas autorizadas y ejecutar pruebas controladas de M01.
