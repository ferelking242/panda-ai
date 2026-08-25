#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  setup_glibc.sh — Installe le runtime glibc complet + deps Chromium       ║
# ║                                                                            ║
# ║  Objectif : rendre Panda IDE (Alpine/musl) 100% compatible glibc pour     ║
# ║  patchright, playwright, Chromium, et tout binaire manylinux.              ║
# ║                                                                            ║
# ║  Usage :                                                                   ║
# ║    chmod +x scripts/setup_glibc.sh                                         ║
# ║    sudo bash scripts/setup_glibc.sh                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[setup]${NC} $*"; }
ok()   { echo -e "${GREEN}  ✅ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $*${NC}"; }
fail() { echo -e "${RED}  ❌ $*${NC}"; }

# ── 0. Détection de la plateforme ────────────────────────────────────────────
log "Détection de la plateforme..."

ARCH=$(uname -m)
LIBC_TYPE=""
if ldd --version 2>&1 | grep -qi "glibc"; then
    LIBC_TYPE="glibc"
elif ldd --version 2>&1 | grep -qi "musl"; then
    LIBC_TYPE="musl"
else
    # Fallback : vérifier si ldd utilise musl
    if file /lib/ld-musl-* 2>/dev/null | grep -q "musl"; then
        LIBC_TYPE="musl"
    elif file /lib64/ld-linux-x86-64.so.2 2>/dev/null | grep -q "ELF"; then
        LIBC_TYPE="glibc"
    else
        LIBC_TYPE="unknown"
    fi
fi

HAS_PACKAGE_MANAGER=""
if command -v apk >/dev/null 2>&1; then
    HAS_PACKAGE_MANAGER="apk"
elif command -v apt-get >/dev/null 2>&1; then
    HAS_PACKAGE_MANAGER="apt"
elif command -v dnf >/dev/null 2>&1; then
    HAS_PACKAGE_MANAGER="dnf"
fi

log "Architecture: ${ARCH}"
log "libc: ${LIBC_TYPE}"
log "Package manager: ${HAS_PACKAGE_MANAGER}"

# ── 1. Installer les dépendances système ──────────────────────────────────────
install_system_deps() {
    log "Installation des dépendances système..."

    if [ "$HAS_PACKAGE_MANAGER" = "apk" ]; then
        # ═══ ALPINE (musl) ═══
        # On installe TOUT ce que Chromium binaire a besoin au runtime
        apk update
        apk upgrade --no-cache

        # --- glibc compatibility layer (le coeur du fix) ---
        apk add --no-cache gcompat || {
            warn "gcompat pas disponible, tentative libc6-compat..."
            apk add --no-cache libc6-compat || warn "libc6-compat non dispo"
        }

        # --- Chromium runtime dependencies (NSS, ATK, GLib, X11, etc.) ---
        apk add --no-cache \
            nss \
            freetype \
            harfbuzz \
            ttf-freefont \
            font-noto \
            font-noto-cjk \
            dbus \
            mesa-dri-gallium \
            libstdc++ \
            libgcc \
            libx11 \
            libxcomposite \
            libxdamage \
            libxrandr \
            libxcb \
            libxext \
            libxfixes \
            libxi \
            libxtst \
            libdrm \
            libgbm \
            alsa-lib \
            at-spi2-core \
            atk \
            at-spi2-atk \
            cairo \
            gdk-pixbuf \
            glib \
            gtk+3.0 \
            pango \
            cups-libs \
            libjpeg-turbo \
            libpng \
            zlib \
            expat \
            nspr \
            icu-libs \
            || warn "Certaines libs X11 manquantes (non bloquant)"

        # --- Outils de build (pour pip si compilation depuis source nécessaire) ---
        apk add --no-cache \
            build-base \
            gcc \
            g++ \
            python3-dev \
            musl-dev \
            libffi-dev \
            openssl-dev \
            || true

        ok "Dépendances Alpine installées"

    elif [ "$HAS_PACKAGE_MANAGER" = "apt" ]; then
        # ═══ DEBIAN/UBUNTU (glibc) ═══
        apt-get update -qq
        apt-get install -y -qq \
            libnss3 \
            libatk1.0-0 \
            libatk-bridge2.0-0 \
            libcups2 \
            libdrm2 \
            libxkbcommon0 \
            libxcomposite1 \
            libxdamage1 \
            libxrandr2 \
            libgbm1 \
            libpango-1.0-0 \
            libcairo2 \
            libasound2 \
            libatspi2.0-0 \
            libxshmfence1 \
            libstdc++6 \
            fonts-noto-cjk \
            fonts-noto-color-emoji \
            || true
        ok "Dépendances Debian installées"

    elif [ "$HAS_PACKAGE_MANAGER" = "dnf" ]; then
        # ═══ FEDORA/CENTOS (glibc) ═══
        dnf install -y \
            nss \
            atk \
            at-spi2-atk \
            cups-libs \
            libdrm \
            libXcomposite \
            libXdamage \
            libXrandr \
            mesa-libgbm \
            pango \
            cairo \
            alsa-lib \
            libxkbcommon \
            libXtst \
            || true
        ok "Dépendances Fedora installées"
    fi
}

# ── 2. Vérifier la couverture glibc ────────────────────────────────────────────
verify_glibc() {
    log "Vérification de la couverture glibc..."

    local MISSING=0

    # Symboles glibc critiques que patchright/Chromium cherchent
    local SYMBOLS=(
        "glibc-2.17"
        "glibc-2.18"
        "glibc-2.28"
        "glibc-2.31"
        "glibc-2.34"
        "GLIBC_2.17"
        "GLIBC_2.28"
    )

    if [ "$LIBC_TYPE" = "glibc" ]; then
        ok "glibc natif détecté — aucune couche de compat nécessaire"
        return 0
    fi

    if [ "$LIBC_TYPE" = "musl" ]; then
        # Vérifier que gcompat est installé
        if ldconfig -p 2>/dev/null | grep -q "ld-linux"; then
            ok "gcompat installé (ld-linux-x86-64.so.2 disponible)"
        else
            warn "gcompat probablement pas installé correctement"
            MISSING=1
        fi

        # Vérifier les libs Chromium critiques
        local CRITICAL_LIBS=("libnss3.so" "libatk-1.0.so" "libglib-2.0.so" "libdrm.so" "libgbm.so" "libX11.so")
        for lib in "${CRITICAL_LIBS[@]}"; do
            if ldconfig -p 2>/dev/null | grep -q "$lib"; then
                ok "$lib trouvé"
            else
                warn "$lib NON trouvé — Chromium pourrait crash"
                MISSING=1
            fi
        done
    fi

    return $MISSING
}

# ── 3. Installer Python + Node.js (si absents) ────────────────────────────────
install_runtimes() {
    log "Vérification de Python et Node.js..."

    if [ "$HAS_PACKAGE_MANAGER" = "apk" ]; then
        apk add --no-cache python3 py3-pip python3-dev nodejs npm || true
    elif [ "$HAS_PACKAGE_MANAGER" = "apt" ]; then
        apt-get install -y -qq python3 python3-pip python3-venv nodejs npm || true
    fi

    # Vérifier Python 3.10+
    if python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
        ok "Python $(python3 --version 2>&1 | awk '{print $2}')"
    else
        warn "Python < 3.10 — certaines dépendances pourraient échouer"
    fi

    # Vérifier Node.js 18+
    if command -v node >/dev/null 2>&1; then
        NODE_VER=$(node --version 2>/dev/null | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VER" -ge 18 ] 2>/dev/null; then
            ok "Node.js $(node --version)"
        else
            warn "Node.js $(node --version) — le dashboard Next.js nécessite v18+"
            warn "Installe Node 20 : curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"
        fi
    else
        warn "Node.js non trouvé — dashboard non installable"
    fi
}

# ── 4. Installer Chromium via patchright ───────────────────────────────────────
install_chromium() {
    log "Installation de Chromium via patchright..."

    # Activer le venv si présent
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

    if [ -d "$PROJECT_DIR/.venv" ]; then
        source "$PROJECT_DIR/.venv/bin/activate"
        ok "venv activé"
    fi

    # Installer patchright
    if python3 -c "import patchright; print(patchright.__version__)" 2>/dev/null; then
        ok "patchright déjà installé"
    else
        log "Installation de patchright..."
        pip install patchright --index-url https://pypi.org/simple/ 2>/dev/null || {
            warn "patchright PyPI échoué — tentative depuis GitHub..."
            pip install "patchright @ git+https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python.git" --no-cache-dir 2>/dev/null || {
                fail "patchright impossible à installer sur cette plateforme"
                fail "Le mode HTTP sera utilisé à la place (pas de navigateur)"
                return 1
            }
        }
        ok "patchright installé"
    fi

    # Installer Chromium
    log "Téléchargement de Chromium (~150MB)..."
    patchright install chromium 2>/dev/null || python3 -m patchright install chromium 2>/dev/null || {
        warn "Chromium binaire impossible à installer"
        warn "Le serveur démarrera en mode DEGRADED (pas de navigateur)"
        return 1
    }

    ok "Chromium installé"
    return 0
}

# ── 5. Test rapide ─────────────────────────────────────────────────────────────
quick_test() {
    log "Test rapide — vérification que Chromium démarre..."

    python3 -c "
import asyncio
import sys

async def test():
    try:
        from patchright.async_api import async_playwright
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('data:text/html,<h1>OK</h1>')
        title = await page.evaluate('document.querySelector(\"h1\").textContent')
        await browser.close()
        await pw.stop()
        assert title == 'OK', f'Unexpected title: {title}'
        return True
    except Exception as e:
        print(f'  Error: {e}', file=sys.stderr)
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
" 2>&1 && ok "Chromium démarre correctement !" || {
        warn "Chromium ne démarre pas — vérifie les logs ci-dessus"
        warn "Le serveur fonctionnera en mode HTTP (sans navigateur)"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🐼 Panda AI — Setup glibc + Chromium                      ║"
echo "║  Détecte musl → installe glibc layer complet + deps        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

install_system_deps
verify_glibc || true
install_runtimes
install_chromium || true
quick_test || true

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup terminé                                          ║"
echo "║                                                            ║"
echo "║  Prochaine étape :                                         ║"
echo "║    cd ~/Panda-Ai && bash start-panda.sh                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
