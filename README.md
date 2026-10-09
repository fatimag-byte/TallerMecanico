# Taller Mecánico — Autenticación

SPA con Vue 3, Vite, TypeScript y Vuetify 3, respaldada por FastAPI y MySQL.

## Seguimiento del proyecto

La bitácora técnica, fase activa, riesgos y próximos pasos se encuentran en [analisis/fase_taller_mecanico.md](analisis/fase_taller_mecanico.md). Las reglas de continuidad para futuras sesiones están en `AGENTS.md` y la planificación progresiva en `PLAN.md`.

## Inicio rápido

1. Copia `backend/.env.example` a `backend/.env` y configura MySQL y las claves JWT.
2. Crea la base de datos: `CREATE DATABASE taller_mecanico_db CHARACTER SET utf8mb4;`.
3. Backend:
   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
4. Frontend (otra terminal):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

La primera cuenta registrada recibe el rol `administrador`; las posteriores reciben `tecnico`.

## Seguridad incluida

- Passwords con bcrypt y salt aleatorio por usuario (nunca se almacenan passwords en claro).
- Access token JWT de corta duración y refresh token aleatorio rotativo almacenado sólo como hash SHA-256.
- Renovación automática transparente ante un `401`; cierre de sesión si la sesión ya no es válida.
- Registro único por correo, mensajes de validación claros y restricciones de roles/permisos en servidor.
