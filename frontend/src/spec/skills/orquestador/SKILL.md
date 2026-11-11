---
name: orquestador
description: Orquesta tareas del proyecto TallerMecanico, aplicando su documentación, alcance, seguridad, pruebas y trazabilidad. Úsala explícitamente para iniciar trabajo en este repositorio.
metadata:
  short-description: Orquesta tareas de TallerMecanico
---

# Orquestador — TallerMecanico

Usa esta skill únicamente cuando el usuario la invoque como `$orquestador` para trabajar en el repositorio TallerMecanico. Su fuente de reglas del proyecto es `frontend/src/spec/orquestador/orquestador.md`; no la sustituyas ni dupliques.

## Inicio obligatorio

1. Localiza y lee por completo `frontend/src/spec/orquestador/orquestador.md` desde la raíz del repositorio activo.
2. Sigue su jerarquía de instrucciones y consulta los documentos que enruta para el módulo solicitado.
3. Lee `AGENTS.md`, `PLAN.md`, `analisis/fase_taller_mecanico.md` y la bitácora de la fase afectada antes de modificar archivos.
4. Consulta Git de forma no mutante: estado, rama, último commit y remoto.
5. Resume el estado real: terminado, pendientes, fallos, bloqueos, dependencias y siguiente actividad recomendada.

## Ejecución

- Mantén el alcance de la solicitud; no sustituyas tecnología, arquitectura ni componentes que ya funcionen.
- Para frontend, aplica `frontend/src/spec/frontend/skil-vue.md`.
- Para backend, persistencia, seguridad o pruebas FastAPI, aplica `frontend/src/spec/skills/Python_FastAPI_Best_Practices_Skill.md`.
- Reutiliza módulos existentes antes de crear rutas, servicios, componentes o endpoints.
- Ejecuta pruebas proporcionales al cambio y nunca describas como ejecutada una prueba que no lo fue.
- Actualiza las bitácoras y `PLAN.md` cuando la sesión implemente una fase o cambio documentable, conforme a `AGENTS.md`.

## Límites

- No expongas secretos, tokens ni contraseñas.
- No hagas operaciones Git mutantes sin autorización explícita.
- Si el archivo fuente del orquestador no existe o sus enlaces no resuelven, repórtalo y corrígelo solo si el usuario lo autorizó dentro de la solicitud.
