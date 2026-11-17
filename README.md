# Kick Fleet

Control plane para automatización de navegador distribuida: cuentas de prueba autorizadas y simulación de chat. No infla viewers ni followers.

Stack: Docker Compose, Chromium headed (Xvfb + VNC + noVNC), Playwright, FastAPI, Redis, PostgreSQL, Next.js.

## Arranque local (Windows + Docker Desktop)

```powershell
Copy-Item .env.example .env
.\scripts\dev.ps1
```

Dashboard: http://localhost:3000  
API: http://localhost:8000/health  
Previews: http://localhost:6081 · 6082 · 6083

## Deploy Linux VPS

```bash
cp .env.example .env
# rota FERNET_KEY
chmod +x scripts/deploy.sh scripts/healthcheck.sh
./scripts/deploy.sh
./scripts/healthcheck.sh
```

HTTP en `:80` (dashboard, `/api`, `/ws`, `/vnc/worker-0N/`).

## Claude in Chrome

Los workers van headed. Montá la extensión descomprimida y definí `CLAUDE_EXTENSION_DIR=/opt/claude-extension` en el worker. Sin ese mount, Playwright y la supervisión visual (VNC + inspect a11y) siguen disponibles.

## Contrato

- Imágenes y compose iguales en Windows y VPS.
- Perfiles Chromium persistentes por worker.
- Credenciales cifradas (`FERNET_KEY`).
- CPU/RAM limitados por contenedor.
