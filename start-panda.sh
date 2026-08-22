#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Panda AI — Quick Start (Termux / Linux / macOS)           ║
# ╚══════════════════════════════════════════════════════════════╝

set -e
cd "$(dirname "$0")"

echo "🐼 Panda AI — Starting Gateway"
echo "================================"
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "📝 No .env found — copying from .env.example"
    cp .env.example .env
    echo "   Edit .env with: nano .env"
    echo ""
fi

# Activate venv if present
if [ -d .venv ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No .venv found — using system Python"
    echo "   Create one with: python3 -m venv .venv && source .venv/bin/activate"
fi

echo ""
echo "🚀 Starting Panda AI Gateway..."
echo "   Dashboard: http://localhost:8000/client"
echo "   API:       http://localhost:8000/v1"
echo "   Docs:      http://localhost:8000/docs"
echo ""

python -m src.api.server
