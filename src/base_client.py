"""
Base client — shared interface and logic for all provider clients.

Every provider (ChatGPT, Claude, Gemini, etc.) inherits from BaseClient
and implements provider-specific selectors and navigation.
"""

from __future__ import annotations

import asyncio
import re
import time
from abc import ABC, abstractmethod

from patchright.async_api import Page

from src.config import Config
from src.browser.human import human_type, human_click, random_delay
from src.log import setup_logging

log = setup_logging("base_client")


class BaseClient(ABC):
    """
    Abstract base for all AI provider clients.

    Provides shared send/receive, thread management, profile scraping,
    model selection, and ephemeral chat support.
    """

    def __init__(self, page: Page) -> None:
        self._page = page
        self._current_model: str = ""
        self._provider_name: str = "unknown"

    @property
    def page(self) -> Page:
        return self._page

    @property
    def provider_name(self) -> str:
        return self._provider_name

    # ── Abstract methods (each provider MUST implement) ─────────

    @abstractmethod
    async def send_message(
        self,
        text: str,
        image_paths: list[str] | None = None,
        file_paths: list[str] | None = None,
    ) -> "ChatResponse":
        """Send a message and wait for the complete response."""
        ...

    @abstractmethod
    async def new_chat(self) -> None:
        """Start a new conversation."""
        ...

    @abstractmethod
    async def navigate_to_thread(self, thread_id: str) -> None:
        """Navigate to an existing conversation."""
        ...

    @abstractmethod
    async def list_threads(self) -> list[dict]:
        """Scrape sidebar for conversation threads."""
        ...

    @abstractmethod
    async def get_conversation_title(self) -> str:
        """Get the current conversation's title."""
        ...

    # ── Profile info (provider-specific scraping) ───────────────

    async def get_profile(self) -> dict:
        """
        Scrape the current user's profile info from the provider's UI.

        Returns dict with keys:
            name: Display name
            email: Email address
            avatar_url: Profile picture URL
            plan: Subscription plan (e.g. "Plus", "Pro", "Free")
            provider: Provider name
        """
        return {
            "name": "",
            "email": "",
            "avatar_url": "",
            "plan": "",
            "provider": self._provider_name,
        }

    # ── Model selection (default: no-op) ────────────────────────

    async def select_model(self, model_id: str) -> bool:
        """Select a model. Returns True if successful."""
        log.debug(f"select_model not implemented for {self._provider_name}")
        return False

    async def get_available_models(self) -> list[str]:
        """Return available models from the UI."""
        return []

    # ── Ephemeral / temporary chat ──────────────────────────────

    async def start_ephemeral_chat(self) -> None:
        """Start an ephemeral (temporary) chat that won't be saved."""
        log.info(f"start_ephemeral_chat: not implemented for {self._provider_name}")
        await self.new_chat()

    # ── Shared helpers ──────────────────────────────────────────

    def _extract_thread_id_from_url(self, url_pattern: str) -> str:
        """Extract thread ID from current URL using the given regex pattern."""
        url = self._page.url
        match = re.search(url_pattern, url)
        return match.group(1) if match else ""

    async def _find_selector(self, selectors: list[str], name: str) -> str | None:
        """Try each selector in the fallback list. Return the first match."""
        for selector in selectors:
            try:
                el = await self._page.wait_for_selector(
                    selector,
                    timeout=Config.SELECTOR_TIMEOUT,
                    state="visible",
                )
                if el:
                    log.debug(f"Found {name} via: {selector}")
                    return selector
            except Exception:
                log.debug(f"Selector miss for {name}: {selector}")
                continue
        log.warning(f"No working selector found for: {name}")
        return None

    async def _click_send(self, send_selectors: list[str]) -> bool:
        """Click the send button using selector fallbacks."""
        selector = await self._find_selector(send_selectors, "send button")
        if selector:
            await human_click(self._page, selector)
            log.debug("Send button clicked")
            return True
        return False

    async def _detect_page_error(self) -> str | None:
        """Check if the current page shows a browser error."""
        try:
            return await self._page.evaluate(
                """
                () => {
                    const body = document.body ? document.body.innerText : '';
                    const title = document.title || '';
                    if (body.includes('DNS_PROBE_FINISHED_NXDOMAIN')) return 'DNS_PROBE_FINISHED_NXDOMAIN';
                    if (body.includes('ERR_NAME_NOT_RESOLVED')) return 'ERR_NAME_NOT_RESOLVED';
                    if (body.includes('ERR_CONNECTION_REFUSED')) return 'ERR_CONNECTION_REFUSED';
                    if (body.includes('ERR_INTERNET_DISCONNECTED')) return 'ERR_INTERNET_DISCONNECTED';
                    if (body.includes('ERR_CONNECTION_TIMED_OUT')) return 'ERR_CONNECTION_TIMED_OUT';
                    if (title.includes("can't be reached") || title.includes("is not available"))
                        return 'page_unreachable';
                    return null;
                }
                """
            )
        except Exception:
            return None

    async def _upload_files(self, file_paths: list[str], selectors: list[str]) -> None:
        """Upload files to the provider's input area."""
        from pathlib import Path

        valid_paths = []
        for p in file_paths:
            path = Path(p)
            if path.exists() and path.is_file():
                valid_paths.append(str(path.resolve()))
            else:
                log.warning(f"File not found, skipping: {p}")

        if not valid_paths:
            log.warning("No valid files to upload")
            return

        log.info(f"Uploading {len(valid_paths)} file(s)...")

        file_input = None
        for selector in selectors:
            try:
                elements = await self._page.query_selector_all(selector)
                if elements:
                    file_input = elements[0]
                    break
            except Exception:
                continue

        if file_input:
            await file_input.set_input_files(valid_paths)
        else:
            try:
                await self._page.set_input_files("input[type='file']", valid_paths)
            except Exception as e:
                log.error(f"Failed to upload files: {e}")
                raise RuntimeError(f"Could not upload files: {e}")

        await asyncio.sleep(3)
        if len(valid_paths) > 1:
            await asyncio.sleep(len(valid_paths))
        log.info("File upload complete")

    async def _dismiss_overlays(self) -> None:
        """Check for and dismiss blocking dialogs/overlays."""
        try:
            result = await self._page.evaluate(
                """
                () => {
                    const info = { dismissed: [] };
                    const dialogs = document.querySelectorAll('[role="dialog"], dialog[open]');
                    for (const d of dialogs) {
                        const closeBtn = d.querySelector(
                            'button[aria-label="Close"], button[aria-label="Dismiss"]'
                        );
                        if (closeBtn) { closeBtn.click(); info.dismissed.push('dialog'); }
                    }
                    const allButtons = document.querySelectorAll('button');
                    for (const btn of allButtons) {
                        const t = (btn.innerText || '').trim().toLowerCase();
                        if (t.includes('continue generating')) { btn.click(); info.dismissed.push('continue'); }
                    }
                    return info;
                }
                """
            )
            if result and result.get("dismissed"):
                log.info(f"Dismissed overlays: {result['dismissed']}")
        except Exception:
            pass
