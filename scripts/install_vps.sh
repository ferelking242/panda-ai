#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════
#  Panda AI — Installation VPS (Debian/Ubuntu)
#
#  Installe et configure :
#    - Dépendances système (Chromium/Patchright)
#    - Environnement Python (.venv) + requirements
#    - Navigateur Chromium pour Patchright
#    - Dashboard Next.js (Node 20)
#    - Services systemd : panda-ai (:8000) + panda-dashboard (:5000)
#
#  Usage:
#    bash scripts/install_vps.sh              # installation complète
#    bash scripts/install_vps.sh --no-node    # backend seul (pas de dashboard)
#
#  Idempotent : peut être relancé sans casser l'existant.
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_NODE=true
[[ "${1:-}" == "--no-node" ]] && WITH_NODE=false

log()  { echo -e "\033[1;32m[panda]\033[0m $*"; }
warn() { echo -e "\033[1;33m[panda]\033[0m $*"; }
die()  { echo -e "\033[1;31m[panda] ERREUR:\033[0m $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "À lancer en root (ou sudo bash scripts/install_vps.sh)"
command -v apt-get >/dev/null || die "Ce script cible Debian/Ubuntu (apt)."

# ── 1. Dépendances système ──────────────────────────────────────────
log "Installation des dépendances système..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  python3 python3-venv python3-pip curl ca-certificates git \
  fonts-liberation libasound2t64 libasound2 2>/dev/null \
  || apt-get install -y -qq python3 python3-venv python3-pip curl ca-certificates git fonts-liberation
# Libs Chromium (la liste exacte est résolue par patchright install-deps)
apt-get install -y -qq libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
  libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
  libxdamage1 libxrandr2 xdg-utils libxshmfence1 || true

# ── 2. Environnement Python ─────────────────────────────────────────
log "Création du venv Python (${REPO_DIR}/.venv)..."
python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" install --upgrade pip -q
log "Installation des dépendances Python..."
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/requirements.txt" -q
log "Téléchargement de Chromium pour Patchright..."
"$REPO_DIR/.venv/bin/patchright" install chromium
"$REPO_DIR/.venv/bin/patchright" install-deps chromium >/dev/null 2>&1 || true

# ── 3. Fichier .env ────────────────────────────────────────────────
if [[ ! -f "$REPO_DIR/.env" ]]; then
  log "Génération de .env avec un API_TOKEN aléatoire..."
  API_TOKEN="pnd_$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
  cat > "$REPO_DIR/.env" <<EOF
# Panda AI — configuration VPS (généré par install_vps.sh)
PROVIDER=chatgpt
# PROVIDER_CHAIN=chatgpt,claude,gemini
API_HOST=0.0.0.0
API_PORT=8000
HEADLESS=true
API_TOKEN=${API_TOKEN}
POOL_SIZE=1
RESPONSE_TIMEOUT=120000
LOG_LEVEL=INFO
EOF
  chmod 600 "$REPO_DIR/.env"
  log ".env créé (token inclus). Le token est aussi lisible avec: grep API_TOKEN ${REPO_DIR}/.env"
else
  warn ".env existe déjà — conservé tel quel."
fi

mkdir -p "$REPO_DIR/logs" "$REPO_DIR/browser_data" "$REPO_DIR/downloads/images"

# ── 4. Dashboard (Node 20) ─────────────────────────────────────────
if $WITH_NODE; then
  if ! command -v node >/dev/null || [[ "$(node -v | cut -dv -f2 | cut -d. -f1)" -lt 18 ]]; then
    log "Installation de Node.js 20 (NodeSource)..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null
    apt-get install -y -qq nodejs
  fi
  log "Build du dashboard Next.js..."
  cd "$REPO_DIR/dashboard"
  npm install --no-audit --no-fund
  npm run build
  cd "$REPO_DIR"
fi

# ── 5. Services systemd ────────────────────────────────────────────
log "Création des services systemd..."

cat > /etc/systemd/system/panda-ai.service <<EOF
[Unit]
Description=Panda AI Gateway (FastAPI + Patchright)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
ExecStart=${REPO_DIR}/.venv/bin/python -m src.api.server
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
NoNewPrivileges=true
ProtectSystem=full
ReadWritePaths=${REPO_DIR}

[Install]
WantedBy=multi-user.target
EOF

if $WITH_NODE; then
cat > /etc/systemd/system/panda-dashboard.service <<EOF
[Unit]
Description=Panda AI Dashboard (Next.js)
After=panda-ai.service network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}/dashboard
ExecStart=$(command -v node) server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=5000
Environment=API_ORIGIN=http://127.0.0.1:8000

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable --now panda-ai
$WITH_NODE && systemctl enable --now panda-dashboard

sleep 3
echo ""
log "═══════════════════════════════════════════════════════"
log " Installation terminée ✅"
log "═══════════════════════════════════════════════════════"
systemctl --no-pager --lines=3 status panda-ai || true
$WITH_NODE && systemctl --no-pager --lines=3 status panda-dashboard || true
echo ""
log "API       → http://$(curl -s ifconfig.me 2>/dev/null || echo VPS_IP):8000"
$WITH_NODE && log "Dashboard → http://$(curl -s ifconfig.me 2>/dev/null || echo VPS_IP):5000"
log "Token API → grep API_TOKEN ${REPO_DIR}/.env"
log "Logs      → journalctl -u panda-ai -f"
warn "Pense à ouvrir les ports 8000/5000 dans ton firewall (ufw allow 8000/tcp 5000/tcp)."
