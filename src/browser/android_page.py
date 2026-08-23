"""
AndroidPage — Remplacement drop-in de Playwright Page pour Android.

Au lieu de contrôler Chromium via Playwright, AndroidPage envoie des
commandes JavaScript à la WebView Flutter de panda-ide via un bridge HTTP
local (port configurable, défaut 9221).

Architecture (protocole v2 — multi-session) :
  Python (gateway)  →  HTTP POST :9221 {action, session, ...}
                     →  GatewayWebViewBridge (panda-ide)
                     →  onglet dédié dans le navigateur existant de l'IDE
                        (flutter_inappwebview — zéro doublon de moteur)
                     ←  retourne le résultat JSON

Chaque AndroidPage est liée à UNE session (= un onglet isolé du navigateur
de l'IDE, cookies séparés par profil). Plusieurs AndroidPage peuvent donc
vivre en parallèle : ChatGPT + Claude + Gemini simultanément.

Compatibilité : implémente le sous-ensemble de l'API Playwright Page
utilisé par les clients fournisseurs (ChatGPTClient, ClaudeClient, …).
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx

from src.config import Config
from src.log import setup_logging

log = setup_logging("android_page")


class AndroidPageError(Exception):
    """Erreur lors de la communication avec le bridge WebView."""


class AndroidPage:
    """
    Pseudo-page Playwright pour Android via bridge HTTP → Flutter WebView.

    Args:
        bridge_port: port HTTP du bridge Flutter (défaut Config.WEBVIEW_BRIDGE_PORT).
        session_id: identifiant de session. Chaque session = un onglet isolé
            (profil dédié) dans le navigateur intégré de panda-ide.
            Défaut : le fournisseur actif (ex "chatgpt", "claude").

    Usage :
        page = AndroidPage(session_id="chatgpt")
        await page.ensure_session("https://chatgpt.com")
        result = await page.evaluate("document.title")
    """

    def __init__(
        self,
        bridge_port: int | None = None,
        session_id: str | None = None,
        close_session_on_exit: bool = True,
    ) -> None:
        self._port = bridge_port or Config.WEBVIEW_BRIDGE_PORT
        self._base = f"http://127.0.0.1:{self._port}"
        self._client: httpx.AsyncClient | None = None
        # Session par défaut = nom du fournisseur → 1 onglet par fournisseur
        self.session_id = session_id or Config.PROVIDER
        self._close_session_on_exit = close_session_on_exit
        self.url: str = ""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Ferme le client HTTP et, demandé, la session côté IDE."""
        if self._close_session_on_exit:
            try:
                await self.close_session()
            except Exception as e:
                log.debug(f"[AndroidPage] close_session ignored: {e}")
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Sessions (protocole v2) ──────────────────────────────────────────────

    async def ensure_session(self, url: str | None = None) -> Any:
        """
        Crée la session côté IDE si absente (idempotent) et navigue vers
        `url` si fourni. Retourne l'état de la session créé par le bridge.
        """
        payload: dict[str, Any] = {"session": self.session_id}
        if url:
            payload["url"] = url
            self.url = url
        log.info(f"[AndroidPage] ensure_session({self.session_id}) url={url}")
        return await self._bridge("session.create", payload)

    async def close_session(self) -> Any:
        """Ferme la session et libère l'onglet côté IDE."""
        return await self._bridge("session.close", {"session": self.session_id})

    @staticmethod
    async def list_sessions(bridge_port: int | None = None) -> list[dict[str, Any]]:
        """Liste les sessions actives côté IDE (helper statique)."""
        probe = AndroidPage(
            bridge_port=bridge_port,
            session_id="__probe__",
            close_session_on_exit=False,
        )
        try:
            result = await probe._bridge("sessions.list")
            return result or []
        finally:
            if probe._client and not probe._client.is_closed:
                await probe._client.aclose()

    # ── Bridge helpers ────────────────────────────────────────────────────────

    async def _bridge(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        """Envoie une commande au bridge Flutter et retourne le résultat."""
        client = await self._get_client()
        body = {"action": action, **(payload or {})}
        # Protocole v2 : toute commande ciblée porte sa session.
        if action not in ("ping", "sessions.list") and "session" not in body:
            body["session"] = self.session_id
        try:
            resp = await client.post(f"{self._base}/cmd", json=body)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise AndroidPageError(f"Bridge error: {data['error']}")
            return data.get("result")
        except httpx.ConnectError as e:
            raise AndroidPageError(
                f"Cannot reach WebView bridge on port {self._port}. "
                "Make sure panda-ide is running with the Gateway panel open."
            ) from e
        except httpx.HTTPStatusError as e:
            raise AndroidPageError(f"Bridge HTTP {e.response.status_code}: {e.response.text}") from e

    # ── Navigation ────────────────────────────────────────────────────────────

    async def goto(self, url: str, **kwargs) -> None:
        """Navigue vers l'URL dans la session (onglet dédié) de l'IDE."""
        log.info(f"[AndroidPage:{self.session_id}] navigate → {url}")
        self.url = url
        await self._bridge("navigate", {"url": url})
        # Attendre que la page se charge
        await asyncio.sleep(2.0)

    # Alias Playwright
    async def navigate(self, url: str, **kwargs) -> None:
        await self.goto(url, **kwargs)

    # ── JavaScript evaluation ─────────────────────────────────────────────────

    async def evaluate(self, expression: str, *args) -> Any:
        """Évalue une expression JS dans la session et retourne le résultat."""
        script = expression
        if args:
            # Injecter les arguments comme `arguments` n'est pas supporté
            # — sérialiser comme variables locales
            args_json = json.dumps(list(args))
            script = f"(function(args){{ return ({expression}); }})({args_json})"
        return await self._bridge("eval", {"script": script})

    async def evaluate_handle(self, expression: str, *args) -> Any:
        return await self.evaluate(expression, *args)

    # ── DOM interactions ──────────────────────────────────────────────────────

    async def query_selector(self, selector: str) -> "AndroidElement | None":
        exists = await self.evaluate(
            f"document.querySelector({json.dumps(selector)}) !== null"
        )
        if exists:
            return AndroidElement(selector, self)
        return None

    async def query_selector_all(self, selector: str) -> list["AndroidElement"]:
        count = await self.evaluate(
            f"document.querySelectorAll({json.dumps(selector)}).length"
        )
        return [AndroidElement(f"{selector}:nth-child({i+1})", self) for i in range(count or 0)]

    async def wait_for_selector(
        self,
        selector: str,
        timeout: float = 10000,
        state: str = "visible",
        **kwargs,
    ) -> "AndroidElement | None":
        """Attend qu'un sélecteur soit présent dans le DOM."""
        deadline = time.monotonic() + (timeout / 1000)
        poll_ms = 500
        script = f"document.querySelector({json.dumps(selector)}) !== null"
        while time.monotonic() < deadline:
            try:
                found = await self.evaluate(script)
                if found:
                    return AndroidElement(selector, self)
            except Exception:
                pass
            await asyncio.sleep(poll_ms / 1000)
        log.warning(f"[AndroidPage:{self.session_id}] wait_for_selector timeout: {selector}")
        return None

    async def fill(self, selector: str, value: str, **kwargs) -> None:
        """Remplit un champ de formulaire."""
        escaped = json.dumps(value)
        await self.evaluate(
            f"""
            (function() {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return;
                el.focus();
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value') ||
                    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
                if (nativeInputValueSetter) {{
                    nativeInputValueSetter.set.call(el, {escaped});
                }} else {{
                    el.value = {escaped};
                }}
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }})()
            """
        )

    async def type(self, selector: str, text: str, delay: int = 50, **kwargs) -> None:
        """Tape du texte caractère par caractère."""
        await self.fill(selector, text)

    async def click(self, selector: str, **kwargs) -> None:
        """Clique sur un élément."""
        await self.evaluate(
            f"document.querySelector({json.dumps(selector)})?.click()"
        )

    async def press(self, selector: str, key: str, **kwargs) -> None:
        """Simule une touche du clavier sur un élément."""
        key_code_map = {"Enter": 13, "Escape": 27, "Tab": 9, "ArrowDown": 40}
        code = key_code_map.get(key, 0)
        await self.evaluate(
            f"""
            (function() {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return;
                ['keydown','keypress','keyup'].forEach(t => {{
                    el.dispatchEvent(new KeyboardEvent(t, {{
                        key: {json.dumps(key)},
                        keyCode: {code},
                        bubbles: true
                    }}));
                }});
            }})()
            """
        )

    # ── Page content ──────────────────────────────────────────────────────────

    async def content(self) -> str:
        """Retourne le HTML complet de la page."""
        return await self.evaluate("document.documentElement.outerHTML") or ""

    async def title(self) -> str:
        """Retourne le titre de la page."""
        return await self.evaluate("document.title") or ""

    async def inner_text(self, selector: str) -> str:
        return await self.evaluate(
            f"document.querySelector({json.dumps(selector)})?.innerText || ''"
        ) or ""

    async def inner_html(self, selector: str) -> str:
        return await self.evaluate(
            f"document.querySelector({json.dumps(selector)})?.innerHTML || ''"
        ) or ""

    async def input_value(self, selector: str) -> str:
        return await self.evaluate(
            f"document.querySelector({json.dumps(selector)})?.value || ''"
        ) or ""

    # ── Wait helpers ──────────────────────────────────────────────────────────

    async def wait_for_timeout(self, ms: int) -> None:
        await asyncio.sleep(ms / 1000)

    async def wait_for_load_state(self, state: str = "load", **kwargs) -> None:
        await asyncio.sleep(1.0)

    # ── Stealth (no-op sur Android — la WebView est déjà native) ─────────────

    async def add_init_script(self, script: str) -> None:
        pass  # Non applicable pour WebView native

    # ── Screenshot (retourne None — non supporté via bridge) ─────────────────

    async def screenshot(self, **kwargs) -> bytes | None:
        return None

    # ── Context (stub) ────────────────────────────────────────────────────────

    @property
    def context(self) -> "AndroidContext":
        return AndroidContext()

    def __repr__(self) -> str:
        return f"<AndroidPage session={self.session_id!r} url={self.url!r} bridge=:{self._port}>"


class AndroidElement:
    """Proxy d'élément DOM pour AndroidPage."""

    def __init__(self, selector: str, page: AndroidPage) -> None:
        self._selector = selector
        self._page = page

    async def click(self, **kwargs) -> None:
        await self._page.click(self._selector)

    async def fill(self, value: str, **kwargs) -> None:
        await self._page.fill(self._selector, value)

    async def type(self, text: str, **kwargs) -> None:
        await self._page.type(self._selector, text)

    async def press(self, key: str, **kwargs) -> None:
        await self._page.press(self._selector, key)

    async def inner_text(self) -> str:
        return await self._page.inner_text(self._selector)

    async def inner_html(self) -> str:
        return await self._page.inner_html(self._selector)

    async def input_value(self) -> str:
        return await self._page.input_value(self._selector)

    async def evaluate(self, expression: str, *args) -> Any:
        full = (
            f"(function(el){{ return ({expression}); }})"
            f"(document.querySelector({json.dumps(self._selector)}))"
        )
        return await self._page.evaluate(full)

    async def get_attribute(self, name: str) -> str | None:
        return await self._page.evaluate(
            f"document.querySelector({json.dumps(self._selector)})"
            f"?.getAttribute({json.dumps(name)})"
        )

    def __repr__(self) -> str:
        return f"<AndroidElement selector={self._selector!r}>"


class AndroidContext:
    """Stub de BrowserContext pour compatibilité."""

    async def add_cookies(self, cookies: list) -> None:
        pass

    async def cookies(self, urls: list | None = None) -> list:
        return []
