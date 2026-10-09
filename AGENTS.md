# Continuidad de desarrollo para Codex

Antes de iniciar trabajo de desarrollo, leer `PLAN.md`, `analisis/fase_taller_mecanico.md` y el documento de la fase activa. Consultar además el estado de Git con comandos de lectura, rama, último commit y remoto cuando exista.

Presentar un resumen breve de estado: trabajo terminado, pendientes, fallos o bloqueos, dependencias y siguiente actividad recomendada. No asumir contexto de conversaciones anteriores; el código, Git y la documentación son las fuentes de verdad.

Si documentación y código difieren, señalar la discrepancia y verificarla antes de modificar código. Trabajar solamente dentro del módulo y alcance explícitamente solicitados.

Al finalizar una fase o sesión de implementación, actualizar la bitácora de fase, `analisis/fase_taller_mecanico.md` y `PLAN.md` con evidencia real, incluidas pruebas fallidas o bloqueadas. Actualizar diagramas Mermaid si cambió la arquitectura representada. Proponer un mensaje de commit, pero no ejecutar `git add`, `git commit`, `git push`, `git pull` ni operaciones destructivas sin autorización expresa.

No exponer ni leer en respuestas secretos de `.env`, tokens, claves JWT o contraseñas. No marcar una actividad como COMPLETADO sin evidencia de implementación y verificación satisfactoria.
