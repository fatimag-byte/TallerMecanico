# Fase — Dashboard administrativo

| Actividad | Estado | Evidencia | Observaciones |
|---|---|---|---|
| Layout administrativo compartido | COMPLETADO | `frontend/src/App.vue` | Dashboard, roles y taller usan barra superior y menú lateral compartidos. |
| Sidebar expansible y fijable | COMPLETADO | `App.vue`; `npx vue-tsc -b` 2026-10-14 | Se expande al pasar el cursor; el botón de menú lo mantiene abierto y en táctil abre/cierra el drawer. |
| Métricas reales y contención de rol | COMPLETADO | `frontend/src/views/DashboardView.vue` | Datos obtenidos de sesión/API; roles y permisos se muestran como chips ajustables. |
| Verificación visual autenticada | PENDIENTE | Servidores activos en `127.0.0.1:5173` y `127.0.0.1:8000` | No se utilizaron las credenciales expuestas en una captura. |
| Rediseño moderno, responsivo y de permisos compactos | COMPLETADO 2026-11-10 | `frontend/src/views/DashboardView.vue`; `npm run build` | Encabezado de estado, métricas con jerarquía visual y tabla adaptativa; muestra dos permisos y agrupa los restantes en `+N` con tooltip para evitar saturación sin ocultar información. |
| Perfil de acceso en modal y contraste oscuro | COMPLETADO 2026-11-10 | `DashboardView.vue`, `utils/labels.ts`, `styles/theme.css`; recorrido visual autenticado | El botón de accesos abre un modal responsivo con usuario, correo, roles y permisos con lenguaje operativo; sus superficies, iconos y textos se verificaron en oscuro. |
| Encabezado puntual de permisos de usuario | COMPLETADO 2026-11-10 | `DashboardView.vue`; comprobación visual autenticada en claro y `npm run build` | Se sustituyó sólo el encabezado por escudo dorado, divisor vertical, etiqueta azul y textos jerárquicos; se eliminó X y el borde dorado superior. El tema oscuro se declara en el componente y compila; la sesión temporal de navegador no volvió a renderizar Dashboard tras alternar tema, sin alterar datos para forzarla. |
