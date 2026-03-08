#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "${ROOT_DIR}/backend/.env" ]]; then
  cp "${ROOT_DIR}/backend/.env.example" "${ROOT_DIR}/backend/.env"
  echo "Created backend/.env from .env.example"
fi

python -m pip install -r "${ROOT_DIR}/backend/requirements.txt"

echo "Starting backend on http://localhost:8000"
(
  cd "${ROOT_DIR}/backend"
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &

echo "Starting static frontend on http://localhost:8080/legal_portal.html"
(
  cd "${ROOT_DIR}/frontend"
  python -m http.server 8080
)
