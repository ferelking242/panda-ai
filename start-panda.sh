#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Panda AI — Quick Start (Termux / Linux / macOS / Panda IDE Alpine)       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e
cd "$(dirname "$0")"

echo "🐼 Panda AI — Starting Gateway"
echo "================================"
echo ""

# ── 0. Detect platform ────────────────────────────────────────────────────────
ARCH=$(uname -m)
LIBC="glibc"
if ldd --version 2>&1 | grep -qi "musl" 2>/dev/null; then
    LIBC="musl"
elif [ -f /lib/ld-musl-* ] 2>/dev/null; then
    LIBC="musl"
fi

echo "  Platform: ${ARCH} / ${LIBC}"

# ── 1. Check .env ─────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "📝 No .env found — copying from .env.example"
    cp .env.example .env 2>/dev/null || cat > .env << 'ENVEOF'
PROVIDER=chatgpt
HEADLESS=true
API_PORT=8000
LOG_LEVEL=info
ENVEOF
    echo "   Edit .env with: nano .env"
    echo ""
fi

# ── 2. Activate venv ──────────────────────────────────────────────────────────
if [ -d .venv ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No .venv found — using system Python"
    echo "   Create one with: python3 -m venv .venv && source .venv/bin/activate"
fi

# ── 3. Check if patchright is available ────────────────────────────────────────
HAS_BROWSER=false
python3 -c "import patchright" 2>/dev/null && HAS_BROWSER=true

if [ "$HAS_BROWSER" = "false" ] && [ "$LIBC" = "musl" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  patchright non disponible (musl / ARM64)              ║"
    echo "║                                                            ║"
    echo "║  Le serveur démarre en mode HTTP (sans navigateur).        ║"
    echo "║  Pour activer le navigateur :                              ║"
    echo "║    bash scripts/setup_glibc.sh                             ║"
    echo "║    pip install patchright && patchright install chromium   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    export BROWSER_MODE="${BROWSER_MODE:-lightweight}"
fi

# ── 4. Start ──────────────────────────────────────────────────────────────────
echo "🚀 Starting Panda AI Gateway..."
echo "   Dashboard: http://localhost:8000/client"
echo "   API:       http://localhost:8000/v1"
echo "   Docs:      http://localhost:8000/docs"
echo ""

python -m src.api.server
