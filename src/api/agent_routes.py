"""
Agent API routes — profile, sub-agents, ephemeral chats.

Endpoints:
  GET  /api/agent/profile          - Get current user's profile info
  GET  /api/agent/providers        - List all supported providers with status
  GET  /api/agent/models           - List models for all providers
  POST /api/agent/ephemeral        - Start an ephemeral (temporary) chat
  GET  /api/agent/sub-agents       - List active sub-agents
  POST /api/agent/sub-agents       - Create a sub-agent
  POST /api/agent/sub-agents/execute - Execute a task on a sub-agent
  POST /api/agent/sub-agents/parallel - Execute tasks in parallel across agents
  DELETE /api/agent/sub-agents/{id} - Close a sub-agent
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import Config
from src.log import setup_logging
from src.api.dashboard_routes import record_request

log = setup_logging("agent_routes")

agent_router = APIRouter(prefix="/api/agent", tags=["agent"])

# Global references — set by server.py
_client = None
_browser = None


def set_agent_references(client, browser) -> None:
    global _client, _browser
    _client = client
    _browser = browser


_lock = asyncio.Lock()

# ── All providers ─────────────────────────────────────────────

ALL_PROVIDERS = [
    {
        "id": "chatgpt",
        "name": "ChatGPT",
        "url": Config.CHATGPT_URL,
        "models": [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini",
            "o3-mini", "o3", "gpt-4",
        ],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "claude",
        "name": "Claude",
        "url": Config.CLAUDE_URL,
        "models": [
            "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229", "claude-3-haiku-20240307",
        ],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "gemini",
        "name": "Gemini",
        "url": Config.GEMINI_URL,
        "models": [
            "gemini-2.0-flash", "gemini-1.5-pro",
            "gemini-2.0-flash-thinking",
        ],
        "supports_images": True,
        "supports_ephemeral": True,
        "supports_profile": True,
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "url": Config.DEEPSEEK_URL,
        "models": ["deepseek-r1", "deepseek-v3"],
        "supports_images": False,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "grok",
        "name": "Grok",
        "url": Config.GROK_URL,
        "models": ["grok-3", "grok-3-mini", "grok-2"],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "mistral",
        "name": "Mistral",
        "url": Config.MISTRAL_URL,
        "models": [
            "mistral-large", "mistral-small", "mistral-nemo",
            "codestral", "pixtral-large",
        ],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "qwen",
        "name": "Qwen",
        "url": Config.QWEN_URL,
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long", "qwq-32b"],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
    {
        "id": "kimi",
        "name": "Kimi",
        "url": Config.KIMI_URL,
        "models": [
            "kimi-k2", "moonshot-v1-8k", "moonshot-v1-32k",
            "moonshot-v1-128k",
        ],
        "supports_images": True,
        "supports_ephemeral": False,
        "supports_profile": True,
    },
]


# ── Schemas ──────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    name: str = ""
    email: str = ""
    avatar_url: str = ""
    plan: str = ""
    provider: str = ""
    logged_in: bool = False


class ProviderInfo(BaseModel):
    id: str
    name: str
    url: str
    models: list[str]
    supports_images: bool = False
    supports_ephemeral: bool = False
    supports_profile: bool = False
    is_active: bool = False


class EphemeralRequest(BaseModel):
    message: str
    model: str = ""
    provider: str = ""


class SubAgentCreate(BaseModel):
    provider: str = ""
    model: str = ""


class SubAgentTask(BaseModel):
    agent_id: str
    message: str
    model: str = ""


class ParallelTask(BaseModel):
    provider: str
    message: str
    model: str = ""


class ParallelRequest(BaseModel):
    tasks: list[ParallelTask]


# ── Routes ──────────────────────────────────────────────────


@agent_router.get("/profile", response_model=ProfileResponse)
async def get_profile() -> ProfileResponse:
    """Get the current user's profile from the active provider."""
    start = time.time()
    try:
        if _client is None:
            raise HTTPException(status_code=503, detail="Client not initialized")

        from src.profile import get_profile as scrape_profile
        page = _client.page

        profile = await scrape_profile(page, Config.PROVIDER)

        # Check login status
        logged_in = False
        if _browser:
            try:
                logged_in = await _browser.is_logged_in()
            except Exception:
                pass

        result = ProfileResponse(
            name=profile.get("name", ""),
            email=profile.get("email", ""),
            avatar_url=profile.get("avatar_url", ""),
            plan=profile.get("plan", ""),
            provider=Config.PROVIDER,
            logged_in=logged_in,
        )

        elapsed = (time.time() - start) * 1000
        record_request("/api/agent/profile", "ok", elapsed)
        return result

    except HTTPException:
        raise
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_request("/api/agent/profile", "error", elapsed, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List all supported providers with their status."""
    return [
        ProviderInfo(
            id=p["id"],
            name=p["name"],
            url=p["url"],
            models=p["models"],
            supports_images=p["supports_images"],
            supports_ephemeral=p["supports_ephemeral"],
            supports_profile=p["supports_profile"],
            is_active=(p["id"] == Config.PROVIDER),
        )
        for p in ALL_PROVIDERS
    ]


@agent_router.get("/models")
async def list_all_models() -> dict:
    """List models for the active provider only.
    
    Only the currently connected provider's models are returned so clients
    don't try to use models from disconnected providers.
    """
    active = Config.PROVIDER
    active_data = next((p for p in ALL_PROVIDERS if p["id"] == active), None)
    if not active_data:
        return {}
    return {active: active_data["models"]}


@agent_router.get("/models/active")
async def get_active_provider_models() -> dict:
    """Fetch the real model list from the currently active provider."""
    start = time.time()
    provider = Config.PROVIDER
    try:
        if _client is None or _client.page is None:
            raise HTTPException(status_code=503, detail="Client not ready")

        page = _client.page
        models = []

        if provider == "chatgpt":
            # ChatGPT models endpoint (GET /backend-api/models)
            try:
                resp = await page.evaluate("""
                    async () => {
                        const r = await fetch('/backend-api/models?history_and_training_messages=false', {
                            credentials: 'include'
                        });
                        if (!r.ok) return {error: r.status};
                        return await r.json();
                    }
                """)
                if isinstance(resp, dict) and "data" in resp:
                    models = [m.get("slug", m.get("id", "")) for m in resp["data"] if m.get("slug") or m.get("id")]
                elif isinstance(resp, dict) and "error" not in resp:
                    # Try parsing as list
                    if isinstance(resp, list):
                        models = [m.get("slug", m.get("id", "")) for m in resp if m.get("slug") or m.get("id")]
            except Exception as e:
                log.warning(f"Failed to fetch ChatGPT models: {e}")

        elif provider == "claude":
            # Claude models are accessed via the model selector in the UI
            try:
                resp = await page.evaluate("""
                    async () => {
                        const r = await fetch('https://claude.ai/api/models', {
                            credentials: 'include'
                        });
                        if (!r.ok) return {error: r.status};
                        return await r.json();
                    }
                """)
                if isinstance(resp, dict) and "models" in resp:
                    models = [m.get("id", "") for m in resp["models"] if m.get("id")]
                elif isinstance(resp, list):
                    models = [m.get("id", "") for m in resp if m.get("id")]
            except Exception as e:
                log.warning(f"Failed to fetch Claude models: {e}")

        elif provider == "gemini":
            # Gemini models via the chat page model selector
            try:
                resp = await page.evaluate("""
                    async () => {
                        const r = await fetch('/api/models', { credentials: 'include' });
                        if (!r.ok) return {error: r.status};
                        return await r.json();
                    }
                """)
                if isinstance(resp, dict) and "models" in resp:
                    models = [m.get("id", "") for m in resp["models"] if m.get("id")]
            except Exception as e:
                log.warning(f"Failed to fetch Gemini models: {e}")

        # Fallback: use hardcoded if live fetch returned nothing
        if not models:
            provider_data = next((p for p in ALL_PROVIDERS if p["id"] == provider), None)
            if provider_data:
                models = provider_data["models"]

        elapsed = (time.time() - start) * 1000
        record_request("/api/agent/models/active", "ok", elapsed)

        return {
            "provider": provider,
            "models": models,
            "live": len(models) > 0 and provider in ("chatgpt", "claude", "gemini"),
        }

    except HTTPException:
        raise
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_request("/api/agent/models/active", "error", elapsed, error=str(e))
        # Fallback to hardcoded
        provider_data = next((p for p in ALL_PROVIDERS if p["id"] == Config.PROVIDER), None)
        return {
            "provider": Config.PROVIDER,
            "models": provider_data["models"] if provider_data else [],
            "live": False,
        }


@agent_router.post("/ephemeral")
async def start_ephemeral_chat(req: EphemeralRequest) -> dict:
    """
    Start an ephemeral (temporary) chat.

    Ephemeral chats are not saved in the provider's history.
    Currently supported: Gemini (Incognito/Temporary chats).
    For other providers, starts a new chat that can be cleared later.
    """
    start = time.time()
    try:
        if _client is None:
            raise HTTPException(status_code=503, detail="Client not initialized")

        async with _lock:
            # Try ephemeral mode first
            if hasattr(_client, "start_ephemeral_chat"):
                await _client.start_ephemeral_chat()

            # Select model if specified
            if req.model:
                await _client.select_model(req.model)

            # Send the message
            result = await _client.send_message(req.message)

            elapsed = (time.time() - start) * 1000
            record_request("/api/agent/ephemeral", "ok", elapsed)

            return {
                "message": result.message,
                "thread_id": result.thread_id,
                "response_time_ms": result.response_time_ms,
                "ephemeral": True,
                "provider": req.provider or Config.PROVIDER,
            }

    except HTTPException:
        raise
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_request("/api/agent/ephemeral", "error", elapsed, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/sub-agents")
async def list_sub_agents() -> dict:
    """List active sub-agents and their status."""
    from src.agents.sub_agent import get_agent_manager
    manager = get_agent_manager()
    if manager is None:
        return {"agents": [], "total": 0, "available": 0}
    return {
        "agents": manager.list_agents(),
        "total": manager.agent_count,
        "available": manager.available_count,
    }


@agent_router.post("/sub-agents")
async def create_sub_agent(req: SubAgentCreate) -> dict:
    """Create a new sub-agent for a specific provider."""
    from src.agents.sub_agent import get_agent_manager
    manager = get_agent_manager()
    if manager is None:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    provider = req.provider or Config.PROVIDER
    agent = await manager._create_agent(provider)
    if agent is None:
        raise HTTPException(status_code=500, detail=f"Failed to create agent for {provider}")

    await manager._queue.put(agent)
    return {"id": agent.id, "provider": agent.provider, "status": "ready"}


@agent_router.post("/sub-agents/execute")
async def execute_on_agent(req: SubAgentTask) -> dict:
    """Execute a task on a specific sub-agent."""
    from src.agents.sub_agent import AgentTask, get_agent_manager
    manager = get_agent_manager()
    if manager is None:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    # Find the agent
    agent = manager._agents.get(req.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {req.agent_id} not found")

    task = AgentTask(
        provider=agent.provider,
        model=req.model,
        message=req.message,
    )

    try:
        result = await agent.execute(task)
        await manager.release(agent)
        return {
            "task_id": task.id,
            "result": result,
            "status": task.status,
            "elapsed_ms": int((task.completed_at - task.created_at) * 1000),
        }
    except Exception as e:
        await manager.release(agent)
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/sub-agents/parallel")
async def execute_parallel(req: ParallelRequest) -> dict:
    """Execute tasks in parallel across multiple sub-agents."""
    from src.agents.sub_agent import AgentTask, get_agent_manager
    manager = get_agent_manager()
    if manager is None:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    tasks = [
        AgentTask(
            provider=t.provider,
            model=t.model,
            message=t.message,
        )
        for t in req.tasks
    ]

    results = await manager.execute_parallel(tasks)
    return {
        "results": [
            {
                "task_id": t.id,
                "provider": t.provider,
                "result": t.result,
                "status": t.status,
                "error": t.error,
                "elapsed_ms": int((t.completed_at - t.created_at) * 1000) if t.completed_at else 0,
            }
            for t in results
        ]
    }


@agent_router.delete("/sub-agents/{agent_id}")
async def close_sub_agent(agent_id: str) -> dict:
    """Close a sub-agent and free its page."""
    from src.agents.sub_agent import get_agent_manager
    manager = get_agent_manager()
    if manager is None:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = manager._agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await agent.close()
    del manager._agents[agent_id]
    return {"closed": agent_id}
