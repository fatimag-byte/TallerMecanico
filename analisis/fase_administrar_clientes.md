# Fase — Administrar clientes

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|
| Tabla, buscador y filtros | COMPLETADO | `frontend/src/views/CustomersManageView.vue`; vista abierta en `/clientes` | Muestra datos de MySQL, taller, contacto, estado y fecha. |
| Actualización por modal | COMPLETADO | Modal visible; `PUT /api/customers/{id}` 200 | El taller es solo lectura y el backend conserva la asociación. |
| Desactivación lógica | COMPLETADO | `PATCH /api/customers/{id}/status` 200 | Conserva el registro y deja auditoría. |
| Asociación de vehículo | COMPLETADO | Botón visible y navegación a `/vehiculos/registro` | Precarga cliente y taller. |
| Rediseño de Actualizar cliente y avisos de guardado | COMPLETADO | `frontend/src/views/CustomersManageView.vue`; `npm run build` 2026-11-10 | Modal organizado en Datos personales, Domicilio y Contacto con cabecera azul clara, iconografía dorada/azul, adaptación responsiva y oscura. Tras éxito de API cierra, recarga tabla y muestra aviso verde por 3 s; ante error conserva modal y datos con el mensaje solicitado. |
| Corrección de guardado en Actualizar cliente | COMPLETADO | `CustomersManageView.vue`, `customers.ts`, `CustomerRequest`; `npm run build` 2026-11-10 | Se corrigió el 422 previo: los opcionales vacíos se convierten a `null` antes de validar duplicados o actualizar. No hay petición, cierre ni aviso cuando el payload normalizado no cambió. Los errores muestran el detalle real del backend durante 3 s. |
