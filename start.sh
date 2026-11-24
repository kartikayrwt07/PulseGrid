#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-4173}"

echo "Starting PulseGrid Local Demo..."

if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created .env from .env.example"
fi

# Ensure a strong SECRET_KEY exists before launching uvicorn
if grep -q "change-me-use-openssl-rand-hex-32" "$ROOT_DIR/.env"; then
  RAND_KEY="$(python -c "import secrets; print(secrets.token_hex(32))")"
  python -c "
from pathlib import Path
p = Path(r'$ROOT_DIR/.env')
p.write_text(p.read_text().replace('change-me-use-openssl-rand-hex-32', '$RAND_KEY'))
"
fi

cd "$ROOT_DIR/backend"
python -m pip install -r requirements.txt -q
python ml/generate_data.py
python ml/train_and_evaluate.py

python -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --log-level warning &
BACKEND_PID=$!

cd "$ROOT_DIR/frontend"
npm install -q --no-audit --no-fund
VITE_PROXY_TARGET="http://127.0.0.1:${BACKEND_PORT}" npm run build
VITE_PROXY_TARGET="http://127.0.0.1:${BACKEND_PORT}" npm run preview -- --host 127.0.0.1 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT

sleep 3
echo "Health check:"
curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/v1/health"
echo ""
echo "PulseGrid ready!"
echo "  Frontend: http://127.0.0.1:${FRONTEND_PORT}"
echo "  Backend:  http://127.0.0.1:${BACKEND_PORT}/docs"
echo "Press Ctrl+C to stop."
wait
