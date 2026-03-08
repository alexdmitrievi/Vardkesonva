# Deploy on REG.RU VPS (Docker Compose + Nginx + SSL)

## 1) Prepare VPS

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo systemctl enable docker
sudo systemctl start docker
```

## 2) Upload project and configure env

```bash
git clone <your-repo-url> legal-automation
cd legal-automation
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
- set `APP_ENV=production`
- set `REQUIRE_AUTH=true`
- set strong `API_BEARER_TOKEN`
- set `CORS_ORIGINS=https://your-domain.ru`
- set `N8N_BASE_URL` to your n8n endpoint
- keep paths unchanged:
  - `/webhook/case/create`
  - `/webhook/case/event/create`
  - `/webhook/ai/legal/consult`

## 3) Run containers

```bash
docker compose up -d --build
docker compose ps
```

`docker-compose.yml` now includes healthchecks for both services and starts frontend only after backend is healthy.

Check:

```bash
curl -i http://127.0.0.1:8000/healthz
curl -i http://127.0.0.1:8080/legal_portal.html
```

## 4) Nginx reverse proxy

Create `/etc/nginx/sites-available/legal-automation`:

```nginx
server {
    listen 80;
    server_name your-domain.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
    }
}
```

Enable config:

```bash
sudo ln -sf /etc/nginx/sites-available/legal-automation /etc/nginx/sites-enabled/legal-automation
sudo nginx -t
sudo systemctl reload nginx
```

## 5) SSL with certbot

```bash
sudo certbot --nginx -d your-domain.ru
sudo certbot renew --dry-run
```

## 6) Update frontend config

Set runtime config in `frontend/config.js` (or via UI save in browser localStorage).  
Production defaults should be:
- `Backend API Base URL = https://your-domain.ru`
- keep `Direct n8n mode` disabled in production.

## 7) Ops checks

```bash
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
```

Recommended:
- nightly backups for `backend/storage`
- keep `backend/.env` outside git
- use firewall + allowlist for admin endpoints
