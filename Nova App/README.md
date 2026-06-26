# Nova App

Nova App is a Progressive Web App for the Nova Raspberry Pi assistant. It is installed through a browser with Add to Home Screen and can be hosted behind Cloudflare.

## Run Locally

From the main Nova folder:

```bash
python3 "Nova App/backend/server.py"
```

Open:

```text
http://127.0.0.1:8765
```

Set these before exposing the app:

```env
NOVA_APP_HOST=127.0.0.1
NOVA_APP_PORT=8765
NOVA_APP_PASSWORD=change_this_before_cloudflare
```

## Structure

- `backend/server.py`: standard-library HTTP server, static file server, JSON API, and Server-Sent Events.
- `backend/auth.py`: password login and session cookie management.
- `backend/providers.py`: status snapshots from Nova modules.
- `frontend/index.html`: app shell and screens.
- `frontend/src/app.js`: UI state, navigation, chat, SSE updates.
- `frontend/src/api.js`: fetch helpers.
- `frontend/src/styles.css`: responsive light/dark styling.
- `frontend/service-worker.js`: offline app-shell caching.
- `frontend/manifest.webmanifest`: PWA install metadata.
- `frontend/assets/nova-icon.svg`: install icon.

## APIs

- `POST /api/login`
- `POST /api/logout`
- `GET /api/session`
- `GET /api/status`
- `GET /api/events`
- `POST /api/command`
- `POST /api/backup/manual`
- `POST /api/settings`
- `GET /api/camera/stream`

## Cloudflare

Recommended setup:

1. Run Nova App on the Raspberry Pi bound to `127.0.0.1`.
2. Use Cloudflare Tunnel to expose the local service.
3. Put Cloudflare Access in front of the hostname.
4. Set `NOVA_APP_PASSWORD` to a strong local password.
5. Use HTTPS from Cloudflare so PWA install and service worker features work.

## Install

On iPhone or iPad:

1. Open the Cloudflare HTTPS URL in Safari.
2. Tap Share.
3. Tap Add to Home Screen.

On Android:

1. Open the HTTPS URL in Chrome.
2. Tap Install app or Add to Home screen.

On desktop:

1. Open the HTTPS URL in Chrome or Edge.
2. Click the install icon in the address bar.
