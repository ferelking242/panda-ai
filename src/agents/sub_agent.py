"""
Sub-agent system — lightweight parallel AI agents.

Instead of launching N full browser contexts (expensive: ~400MB each),
we use a SINGLE browser context with N pages. Each page navigates to
a different provider or runs a different task concurrently.

This cuts memory usage by ~80% compared to the full pool approach.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import AsyncGenerator

from patchright.async_api import BrowserContext, Page

from src.config import Config
from src.log import setup_logging

log = setup_logging("sub_agent")


@dataclass
class AgentTask:
    """A task to be executed by a sub-agent."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    provider: str = ""
    model: str = ""
    message: str = ""
    system_prompt: str = ""
    status: str = "pending"  # pending, running, completed, failed
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0


@dataclass
class SubAgent:
    """
    A lightweight agent that uses a single browser page.

    Multiple SubAgents can share one BrowserContext — each gets its own
    Page (tab). This is ~5x cheaper than separate BrowserManager instances.
    """
    id: str
    page: Page
    provider: str
    model: str = ""
    task: AgentTask | None = None
    active: bool = False

    async def execute(self, task: AgentTask) -> str:
        """Execute a task using this agent's page."""
        self.task = task
        self.active = True
        task.status = "running"

        try:
            # Import the appropriate client
            client = self._make_client()
            if client is None:
                raise RuntimeError(f"No client for provider: {task.provider}")

            # Select model if specified
            if task.model:
                await client.select_model(task.model)

            # Send message and get response
            result = await client.send_message(task.message)

            task.status = "completed"
            task.result = result.message
            task.completed_at = time.time()
            self.active = False

            log.info(
                f"Agent {self.id} completed task {task.id} "
                f"({task.completed_at - task.created_at:.1f}s)"
            )
            return result.message

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()
            self.active = False
            log.error(f"Agent {self.id} failed: {e}")
            raise

    def _make_client(self):
        """Create the appropriate provider client for this agent's page."""
        provider = self.provider or Config.PROVIDER

        if provider == "chatgpt":
            from src.chatgpt.client import ChatGPTClient
            return ChatGPTClient(self.page)
        elif provider == "claude":
            from src.claude.client import ClaudeClient
            return ClaudeClient(self.page)
        elif provider == "gemini":
            from src.gemini.client import GeminiClient
            return GeminiClient(self.page)
        elif provider == "deepseek":
            from src.deepseek.client import DeepSeekClient
            return DeepSeekClient(self.page)
        elif provider == "grok":
            from src.grok.client import GrokClient
            return GrokClient(self.page)
        elif provider == "mistral":
            from src.mistral.client import MistralClient
            return MistralClient(self.page)
        elif provider == "qwen":
            from src.qwen.client import QwenClient
            return QwenClient(self.page)
        elif provider == "kimi":
            from src.kimi.client import KimiClient
            return KimiClient(self.page)
        return None

    async def close(self):
        """Close this agent's page (frees one tab)."""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
        except Exception:
            pass
        self.active = False


class SubAgentManager:
    """
    Manages a pool of SubAgents within a single BrowserContext.

    Much lighter than BrowserPool (which creates full BrowserManager instances).
    Memory: ~20MB per agent (page) vs ~400MB per full browser context.
    """

    def __init__(self, context: BrowserContext, max_agents: int = 5) -> None:
        self._context = context
        self._max_agents = max_agents
        self._agents: dict[str, SubAgent] = {}
        self._queue: asyncio.Queue[SubAgent] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self, providers: list[str] | None = None) -> None:
        """
        Create initial agent pages.

        Args:
            providers: List of provider names (e.g. ["chatgpt", "claude"]).
                      If None, creates agents for the configured provider.
        """
        if self._initialized:
            return

        providers = providers or [Config.PROVIDER]
        log.info(f"SubAgentManager initializing with {len(providers)} providers")

        for provider in providers:
            if len(self._agents) >= self._max_agents:
                break
            agent = await self._create_agent(provider)
            if agent:
                await self._queue.put(agent)

        self._initialized = True
        log.info(f"SubAgentManager ready — {len(self._agents)} agents, {self._queue.qsize()} available")

    async def _create_agent(self, provider: str) -> SubAgent | None:
        """Create a new agent with its own page in the shared context."""
        try:
            page = await self._context.new_page()

            # Navigate to the provider's URL
            url_map = {
                "chatgpt": Config.CHATGPT_URL,
                "claude": Config.CLAUDE_URL,
                "gemini": Config.GEMINI_URL,
                "deepseek": Config.DEEPSEEK_URL,
                "grok": Config.GROK_URL,
                "mistral": Config.MISTRAL_URL,
                "qwen": Config.QWEN_URL,
                "kimi": Config.KIMI_URL,
            }
            url = url_map.get(provider, Config.CHATGPT_URL)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                log.warning(f"Agent page navigation to {provider} failed: {e}")

            agent_id = f"{provider}_{uuid.uuid4().hex[:6]}"
            agent = SubAgent(id=agent_id, page=page, provider=provider)
            self._agents[agent_id] = agent

            log.info(f"Created agent {agent_id} (provider={provider})")
            return agent

        except Exception as e:
            log.error(f"Failed to create agent for {provider}: {e}")
            return None

    async def acquire(self, provider: str | None = None) -> SubAgent:
        """
        Acquire an available agent. Waits if all agents are busy.
        Optionally filters by provider.
        """
        if provider:
            # Try to get an agent with the right provider
            async with self._lock:
                for agent in self._agents.values():
                    if agent.provider == provider and not agent.active:
                        agent.active = True
                        return agent

        # Wait for any available agent
        agent = await self._queue.get()
        agent.active = True
        return agent

    async def release(self, agent: SubAgent) -> None:
        """Release an agent back to the available pool."""
        agent.active = False
        agent.task = None
        await self._queue.put(agent)

    async def execute_task(self, task: AgentTask) -> str:
        """Execute a task using an available agent."""
        agent = await self.acquire(task.provider or None)
        try:
            result = await agent.execute(task)
            return result
        finally:
            await self.release(agent)

    async def execute_parallel(self, tasks: list[AgentTask]) -> list[AgentTask]:
        """
        Execute multiple tasks in parallel, each on its own agent.
        Returns the list of tasks with results.
        """
        if not tasks:
            return []

        # Ensure we have enough agents
        while self._queue.qsize() < len(tasks) and len(self._agents) < self._max_agents:
            provider = tasks[len(self._agents) % len(tasks)].provider or Config.PROVIDER
            agent = await self._create_agent(provider)
            if agent:
                await self._queue.put(agent)

        # Execute all tasks concurrently
        async def _run(task: AgentTask):
            agent = await self.acquire(task.provider or None)
            try:
                await agent.execute(task)
            except Exception:
                pass
            finally:
                await self.release(agent)

        await asyncio.gather(*[_run(t) for t in tasks], return_exceptions=True)
        return tasks

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    @property
    def available_count(self) -> int:
        return self._queue.qsize()

    def list_agents(self) -> list[dict]:
        """Return status of all agents."""
        return [
            {
                "id": a.id,
                "provider": a.provider,
                "active": a.active,
                "task_id": a.task.id if a.task else None,
                "task_status": a.task.status if a.task else None,
            }
            for a in self._agents.values()
        ]

    async def close(self) -> None:
        """Close all agent pages."""
        for agent in self._agents.values():
            await agent.close()
        self._agents.clear()
        log.info("SubAgentManager closed")


# ── Global instance ───────────────────────────────────────────

_manager: SubAgentManager | None = None


def get_agent_manager() -> SubAgentManager | None:
    return _manager


async def init_agent_manager(
    context: BrowserContext, max_agents: int = 5, providers: list[str] | None = None
) -> SubAgentManager:
    """Create and initialize the global SubAgentManager."""
    global _manager
    _manager = SubAgentManager(context, max_agents=max_agents)
    await _manager.initialize(providers=providers)
    return _manager


async def close_agent_manager() -> None:
    """Close the global SubAgentManager."""
    global _manager
    if _manager:
        await _manager.close()
        _manager = None
