# Public Deployment with Docker

[English](deployment.md) · [简体中文](deployment.zh-CN.md) · [← README](../README.md)

Running the web UI for **one person** is just `streamlit run`. To host it on a VPS for **many people**, use the bundled Docker setup — it packages the CadQuery/OpenCASCADE system libraries and applies public-facing hardening for you.

## 1. One command

GitHub Actions builds, tests, and publishes the image to GitHub Container Registry, so the server only has to pull it — no compiling there.

```bash
# Simplest: just run the published image
docker run -d --name boxforge -p 8501:8501 --restart unless-stopped ghcr.io/owenwoow/boxforge:latest

# Recommended: use the repo's docker-compose.yml (adds the resource limits in section 4).
# Only that one file is needed on the server.
docker compose pull && docker compose up -d

# Web UI is now on   http://<server-ip>:8501
# Logs:              docker compose logs -f
# Update:            docker compose pull && docker compose up -d
# Stop:              docker compose down
```

### Image tags

| Tag | What it is |
|---|---|
| `latest` | newest release (the most recent `vX.Y.Z` tag) |
| `X.Y.Z` / `X.Y` | a specific release — pin this in production |
| `edge` | current `main` branch |
| `dev` | current `dev` branch (unstable) |
| `sha-<commit>` | one exact commit |

Pick a tag for compose with `BOXFORGE_TAG`, e.g. `BOXFORGE_TAG=0.2.0 docker compose up -d`.

> Prefer building yourself? `docker compose up -d --build` builds from the checkout instead (first build takes several minutes to download CadQuery/OCP).

## 2. Put TLS + a domain in front (recommended)

Don't expose port `8501` directly. Terminate HTTPS with a reverse proxy and forward to the container. Streamlit uses WebSockets, so the proxy must pass the `Upgrade` headers.

**Caddy** (`Caddyfile` — automatic HTTPS):

```caddy
box.example.com {
    reverse_proxy localhost:8501
}
```

**Nginx**:

```nginx
server {
    server_name box.example.com;
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;      # WebSocket
        proxy_set_header Connection "upgrade";        # WebSocket
        proxy_read_timeout 3600s;
    }
    # add TLS via certbot / your certs
}
```

With a proxy on the same host, bind the app to localhost only — change the compose port mapping to `"127.0.0.1:8501:8501"` so it isn't reachable from the open internet except through the proxy.

## 3. What's hardened for public use

- **Non-root container**, Streamlit telemetry off, dev toolbar & error stack traces hidden (`box_generator/.streamlit/config.toml`).
- **Resource ceiling** in `docker-compose.yml` (`cpus`, `memory`, `pids_limit`) — CadQuery builds are CPU/RAM heavy, so this caps the damage from one abusive request.
- **Bounded caches & disk** — previews live in a size-limited `tmpfs`; old previews and cached models are pruned automatically, so disk/RAM don't creep up.
- **Input abuse guards** (`box_builder/validate.py`) — the partition tree (pasteable as raw YAML in the UI) is capped in nesting depth and total dividers, and export filenames are stripped to a safe basename so they can't traverse the filesystem.

## 4. Tuning the limits

Edit `docker-compose.yml` before deploying to match your server:

| Setting | Meaning | Raise if… |
|---|---|---|
| `cpus` / `memory` | per-container hard ceiling | builds feel slow on a beefy box |
| `pids_limit` | max processes/threads | you see thread-limit errors |
| `tmpfs /tmp size` | preview STL scratch space | you serve very large models |

Model-cost caps live in code: `MAX_PARTITION_DEPTH` / `MAX_PARTITION_NODES` in `box_builder/validate.py`, and `MAX_PREVIEW_FILES` / cache size in `box_generator/app.py`.
