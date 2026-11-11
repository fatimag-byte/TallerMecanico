# Fase — Domicilios dinámicos

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|
| Servicio interno de consulta postal | COMPLETADO | `backend/app/main.py`: `/api/ubicaciones/*`; proveedor `cp.terio.dev` con datos normalizados de SEPOMEX | El navegador sólo consulta FastAPI; se aplican timeout, caché de estados/municipios y mensajes de indisponibilidad. |
| Flujo Estado → Municipio → Colonia → Código postal | COMPLETADO | `frontend/src/components/SmartAddressFields.vue`, reutilizado en `WorkshopRegisterView.vue`, `CustomerRegisterView.vue` y `CustomersManageView.vue` | Limpia dependencias al cambiar el nivel superior, evita respuestas obsoletas mediante contador de solicitud y no descarga el catálogo nacional. |
| Búsqueda inversa por código postal | COMPLETADO | Prueba autenticada local: CP `42860` → Hidalgo / Tepeji del Río de Ocampo / 5 asentamientos | Cuando hay varias localidades se deja la selección pendiente; no se selecciona una de manera arbitraria. |
| Validación backend de combinación geográfica | COMPLETADO | `_validate_geography` en `backend/app/main.py` | Rechaza estado, municipio, colonia y CP inconsistentes; no persiste datos si la fuente falla. |
| Persistencia de domicilio completo de cliente | COMPLETADO | Migración `20261014_0003_customer_address_catalog.py` aplicada con Alembic | Columnas opcionales para proteger registros existentes; las nuevas altas desde la SPA solicitan ambos valores. |
| Compilación y recorrido visual | COMPLETADO | `npm run build`; SPA en `http://127.0.0.1:5173/talleres` | Se verificaron visualmente los selectores, municipios filtrados y la carga inversa. |
