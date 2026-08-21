<p align="center">
  <a href="https://github.com/ferelking242/panda-ai">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:0f172a,100:1e1b4b&height=220&section=header&text=%F0%9F%90%BC%20PANDA%20AI%20GATEWAY&fontSize=40&fontColor=00d4ff&fontAlignY=35&desc=Browser-based%20OpenAI-compatible%20proxy%20for%208%20AI%20providers&descSize=14&descAlignY=55&descAlign=50&animation=fadeIn" width="100%"/>
  </a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=00D4FF&center=true&vCenter=true&width=435&lines=Turn+any+AI+account+into+an+API;No+API+keys+needed;Just+your+browser+login;8+providers+supported" alt="Typing SVG" />
</p>

<p align="center">
  <a href="#-installation"><img src="https://img.shields.io/badge/INSTALL-📦-00d4ff?style=for-the-badge" alt="Install"/></a>
  <a href="#-providers"><img src="https://img.shields.io/badge/PROVIDERS-8-7b2ff7?style=for-the-badge" alt="Providers"/></a>
  <a href="docs/API.md"><img src="https://img.shields.io/badge/API_DOCS-📖-22c55e?style=for-the-badge" alt="API"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-orange?style=for-the-badge" alt="License"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/OpenAI-Compatible-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI"/>
  <img src="https://img.shields.io/github/workflow/status/ferelking242/panda-ai/CI?style=flat-square&label=CI" alt="CI"/>
  <img src="https://img.shields.io/github/stars/ferelking242/panda-ai?style=flat-square&color=ffd700" alt="Stars"/>
</p>

<br/>

## 🐼 What is this?

You already pay for ChatGPT Plus, Claude Pro, or use free tiers of Gemini, DeepSeek, Grok, Mistral, Qwen, or Kimi. But the **official APIs cost extra**.

**Panda AI Gateway** turns your existing browser sessions into fully functional **OpenAI-compatible API servers**. It runs real browsers in the background, automates the web UIs, and exposes everything through standard API endpoints.

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="pnd_yourtoken")
response = client.chat.completions.create(
    model="gemini-browser",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

<br/>

## 📦 Installation

### 🐳 Docker (Recommended)

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai
cp .env.example .env       # Edit: set PROVIDER, API_TOKEN
docker compose up --build -d

# Login once via noVNC browser
open http://localhost:6080/vnc.html
# Sign in with email + password (Google OAuth blocked)

# Verify
curl -H "Authorization: Bearer pnd_yourtoken" http://localhost:8000/v1/models
```

### 🐍 Local Install (Linux / macOS / Windows)

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Chromium browser
patchright install chromium

# Configure
cp .env.example .env
# Edit .env → set PROVIDER, API_TOKEN

# First login (one-time — browser window opens)
python scripts/first_login.py

# Start the gateway
python -m src.api.server
# API live at http://localhost:8000
```

### 📦 Binary Download (No Python required)

Download a pre-built binary for your OS from [GitHub Releases](https://github.com/ferelking242/panda-ai/releases):

| Platform | File | How to run |
|----------|------|-----------|
| Linux x64 | `panda-ai-linux-x64.tar.gz` | `tar xzf panda-ai-*.tar.gz && ./panda-ai` |
| macOS x64/ARM | `panda-ai-macos-x64.tar.gz` | `tar xzf panda-ai-*.tar.gz && ./panda-ai` |
| Windows | `panda-ai-windows-x64.zip` | Extract → double-click `panda-ai.exe` |

```bash
# Linux example
tar xzf panda-ai-linux-x64.tar.gz
cp .env.example .env   # Edit it
./panda-ai
```

### 🏗️ Build Binary From Source

```bash
pip install pyinstaller
python -m PyInstaller panda-ai.spec --clean
# Output: dist/panda-ai (Linux/macOS) or dist/panda-ai.exe (Windows)
```

### 🖥️ VPS / Cloud Server (Headless)

```bash
# SSH into your VPS
ssh root@your-server-ip

# Install Python + deps
apt update && apt install -y python3 python3-pip python3-venv git
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
patchright install chromium

# Configure for headless
cp .env.example .env
cat > .env << 'EOF'
PROVIDER=gemini
API_TOKEN=pnd_yourtoken
API_PORT=8000
HEADLESS=true
BROWSER_MODE=launch
EOF

# Login (one-time — needs a display, use VNC or X forwarding)
python scripts/first_login.py

# Start (use tmux/screen for persistence)
tmux new -s panda
python -m src.api.server
# Ctrl+B D to detach

# Open firewall
ufw allow 8000

# Access from anywhere: http://your-server-ip:8000/v1
```

### 📱 Android (Termux — Full Backend on Phone)

Run the **entire gateway natively on Android** via Termux:

```bash
# 1. Install Termux from F-Droid (NOT Play Store)
#    https://f-droid.org/packages/com.termux/

# 2. Setup
pkg install git
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai
bash android/setup-termux.sh

# 3. Start
bash start-panda.sh

# 4. Open the Panda AI Android app → auto-detects localhost:8000
```

### 📱 Android (APK — Remote Gateway Only)

If you just want the app to connect to a remote gateway:

```bash
cd android/
./gradlew assembleRelease
adb install app/build/outputs/apk/release/app-release-unsigned.apk
```

Or download the APK from [Releases](https://github.com/ferelking242/panda-ai/releases).

<br/>

## 🔑 API Authentication

Tokens use the clean `pnd_` format: `pnd_7Kx9mQ2vL8rT4nY6cW1zP5aH3bN8`

```bash
# Set in .env
API_TOKEN=pnd_yourtoken

# Use in requests
curl -H "Authorization: Bearer pnd_yourtoken" http://localhost:8000/v1/models
```

### Generate tokens with metadata

```bash
curl -X POST http://localhost:8000/api/dashboard/token/generate \
  -H "Authorization: Bearer pnd_masterkey" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "expires_in_seconds": 86400, "max_requests": 1000}'
```

<br/>

## 🔌 Providers

Set `PROVIDER` in your `.env`:

| Provider | `PROVIDER=` | Model | URL |
|---|---|---|---|
| 🟢 ChatGPT | `chatgpt` | `catgpt-browser` | chatgpt.com |
| 🟣 Claude | `claude` | `claude-browser` | claude.ai |
| 🔵 Gemini | `gemini` | `gemini-2.0-flash` | aistudio.google.com |
| 🔷 DeepSeek | `deepseek` | `deepseek-r1` | chat.deepseek.com |
| ⚫ Grok | `grok` | `grok-3` | grok.com |
| 🟠 Mistral | `mistral` | `mistral-large` | chat.mistral.ai |
| 🟤 Qwen | `qwen` | `qwen-max` | chat.qwen.ai |
| 🔴 Kimi | `kimi` | `kimi-k2` | kimi.moonshot.cn |

### Fallback chain

```bash
PROVIDER=gemini
PROVIDER_CHAIN=gemini,claude,chatgpt
```

<br/>

## 📊 Usage Examples

### Python (OpenAI SDK)
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="pnd_xxx")
response = client.chat.completions.create(
    model="claude-browser",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
```

### Python (LangChain + Tools)
```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny, 25C in {city}"

llm = ChatOpenAI(model="gemini-browser", base_url="http://localhost:8000/v1", api_key="pnd_xxx")
llm_with_tools = llm.bind_tools([get_weather])
response = llm_with_tools.invoke("Weather in Tokyo?")
```

### curl
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pnd_xxx" \
  -d '{"model":"gemini-browser","messages":[{"role":"user","content":"Hello!"}]}'
```

<br/>

## 📦 Build Targets

| Target | Command | Output |
|---|---|---|
| 🐳 Docker | `docker compose up --build -d` | Container on :8000 |
| 🐍 Local | `python -m src.api.server` | Server on :8000 |
| 📦 Binary | `python -m PyInstaller panda-ai.spec` | `dist/panda-ai` |
| 🖥️ VPS | `tmux && python -m src.api.server` | Remote server |
| 📱 Android Termux | `bash start-panda.sh` | Phone-native server |
| 📱 Android APK | `./gradlew assembleRelease` | WebView app |

<br/>

## 🧪 Testing

```bash
# Unit tests (no server needed)
python tests/test_integration.py

# Integration tests (requires running server)
python scripts/test_phase1.py
python scripts/test_multi_turn.py
python scripts/test_langchain_tools.py
```

<br/>

## 📂 Project Structure

```
panda-ai/
├── src/                    # Python gateway core
│   ├── api/                # FastAPI (OpenAI + dashboard)
│   ├── browser/            # Browser automation (stealth, pool)
│   ├── chatgpt/claude/gemini/deepseek/grok/mistral/qwen/kimi/
│   ├── tokens.py           # pnd_ token management
│   └── config.py           # Configuration
├── android/                # Android app + Termux scripts
├── dashboard/              # Next.js admin dashboard
├── scripts/                # Test scripts + utilities
├── docker/                 # Docker support files
├── docs/                   # Documentation
├── tests/                  # Unit tests
├── panda-ai.spec           # PyInstaller binary spec
├── Dockerfile              # Docker image
└── docker-compose.yml      # Docker Compose
```

<br/>

## ⚠️ Known Limitations

| Limitation | Details |
|---|---|
| No streaming | Responses returned all at once |
| Single concurrency per browser | Use `POOL_SIZE` for parallelism |
| Response time | 5-30s per request (real browser) |
| Session expiry | Re-login via noVNC |
| Google OAuth blocked | Use email+password, Microsoft, or Apple |

<br/>

---

<p align="center">
  <a href="https://github.com/ferelking242/panda-ai">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:0f172a,100:1e1b4b&height=100&section=footer" width="100%"/>
  </a>
</p>

<p align="center">
  <sub>Made with 🐼 by <a href="https://github.com/ferelking242">FerelKing</a></sub>
</p>
