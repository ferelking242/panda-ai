# 🐼 Panda AI — Android App

Native Android wrapper for Panda AI Gateway.

## What it does

- **Connects** to your Panda AI Gateway (local or remote)
- **Dashboard** — full gateway control from your phone
- **Test Client** — chat with any provider directly
- **API Docs** — browse the OpenAPI spec
- **Backend detection** — auto-detects if gateway is running

## Option 1: Termux (Recommended — runs backend on device)

The full gateway runs **natively on your Android phone** via Termux.

### Setup

```bash
# 1. Install Termux from F-Droid (NOT Play Store)
# https://f-droid.org/packages/com.termux/

# 2. Clone and setup
pkg install git
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai
bash android/setup-termux.sh

# 3. Start the gateway
bash start-panda.sh

# 4. Open the Android app → it auto-detects localhost:8000
```

### What runs on your phone

```
Android Phone
├── Termux (terminal emulator)
│   ├── Python 3.13 + FastAPI
│   ├── Chromium (headless via Patchright)
│   └── Panda AI Gateway on localhost:8000
│
└── Panda AI App (this WebView wrapper)
    └── Loads http://localhost:8000/client
```

## Option 2: Build the APK

If you just want the WebView app (connecting to a remote gateway):

### Prerequisites

- Android Studio (or command-line SDK)
- JDK 17+

### Build

```bash
cd android/

# Using Gradle wrapper
./gradlew assembleRelease

# Or using Android Studio:
# File → Open → android/ → Build → Build APK
```

APK output: `app/build/outputs/apk/release/app-release-unsigned.apk`

### Install on device

```bash
adb install app/build/outputs/apk/release/app-release-unsigned.apk
```

## Option 3: Deploy to VPS + Connect

Run the gateway on a VPS, connect from the Android app remotely:

```bash
# On your VPS (Ubuntu/Debian)
ssh your-vps
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai

# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
patchright install chromium

# Configure
cp .env.example .env
# Edit .env:
#   PROVIDER=gemini
#   API_TOKEN=pnd_yourtoken
#   API_PORT=8000
#   HEADLESS=true

# Start
python -m src.api.server

# Then in the Android app, enter:
# http://your-vps-ip:8000
```

## Architecture

```
┌─────────────────────────┐
│   Panda AI Android App   │
│   (Jetpack Compose)      │
│                          │
│  ┌───────────────────┐   │
│  │    WebView         │   │
│  │  localhost:8000    │───┼──► Gateway API
│  │  /client           │   │    (FastAPI)
│  └───────────────────┘   │
│                          │
│  ┌───────────────────┐   │
│  │  Backend Detection │   │
│  │  (healthz check)   │   │
│  └───────────────────┘   │
└─────────────────────────┘
```
