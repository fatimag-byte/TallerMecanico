# Fase — Desactivación lógica de clientes

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|
| Estado, auditoría y confirmación | COMPLETADO | `CustomersManageView.vue`, `PATCH /api/customers/{id}/status` existente | La baja sigue siendo lógica y conserva el historial. El diálogo ahora comunica el impacto en lenguaje sencillo, muestra el cliente seleccionado y conserva la operación existente. |
| Diseño de diálogo de baja | COMPLETADO | `CustomersManageView.vue`, `theme.css`; `npm run build` 2026-11-10 | Modal centrado de advertencia sin franja dorada, icono azul sobre rojo suave, aviso rojo, acciones Cancelar gris/hover oscuro y Desactivar con degradado rojo. Incluye variante oscura. |
