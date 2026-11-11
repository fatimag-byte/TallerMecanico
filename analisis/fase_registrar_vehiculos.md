# Fase — Registro básico de vehículos

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|
| Alta, VIN y asociación con cliente | COMPLETADO | `VehicleRegisterForm.vue`, `POST /api/vehicles`; cliente/taller validados en FastAPI | VIN validado y relación persistente con cliente y taller. |
| Detección previa de VIN duplicado | COMPLETADO | `GET /api/vehicles/check-vin`; prueba autenticada local devolvió duplicado para VIN existente | MySQL conserva índice único y el formulario informa el resultado antes del alta. |
| Carga múltiple de fotos | COMPLETADO | `VehicleRegisterForm.vue`, `POST /api/vehicles/{id}/photos`, tabla `vehicle_photos` | JPG, PNG y WebP; máximo 15 MB por archivo, validado en cliente y servidor. |
| Autorización de alta | COMPLETADO | Permiso `vehicles:manage`; roles Administrador y Recepcionista | FastAPI realiza la autorización real; la interfaz no es el único control. |
| Validación y confirmación visual del registro | COMPLETADO | `VehicleRegisterForm.vue`; `npm run build` 2026-11-10 | El botón requiere taller y cliente activos, VIN de 17 caracteres previamente verificado y no duplicado, marca, modelo y año válido; fotos y placas siguen opcionales. Se bloquea durante envío, limpia el formulario tras éxito confirmado y muestra alertas verde/roja durante 5 s. |
| Iconografía de campos y secciones | COMPLETADO | `VehicleRegisterForm.vue` | Asociación, Datos del vehículo y Fotografías usan iconos azul `#2850E8` sobre dorado suave `#F8E9CE`; Marca, Modelo, Año y Placas incluyen iconos grises. |
| Reinicio integral de fotografías después de alta | COMPLETADO | `VehicleRegisterForm.vue`; `npm run build` 2026-11-10 | Tras éxito confirmado, se liberan URLs temporales, se vacían archivos y vistas previas, y se recrea el selector de archivos mediante una clave reactiva para borrar su estado visual interno. La confirmación se mantiene 5 s. |
