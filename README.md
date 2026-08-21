<p align="center">
  <img src="assets/catgpt_gatway_logo.jpeg" width="200" alt="Panda AI Gateway Logo" />
</p>

<h1 align="center">🐼 Panda AI Gateway</h1>

<p align="center">
  <strong>Turn any AI chat account into a fully working OpenAI-compatible API.</strong><br/>
  No API keys needed. Just your browser login.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#providers">Providers</a> &bull;
  <a href="docs/API.md">API Docs</a> &bull;
  <a href="docs/SETUP.md">Setup Guide</a> &bull;
  <a href="docs/ARCHITECTURE.md">Architecture</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue?style=flat-square" alt="Python 3.13+" />
  <img src="https://img.shields.io/badge/providers-8-green?style=flat-square" alt="8 Providers" />
  <img src="https://img.shields.io/badge/API-OpenAI_compatible-brightgreen?style=flat-square" alt="OpenAI Compatible" />
  <img src="https://img.shields.io/badge/docker-ready-blue?style=flat-square" alt="Docker" />
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="MIT License" />
</p>

---

## What is this?

You already pay for ChatGPT Plus, Claude Pro, or use free tiers of Gemini, DeepSeek, Grok, Mistral, Qwen, or Kimi. But the official APIs cost extra and the free tiers are limited.

**Panda AI Gateway** turns your existing browser sessions into fully functional OpenAI-compatible API servers. It runs real browsers in the background, automates the web UIs, and exposes everything through standard API endpoints that work with the OpenAI Python SDK, LangChain, and anything that speaks the OpenAI protocol.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy123")

response = client.chat.completions.create(
    model="gemini-browser",  # or claude-browser, catgpt-browser, etc.
    messages=[{"role": "user", "content": "Hello from my own API!"}]
)
print(response.choices[0].message.content)
```

That's it. Your AI subscription just became an API.

---

## Features

| Feature | ChatGPT | Claude | Gemini | DeepSeek | Grok | Mistral | Qwen | Kimi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Chat completions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-turn conversations | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tool / function calling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Image input (vision) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| File attachments (PDF, DOCX) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Image generation (DALL-E) | ✅ | — | — | — | — | — | — | — |
| OpenAI SDK compatible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LangChain compatible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Docker deployment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Provider fallback chain | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Browser pool (parallel) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Responses API (Codex CLI) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Providers

Set `PROVIDER` in your `.env` file to switch. 8 providers supported:

| Provider | `PROVIDER=` | Model ID | URL |
|---|---|---|---|
| **ChatGPT** | `chatgpt` | `catgpt-browser` | chatgpt.com |
| **Claude** | `claude` | `claude-browser` | claude.ai |
| **Gemini** | `gemini` | `gemini-2.0-flash` | aistudio.google.com |
| **DeepSeek** | `deepseek` | `deepseek-r1` | chat.deepseek.com |
| **Grok** | `grok` | `grok-3` | grok.com |
| **Mistral** | `mistral` | `mistral-large` | chat.mistral.ai |
| **Qwen** | `qwen` | `qwen-max` | chat.qwen.ai |
| **Kimi** | `kimi` | `kimi-k2` | kimi.moonshot.cn |

### Provider Fallback Chain

If your primary provider goes down, Panda AI can automatically fall back to another:

```bash
PROVIDER=gemini
PROVIDER_CHAIN=gemini,claude,chatgpt
```

---

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai

cp .env.example .env
# Edit .env → set PROVIDER=gemini (or any provider)

docker compose up --build -d

# Log in once via noVNC
open http://localhost:6080/vnc.html
# Sign in with EMAIL + PASSWORD (Google OAuth is blocked in automated browsers)

# Verify
curl -H "Authorization: Bearer dummy123" http://localhost:8000/v1/models
```

### Option 2: Local

```bash
git clone https://github.com/ferelking242/panda-ai.git
cd panda-ai
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
patchright install chromium

cp .env.example .env
# Edit .env → set PROVIDER

# First login (one-time)
python scripts/first_login.py

# Start
python -m src.api.server
```

> Full guide with Docker internals, Nix flake, systemd, and troubleshooting: [docs/SETUP.md](docs/SETUP.md)

---

## Usage

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy123")

response = client.chat.completions.create(
    model="gemini-browser",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
```

### Python (LangChain)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="claude-browser",
    base_url="http://localhost:8000/v1",
    api_key="dummy123",
)
response = llm.invoke("Best practices for REST API design?")
print(response.content)
```

### curl

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy123" \
  -d '{
    "model": "gemini-browser",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Tool / Function Calling

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Sunny, 25C in {city}"

llm = ChatOpenAI(model="claude-browser", base_url="http://localhost:8000/v1", api_key="dummy123")
llm_with_tools = llm.bind_tools([get_weather])
response = llm_with_tools.invoke("What's the weather in Tokyo?")
print(response.tool_calls)
```

### Responses API (Codex CLI compatible)

```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy123" \
  -d '{
    "model": "gemini-browser",
    "input": "Write a hello world in Python"
  }'
```

> Full API reference: [docs/API.md](docs/API.md)

---

## Configuration

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `PROVIDER` | `chatgpt` | Primary provider |
| `PROVIDER_CHAIN` | — | Fallback chain (comma-separated) |
| `POOL_SIZE` | `1` | Number of parallel browsers |
| `BROWSER_DATA_DIR` | `./browser_data` | Session persistence |
| `API_TOKEN` | `dummy123` | Bearer auth token |
| `API_PORT` | `8000` | Server port |
| `HEADLESS` | `false` | Headless mode |
| `BROWSER_MODE` | `launch` | `launch`, `cdp`, or `android` |
| `CACHE_TTL` | `0` | Response cache (seconds, 0=off) |

> See [.env.example](.env.example) for all settings.

---

## Architecture

```
Your app (OpenAI SDK / LangChain / curl / Codex CLI)
    │
    ▼
Panda AI Gateway (FastAPI on port 8000)
    │
    ├──► Chromium browser pool (Patchright + stealth patches)
    │       │
    │       ├──► chatgpt.com
    │       ├──► claude.ai
    │       ├──► aistudio.google.com
    │       ├──► chat.deepseek.com
    │       ├──► grok.com
    │       ├──► chat.mistral.ai
    │       ├──► chat.qwen.ai
    │       └──► kimi.moonshot.cn
    │
    └──► Dashboard (Next.js on separate port)
```

Real browser sessions with anti-detection (stealth patches, human-like typing, viewport jitter, persistent cookies). Tool calling via prompt engineering. Full Responses API support for Codex CLI.

> Deep dive: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Project Structure

```
panda-ai/
├── src/                    # Python source (gateway core)
│   ├── api/                # FastAPI routes (OpenAI + dashboard)
│   ├── browser/            # Browser automation (manager, stealth, pool)
│   ├── chatgpt/            # ChatGPT provider
│   ├── claude/             # Claude provider
│   ├── gemini/             # Gemini provider
│   ├── deepseek/           # DeepSeek provider
│   ├── grok/               # Grok provider
│   ├── mistral/            # Mistral provider
│   ├── qwen/               # Qwen provider
│   ├── kimi/               # Kimi provider
│   ├── cli/                # Terminal UI
│   ├── media/              # Audio transcription + PDF extraction
│   └── config.py           # Centralized configuration
├── dashboard/              # Next.js admin dashboard (separate)
├── scripts/                # Test scripts + first login
├── docker/                 # Docker support files
├── docs/                   # Documentation
├── extension/              # Browser extension
├── tests/                  # Unit tests
└── docker-compose.yml
```

---

## Testing

```bash
# Unit tests (no server needed)
python tests/test_integration.py

# Integration tests (requires running server)
python scripts/test_phase1.py
python scripts/test_multi_turn.py
python scripts/test_robust.py
python scripts/test_langchain_tools.py
```

---

## Known Limitations

- **No streaming** — Responses returned all at once (browser round-trip)
- **Single concurrency per browser** — Use `POOL_SIZE` for parallelism
- **Response time** — 5-30s per request (real browser)
- **Session expiry** — Re-login via noVNC after days/weeks
- **Google OAuth blocked** — Use email+password, Microsoft, or Apple login

---

## Contributing

Contributions welcome! Fix selectors, add providers, improve detection, write docs.

---

## License

MIT License. See [LICENSE](LICENSE).
