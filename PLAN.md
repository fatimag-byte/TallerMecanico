# Plan de trabajo — TallerMecanico

## Objetivo general

Construir progresivamente una aplicación para la gestión de talleres mecánicos, comenzando por M01 — Identidad, Usuarios, Roles y Permisos.

## Fase activa: M01 — Validación de integración

### Dependencias abiertas

- Instancia MySQL local disponible y configuración local no versionada.
- Dependencias Python instaladas en un entorno aislado.
- Revisión no destructiva de la migración de datos personales.

### Próximas actividades autorizables

| ID | Actividad planificada | Criterio de aceptación |
|---|---|---|
| PLAN-M01-01 | Verificar conexión FastAPI–MySQL sin exponer credenciales | Conexión autenticada y base objetivo identificada. |
| PLAN-M01-02 | Aplicar/revisar migración no destructiva de usuarios | Tablas y columnas verificadas sin pérdida de registros. |
| PLAN-M01-03 | Probar registro, duplicado y login reales | Evidencia de datos persistidos, rechazo 409 y autenticación exitosa. |
| PLAN-M01-04 | Revisar integración real del dashboard de roles | Eliminar o aislar la dependencia de demostración antes de declararlo integrado. |
| PLAN-M01-05 | Diseñar recuperación de contraseña real | Token de un solo uso y proveedor de correo definidos en una fase autorizada. |

## Módulos posteriores

Clientes, vehículos, órdenes de reparación, diagnósticos, refacciones e inventario permanecen fuera de alcance hasta recibir una solicitud específica.

## Criterio de cierre de M01

M01 sólo podrá cerrarse cuando la base de datos, registro, login, renovación de sesión, duplicados y autorización básica cuenten con evidencia de pruebas reales, y el alcance de recuperación de contraseña haya sido resuelto o diferido explícitamente.
