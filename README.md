<p align="center">
  <a href="https://github.com/ferelking242/panda-ai">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:0f172a,100:1e1b4b&height=220&section=header&text=%F0%9F%90%BC%20PANDA%20AI%20GATEWAY&fontSize=40&fontColor=00d4ff&fontAlignY=35&desc=Browser-based%20OpenAI-compatible%20proxy%20for%208%20AI%20providers&descSize=14&descAlignY=55&descAlign=50&animation=fadeIn" width="100%" alt="Panda AI Banner"/>
  </a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=00D4FF&center=true&vCenter=true&width=435&lines=Turn+any+AI+account+into+an+API;No+API+keys+needed;Just+your+browser+login;8+providers+supported" alt="Typing SVG" />
</p>

<p align="center">
  <a href="#-quick-start"><img src="https://img.shields.io/badge/QUICK_START-▶-00d4ff?style=for-the-badge&logo=github&logoColor=white" alt="Quick Start"/></a>
  <a href="#-providers"><img src="https://img.shields.io/badge/PROVIDERS-8-7b2ff7?style=for-the-badge&logo=openai&logoColor=white" alt="Providers"/></a>
  <a href="docs/API.md"><img src="https://img.shields.io/badge/API_DOCS-📖-22c55e?style=for-the-badge" alt="API Docs"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-orange?style=for-the-badge" alt="License"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Patchright-333?style=flat-square" alt="Patchright"/>
  <img src="https://img.shields.io/badge/OpenAI-Compatible-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI Compatible"/>
  <img src="https://img.shields.io/github/stars/ferelking242/panda-ai?style=flat-square&color=ffd700" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/ferelking242/panda-ai?style=flat-square" alt="Forks"/>
</p>

<br/>

---

## 🐼 What is this?

You already pay for ChatGPT Plus, Claude Pro, or use free tiers of Gemini, DeepSeek, Grok, Mistral, Qwen, or Kimi. But the **official APIs cost extra** and the free tiers are limited.

**Panda AI Gateway** turns your existing browser sessions into fully functional **OpenAI-compatible API servers**. It runs real browsers in the background, automates the web UIs, and exposes everything through standard API endpoints.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="pnd_yourtoken")

response = client.chat.completions.create(
    model="gemini-browser",  # or claude-browser, catgpt-browser, etc.
    messages=[{"role": "user", "content": "Hello from my own API!"}]
)
print(response.choices[0].message.content)
```

> **That's it.** Your AI subscription just became an API.

<br/>

## ✨ Features

<table>
<tr>
<td>

**Core**
- ✅ Chat completions
- ✅ Multi-turn conversations
- ✅ Tool / function calling
- ✅ Image input (vision)
- ✅ File attachments (PDF, DOCX)
- ✅ Responses API (Codex CLI)
- ✅ Provider fallback chain
- ✅ Browser pool (parallel)

</td>
<td>

**Providers**
- 🟢 ChatGPT (DALL-E)
- 🟣 Claude
- 🔵 Gemini
- 🔷 DeepSeek
- ⚫ Grok
- 🟠 Mistral
- 🟤 Qwen
- 🔴 Kimi

</td>
<td>

**Platform**
- 🐳 Docker deployment
- 📱 Android (WebView)
- 🖥️ Linux / Windows / Mac
- 🔐 `pnd_` token auth
- 📊 Dashboard API
- 📝 Auto conversation titles
- ⚡ Stealth anti-detection
- 🔄 Auto session recovery

</td>
</tr>
</table>

<br/>

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai

cp .env.example .env
# Edit .env → set PROVIDER=gemini (or any provider)

docker compose up --build -d

# Log in once via noVNC
open http://localhost:6080/vnc.html

# Verify
curl -H "Authorization: Bearer pnd_yourtoken" http://localhost:8000/v1/models
```

### Option 2: Local

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
patchright install chromium

cp .env.example .env
python scripts/first_login.py    # One-time login
python -m src.api.server         # Start API
```

### Option 3: Android

```bash
cd android/
./gradlew assembleRelease
# APK in app/build/outputs/apk/
```

> 📖 Full guide: [docs/SETUP.md](docs/SETUP.md)

<br/>

## 🔌 Providers

Set `PROVIDER` in your `.env` to switch. **8 providers** supported:

<table>
<tr><th>Provider</th><th><code>PROVIDER=</code></th><th>Model ID</th><th>URL</th><th>Features</th></tr>
<tr><td>🟢 ChatGPT</td><td><code>chatgpt</code></td><td><code>catgpt-browser</code></td><td>chatgpt.com</td><td>DALL-E, Projects</td></tr>
<tr><td>🟣 Claude</td><td><code>claude</code></td><td><code>claude-browser</code></td><td>claude.ai</td><td>Artifacts, Projects</td></tr>
<tr><td>🔵 Gemini</td><td><code>gemini</code></td><td><code>gemini-2.0-flash</code></td><td>aistudio.google.com</td><td>Canvas, Gems</td></tr>
<tr><td>🔷 DeepSeek</td><td><code>deepseek</code></td><td><code>deepseek-r1</code></td><td>chat.deepseek.com</td><td>Deep Think</td></tr>
<tr><td>⚫ Grok</td><td><code>grok</code></td><td><code>grok-3</code></td><td>grok.com</td><td>Real-time X data</td></tr>
<tr><td>🟠 Mistral</td><td><code>mistral</code></td><td><code>mistral-large</code></td><td>chat.mistral.ai</td><td>Codestral</td></tr>
<tr><td>🟤 Qwen</td><td><code>qwen</code></td><td><code>qwen-max</code></td><td>chat.qwen.ai</td><td>Long context</td></tr>
<tr><td>🔴 Kimi</td><td><code>kimi</code></td><td><code>kimi-k2</code></td><td>kimi.moonshot.cn</td><td>128k context</td></tr>
</table>

### 🔄 Fallback Chain

If your primary provider goes down, Panda AI automatically falls back:

```bash
PROVIDER=gemini
PROVIDER_CHAIN=gemini,claude,chatgpt
```

<br/>

## 📦 Build & Deploy

<table>
<tr><th>Target</th><th>Command</th><th>Output</th></tr>
<tr><td>🐳 Docker</td><td><code>docker compose up --build -d</code></td><td>Container on port 8000</td></tr>
<tr><td>🐧 Linux</td><td><code>python -m PyInstaller panda-ai.spec</code></td><td><code>dist/panda-ai</code></td></tr>
<tr><td>🪟 Windows</td><td><code>python -m PyInstaller panda-ai.spec</code></td><td><code>dist/panda-ai.exe</code></td></tr>
<tr><td>🍎 macOS</td><td><code>python -m PyInstaller panda-ai.spec</code></td><td><code>dist/panda-ai</code></td></tr>
<tr><td>📱 Android</td><td><code>cd android && ./gradlew assembleRelease</code></td><td><code>app.apk</code></td></tr>
<tr><td>🌐 PWA</td><td>Deploy <code>dashboard/</code> to Vercel/Netlify</td><td>Web dashboard</td></tr>
</table>

```bash
# Quick Docker
docker compose up --build -d

# Binary build (all platforms)
pip install pyinstaller
python -m PyInstaller panda-ai.spec --clean

# Android
cd android && ./gradlew assembleRelease
```

<br/>

## 🔑 API Authentication

Tokens use the clean `pnd_` format:

```
Authorization: Bearer pnd_7Kx9mQ2vL8rT4nY6cW1zP5aH3bN8
```

### Generate via Dashboard API

```bash
# Create a token with name, expiry, and request limit
curl -X POST http://localhost:8000/api/dashboard/token/generate \
  -H "Authorization: Bearer pnd_yourmasterkey" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "scope": ["chat", "models"],
    "expires_in_seconds": 86400,
    "max_requests": 1000
  }'
```

<br/>

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Your Application                     │
│    (OpenAI SDK / LangChain / curl / Codex CLI)   │
└──────────────────────┬──────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────┐
│           Panda AI Gateway (FastAPI)              │
│               localhost:8000                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Token    │ │ Auth     │ │ Dashboard API    │  │
│  │ Store    │ │ Middleware│ │ (stats/config)   │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│          Browser Pool (Patchright + Stealth)      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ChatGPT │ │ Claude │ │ Gemini │ │  ...   │    │
│  │browser │ │browser │ │browser │ │8 total │    │
│  └────────┘ └────────┘ └────────┘ └────────┘    │
└─────────────────────────────────────────────────┘
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

## ⚠️ Known Limitations

| Limitation | Details |
|---|---|
| No streaming | Responses returned all at once (browser round-trip) |
| Single concurrency per browser | Use `POOL_SIZE` for parallelism |
| Response time | 5-30s per request (real browser) |
| Session expiry | Re-login via noVNC after days/weeks |
| Google OAuth blocked | Use email+password, Microsoft, or Apple |

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
│   ├── api/                # FastAPI routes (OpenAI + dashboard)
│   ├── browser/            # Browser automation (stealth, pool)
│   ├── chatgpt/            # ChatGPT provider
│   ├── claude/             # Claude provider
│   ├── gemini/             # Gemini provider
│   ├── deepseek/           # DeepSeek provider
│   ├── grok/               # Grok provider
│   ├── mistral/            # Mistral provider
│   ├── qwen/               # Qwen provider
│   ├── kimi/               # Kimi provider
│   ├── tokens.py           # pnd_ token management
│   └── config.py           # Centralized configuration
├── android/                # Android WebView wrapper
├── dashboard/              # Next.js admin dashboard
├── scripts/                # Test scripts + utilities
├── docker/                 # Docker support files
├── docs/                   # Documentation
├── tests/                  # Unit tests
└── docker-compose.yml
```

<br/>

---

<p align="center">
  <a href="https://github.com/ferelking242/panda-ai">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:0f172a,100:1e1b4b&height=100&section=footer" width="100%" alt="Footer"/>
  </a>
</p>

<p align="center">
  <sub>Made with 🐼 by <a href="https://github.com/ferelking242">FerelKing</a></sub>
</p>
