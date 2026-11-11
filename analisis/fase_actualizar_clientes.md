# Fase — Actualizar clientes

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|
| Modal y endpoint de actualización | COMPLETADO | `CustomersManageView.vue`, `customers.ts`, `main.py` | Existen `PUT /api/customers/{customer_id}` y el modal de edición por fila; el taller permanece asociado como dato de solo lectura. |
| Corrección de payload opcional y detección de cambios | COMPLETADO | `CustomersManageView.vue`; log local con `POST /api/customers/duplicates` 422 previo; validación directa de `CustomerRequest` 2026-11-10 | La causa era enviar cadenas vacías a opcionales (`secondary_email` y `secondary_phone`), que Pydantic rechaza antes del PUT. Ahora se normalizan a `null`; sin cambios no se invoca ninguna API. |
| Prueba sin cambios en interfaz | COMPLETADO | `/clientes`, cliente activo, 2026-11-10 | Al pulsar Guardar cambios sin editar, el modal permaneció visible y no se mostró aviso. |
| Prueba de persistencia con datos reales | NO VERIFICADO | No se alteraron registros reales durante la corrección | La ruta y el modelo se verificaron estáticamente y con payload normalizado; queda pendiente una modificación autorizada de un registro de prueba para observar el PUT y la recarga. |
| Icono de cabecera de Actualizar cliente | COMPLETADO | `CustomersManageView.vue` | Únicamente el recuadro del icono persona-lápiz usa `#64A6E3`; el icono permanece blanco y no se modificó la estructura del modal. |
| Fondo del icono de cabecera | COMPLETADO | `CustomersManageView.vue` | El recuadro de persona-lápiz usa dorado suave `#F8E9CE`; el icono permanece azul y el resto del modal no cambia. |
