#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Panda AI — Android Backend Setup (Termux)                  ║
# ║  Run the full gateway server on your Android phone          ║
# ╚══════════════════════════════════════════════════════════════╝
#
# Prerequisites:
#   1. Install Termux from F-Droid (NOT Play Store — outdated)
#   2. Open Termux and run this script
#
# Usage:
#   pkg install git
#   git clone https://github.com/ferelking242/panda-ai.git
#   cd panda-ai/android
#   bash setup-termux.sh

set -e

echo "🐼 Panda AI — Android Backend Setup"
echo "===================================="
echo ""

# ── Step 1: System dependencies ────────────────────────────────
echo "📦 Installing system dependencies..."
pkg update -y
pkg install -y python nodejs git curl

# ── Step 2: Python dependencies ────────────────────────────────
echo ""
echo "🐍 Setting up Python environment..."
cd ..
python -m venv .venv
source .venv/bin/activate

echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# ── Step 3: Patchright (Chromium for Android) ──────────────────
echo ""
echo "🌐 Installing Chromium browser..."
patchright install chromium
patchright install-deps chromium || echo "⚠️  Some deps may need manual install"

# ── Step 4: Config ─────────────────────────────────────────────
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from template"
    echo "    Edit it with: nano .env"
    echo "    Set PROVIDER=gemini (or your preferred provider)"
fi

# ── Step 5: Create start script ────────────────────────────────
cat > start-panda.sh << 'STARTEOF'
#!/bin/bash
# Start Panda AI Gateway on Android
cd "$(dirname "$0")"
source .venv/bin/activate

echo "🐼 Starting Panda AI Gateway..."
echo "📱 Dashboard: http://localhost:8000/client"
echo "🔌 API: http://localhost:8000/v1"
echo ""

# Run with headless=true for Android (no display)
export HEADLESS=true
export BROWSER_MODE=launch

python -m src.api.server
STARTEOF
chmod +x start-panda.sh

# ── Step 6: Create systemd-like service ────────────────────────
cat > start-service.sh << 'SERVICEEOF'
#!/bin/bash
# Run Panda AI as a background service on Android
cd "$(dirname "$0")"
source .venv/bin/activate

export HEADLESS=true
export BROWSER_MODE=launch
export API_PORT=8000

echo "🐼 Panda AI Gateway starting in background..."
echo "📱 Dashboard: http://localhost:8000/client"

nohup python -m src.api.server > panda.log 2>&1 &
echo $! > panda.pid
echo "PID: $(cat panda.pid)"
echo "Logs: tail -f panda.log"
SERVICEEOF
chmod +x start-service.sh

cat > stop-service.sh << 'STOPEOF'
#!/bin/bash
# Stop Panda AI background service
if [ -f panda.pid ]; then
    kill $(cat panda.pid) 2>/dev/null
    rm panda.pid
    echo "🐼 Panda AI stopped"
else
    echo "Not running"
fi
STOPEOF
chmod +x stop-service.sh

# ── Done ───────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "✅ Setup complete!"
echo ""
echo "To start the gateway:"
echo "  cd panda-ai"
echo "  bash start-panda.sh"
echo ""
echo "Or run as background service:"
echo "  bash start-service.sh"
echo "  bash stop-service.sh"
echo ""
echo "📱 Then open the Panda AI Android app"
echo "   and point it to http://localhost:8000"
echo "========================================="
