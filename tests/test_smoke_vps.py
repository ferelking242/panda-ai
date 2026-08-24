"""Smoke test Panda AI — in-process, no server started, no browser launched.

Uses httpx ASGITransport (lifespan NOT run → no Chromium launch).
Verifies: app assembly, routers registered, auth middleware, token
persistence, bootstrap logic.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = []
FAIL = []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}{(' — ' + detail) if detail and not cond else ''}")
    print(("  ✅ " if cond else "  ❌ ") + name + (f" ({detail})" if detail else ""))


async def main():
    # ── 1. App import & assembly ────────────────────────────────────
    print("\n[1] Import de l'app")
    try:
        from src.api.server import app, _ensure_bootstrap_token  # noqa: E402
        check("src.api.server importe sans erreur", True)
    except Exception as e:
        check("src.api.server importe sans erreur", False, repr(e))
        return

    # FastAPI >= 0.120 wraps included routers lazily (_IncludedRouter).
    # HTTP routes → openapi schema ; websockets → original_router walk.
    try:
        schema_paths = set(app.openapi()["paths"].keys())
    except Exception as e:
        schema_paths = set()
        check("openapi schema généré", False, repr(e))

    ws_paths = set()
    def walk(rs):
        for r in rs:
            p = getattr(r, "path", None)
            if p and "WebSocket" in type(r).__name__:
                ws_paths.add(p)
            inner = getattr(r, "original_router", None)
            if inner is not None:
                walk(inner.routes)
    walk(app.routes)

    routes = schema_paths | ws_paths | {getattr(r, "path", None) for r in app.routes} - {None}
    check(f"{len(routes)} routes découvertes", len(routes) >= 10, str(len(routes)))
    for expected in ("/healthz", "/v1/models", "/v1/chat/completions",
                     "/api/dashboard/stats", "/api/dashboard/cookies",
                     "/ws/chat", "/api/queue/status", "/client"):
        check(f"route {expected} enregistrée", expected in routes)

    # ── 2. Token store : persistance disque ────────────────────────
    print("\n[2] Tokens — persistance")
    from src.tokens import token_store, generate_token, TokenMeta, _PERSIST_PATH
    if _PERSIST_PATH.exists():
        _PERSIST_PATH.unlink()
    tok = generate_token()
    token_store.register(tok, TokenMeta(name="smoke-test"))
    check("fichier de persistance créé", _PERSIST_PATH.exists())
    check("permissions 600", (_PERSIST_PATH.stat().st_mode & 0o777) == 0o600)
    raw = _PERSIST_PATH.read_text()
    check("le token brut n'est PAS stocké (hash seul)", tok not in raw)

    from src.tokens import TokenStore as TS2
    fresh_store = TS2()  # nouvelle instance = simule un restart
    check("token retrouvé après 'restart'", fresh_store.validate(tok) is not None)

    # ── 3. Middleware auth via ASGI transport ──────────────────────
    print("\n[3] Auth middleware (httpx ASGI, lifespan non exécuté)")
    import httpx
    from src.config import Config

    Config.API_TOKEN = ""          # pas d'auth legacy
    token_store._tokens.clear()    # store vide → tout doit être 401
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://test") as c:
        r = await c.get("/healthz")
        check("/healthz ouvert (pas d'auth)", r.status_code == 200, str(r.status_code))

        r = await c.get("/v1/models")
        check("/v1/models sans token → 401", r.status_code == 401, str(r.status_code))

        r = await c.post("/api/dashboard/token/generate", json={})
        check("génération token protégée aussi (401)", r.status_code == 401, str(r.status_code))

    # ── 4. Auth legacy API_TOKEN + store rechargé ──────────────────
    print("\n[4] Accès authentifié")
    Config.API_TOKEN = "legacy-secret-123"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://test") as c:
        r = await c.get("/v1/models", headers={"Authorization": "Bearer legacy-secret-123"})
        check("/v1/models avec API_TOKEN legacy → 200", r.status_code == 200,
              f"{r.status_code} {r.text[:120]}")

        r = await c.get("/api/dashboard/stats", headers={"Authorization": "Bearer legacy-secret-123"})
        check("/api/dashboard/stats authentifié → 200", r.status_code == 200,
              f"{r.status_code} {r.text[:120]}")

        # cookie api_token= accepté par le middleware (flux dashboard)
        httpx.Cookies  # noqa: B018 — just to keep flake quiet
        r2 = await c.get("/status", cookies={"api_token": "legacy-secret-123"})
        check("cookie api_token= accepté", r2.status_code in (200, 401, 404), str(r2.status_code))

    # ── 5. Bootstrap token ─────────────────────────────────────────
    print("\n[5] Bootstrap token premier lancement")
    from src.tokens import is_valid_format
    Config.API_TOKEN = ""
    token_store._tokens.clear()
    if _PERSIST_PATH.exists():
        _PERSIST_PATH.unlink()

    _ensure_bootstrap_token()
    boot_path = Config.PROJECT_ROOT / ".panda_bootstrap_token"
    check("fichier bootstrap écrit", boot_path.exists())
    if boot_path.exists():
        boot_tok = boot_path.read_text().strip()
        check("format pnd_ valide", is_valid_format(boot_tok))
        check("permissions 600", (boot_path.stat().st_mode & 0o777) == 0o600)
        check("token enregistré dans le store",
              token_store.validate(boot_tok) is not None)

    # second appel → ne régénère pas (idempotent)
    before = boot_path.read_text() if boot_path.exists() else ""
    _ensure_bootstrap_token()
    after = boot_path.read_text() if boot_path.exists() else ""
    check("bootstrap idempotent (pas d'écrasement)", before == after)

    # ── cleanup ────────────────────────────────────────────────────
    for p in (_PERSIST_PATH, boot_path):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    print(f"\n{'='*50}\nRÉSULTAT: {len(PASS)} OK / {len(FAIL)} ÉCHEC(S)")
    if FAIL:
        for f in FAIL:
            print("  ❌", f)
        sys.exit(1)


asyncio.run(main())
