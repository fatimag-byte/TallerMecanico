# Orquestador de desarrollo — TallerMecanico

## Propósito

Convertir cada solicitud en una intervención controlada, limitada al alcance autorizado y trazable. Este documento es el índice operativo de la documentación Markdown del repositorio: antes de cambiar código, se consulta la fuente que corresponda al módulo afectado.

## Jerarquía de instrucciones

1. Instrucciones vigentes del usuario y del entorno.
2. [AGENTS.md](../../../../AGENTS.md): continuidad, Git, documentación y restricciones de operación.
3. [PLAN.md](../../../../PLAN.md): fase activa, alcance y actividades autorizables.
4. Bitácora de la fase afectada dentro de [analisis](../../../../analisis/).
5. Guías técnicas de este directorio `spec` según el componente implicado.

Si dos fuentes difieren, no se asume cuál es correcta: se registra la discrepancia, se contrasta con el código y se solicita aclaración únicamente si impide continuar con seguridad.

## Inventario documental gobernado

### Continuidad y planificación

| Documento | Uso obligatorio |
|---|---|
| [AGENTS.md](../../../../AGENTS.md) | Reglas de continuidad, revisión de Git y actualización de evidencia. |
| [PLAN.md](../../../../PLAN.md) | Alcance, fase activa y siguientes actividades. |
| [README.md](../../../../README.md) | Contexto público y forma de uso del proyecto. |
| [fase_taller_mecanico.md](../../../../analisis/fase_taller_mecanico.md) | Bitácora general, riesgos y estado transversal. |

### Bitácoras de análisis y fases

| Documento | Módulo o responsabilidad |
|---|---|
| [fase_autenticacion.md](../../../../analisis/fase_autenticacion.md) | Autenticación, sesiones y acceso. |
| [fase_crear_roles.md](../../../../analisis/fase_crear_roles.md) | Alta y validación de roles. |
| [fase_administrar_roles.md](../../../../analisis/fase_administrar_roles.md) | Administración de roles y asociaciones. |
| [fase_dashboard.md](../../../../analisis/fase_dashboard.md) | Panel administrativo. |
| [fase_diseno_interfaces.md](../../../../analisis/fase_diseno_interfaces.md) | Sistema visual e interfaces. |
| [fase_modo_oscuro.md](../../../../analisis/fase_modo_oscuro.md) | Tema claro/oscuro. |
| [fase_domicilios.md](../../../../analisis/fase_domicilios.md) | Catálogos y validación de domicilios. |
| [fase_administrar_talleres.md](../../../../analisis/fase_administrar_talleres.md) | Consulta y administración de talleres. |
| [fase_registrar_clientes.md](../../../../analisis/fase_registrar_clientes.md) | Alta de clientes. |
| [fase_administrar_clientes.md](../../../../analisis/fase_administrar_clientes.md) | Consulta y administración de clientes. |
| [fase_actualizar_clientes.md](../../../../analisis/fase_actualizar_clientes.md) | Actualización de clientes. |
| [fase_eliminacion_clientes.md](../../../../analisis/fase_eliminacion_clientes.md) | Baja lógica de clientes. |
| [fase_duplicados_clientes.md](../../../../analisis/fase_duplicados_clientes.md) | Detección de coincidencias de clientes. |
| [fase_registrar_vehiculos.md](../../../../analisis/fase_registrar_vehiculos.md) | Alta y asociación de vehículos. |
| [fase_administrar_vehiculos.md](../../../../analisis/fase_administrar_vehiculos.md) | Consulta, fotografías y baja lógica de vehículos. |

### Guías técnicas y documentación de apoyo

| Documento | Cuándo aplicarlo |
|---|---|
| [Python_FastAPI_Best_Practices_Skill.md](../skills/Python_FastAPI_Best_Practices_Skill.md) | Cambios en FastAPI, persistencia, seguridad o pruebas de backend. |
| [skil-vue.md](../frontend/skil-vue.md) | Cambios en Vue 3, TypeScript, componentes, reactividad, formularios o consumo de API. |
| [SKILL.md](../skills/orquestador/SKILL.md) | Skill instalable para invocar este flujo como `$orquestador`. |
| [documentacion-backend.md](../documentacion/backend/documentacion-backend.md) | Referencia de documentación backend cuando tenga contenido. |
| [docuementacion-frontend.md](../documentacion/fontend/docuementacion-frontend.md) | Referencia de documentación frontend cuando tenga contenido. |
| [orquestador.md](orquestador.md) | Este índice y flujo de orquestación. |

> Los dos archivos de documentación de apoyo están presentes pero vacíos al momento de esta revisión. Se conservan como referencias; no se les atribuyen reglas inexistentes.

## Flujo de orquestación

### 1. Descubrimiento

- Leer la solicitud, sus restricciones y los archivos que mencione.
- Consultar [AGENTS.md](../../../../AGENTS.md), [PLAN.md](../../../../PLAN.md), la bitácora general y la bitácora de la fase afectada.
- Revisar estado, rama, último commit y remoto de Git sin alterar el repositorio.
- Identificar implementaciones equivalentes antes de crear archivos, rutas, servicios o endpoints.

### 2. Clasificación

Determinar cuáles de estas áreas participan y leer su guía aplicable:

- Frontend Vue/TypeScript/Vuetify.
- Backend FastAPI/Pydantic/SQLAlchemy.
- MySQL, migraciones o integridad de datos.
- Autenticación, autorización, auditoría o seguridad.
- Pruebas, documentación o diseño visual.

### 3. Plan mínimo

Definir únicamente:

- objetivo verificable;
- alcance incluido y exclusiones;
- archivos y dependencias afectadas;
- riesgos de datos, seguridad o compatibilidad;
- validaciones y pruebas necesarias.

No se inicia un proyecto nuevo, no se sustituyen tecnologías funcionales y no se amplía el alcance sin autorización.

### 4. Ejecución

- Reutilizar arquitectura, componentes, servicios y endpoints existentes cuando sean adecuados.
- Aplicar validación de interfaz y servidor para entradas relevantes.
- Mantener autorización real en backend y persistencia real cuando el módulo la requiera.
- Usar migraciones incrementales y seguras solo cuando el cambio de esquema sea indispensable.
- Preservar los cambios no relacionados ya presentes en el árbol de trabajo.

### 5. Verificación y cierre

- Ejecutar las comprobaciones disponibles y registrar exactamente su resultado.
- No declarar una actividad como completada sin evidencia verificable.
- Actualizar la bitácora de la fase, [fase_taller_mecanico.md](../../../../analisis/fase_taller_mecanico.md) y [PLAN.md](../../../../PLAN.md) cuando se complete una fase o sesión de implementación, conforme a `AGENTS.md`.
- Si cambia la arquitectura documentada, actualizar los diagramas Mermaid correspondientes.
- Proponer un mensaje de commit sin ejecutar operaciones Git mutantes salvo autorización expresa.

## Formato de reporte

Cada entrega debe incluir, en proporción al cambio:

1. Resultado y alcance realizado.
2. Pruebas ejecutadas y su resultado real.
3. Bloqueos, riesgos o pendientes reales.
4. Archivos modificados o creados.
5. Siguiente actividad recomendada, si queda una dependencia abierta.

## Restricción permanente

Se entrega exclusivamente lo solicitado. No se usan datos simulados como implementación final, no se exponen secretos y no se presentan pruebas no ejecutadas como evidencia.
