# 🐼 Android Multi-Session — Protocole WebView Bridge v2

**Date :** 23 août 2026
**Statut :** Implémenté (Python) + implémentation de référence (Dart)

---

## 1. Le problème

Avant le protocole v2, le mode `BROWSER_MODE=android` de panda-ai ne pouvait
gérer **qu'un seul fournisseur à la fois** : un unique `AndroidPage` → une
unique commande `eval`/`navigate` → la WebView attachée au bridge. Impossible
d'avoir ChatGPT **et** Claude **et** Gemini actifs simultanément, et le
fallback `PROVIDER_CHAIN` ne fonctionnait pas sur Android (il lançait des
Chromium Playwright).

## 2. La décision d'architecture : zéro doublon

Panda IDE possède **déjà un navigateur complet** (`lib/ui/browser/`) :
multi-onglets, multi-profils, `flutter_inappwebview`, `IndexedStack` (les
onglets restent vivants → **bascule instantanée**), isolation des cookies par
profil via `dataDirectoryIdentifier`.

> ❌ On ne crée **aucun** second moteur de WebView, aucune WebView cachée.
> ✅ 1 session gateway = **1 onglet du navigateur intégré** + 1 profil dédié.

Bénéfices :
- Bascule instantanée entre fournisseurs (onglets gardés vivants).
- L'utilisateur **voit** ce que fait l'IA : ce sont de vrais onglets.
- Cookies/sessions isolés par fournisseur (profil `AI · <provider>`).
- Moins de mémoire qu'un stack WebView parallèle.

## 3. Flux

```
Client OpenAI SDK / Panda Agent
        │  model="claude-browser"
        ▼
FastAPI panda-ai (:8000)
        │  route → client du bon fournisseur
        ▼
AndroidPage(session_id="claude")
        │  POST http://127.0.0.1:9221/cmd
        │  { "action": "eval", "session": "claude", "script": "…" }
        ▼
GatewayWebViewBridge (panda-ide, port 9221)
        │
        ▼
GatewaySessionManager ──► BrowserController (navigateur intégré)
        │                        │
        │                        ├─ onglet "AI · claude"  (profil isolé)
        │                        ├─ onglet "AI · chatgpt" (profil isolé)
        │                        └─ onglet "AI · gemini"  (profil isolé)
        ▼
flutter_inappwebview (IndexedStack — tous vivants)
```

## 4. Protocole v2

Toutes les commandes : `POST /cmd` avec JSON. Toute commande ciblée porte
`"session"`. Sans `session` → `"default"` (compat v1).

| Action | Payload | Retour |
|---|---|---|
| `ping` | — | `"pong"` |
| `sessions.list` | — | `[{session, tabId, url, title, loading, active}]` |
| `session.create` | `{session, url?}` | `{session, tabId}` (idempotent) |
| `session.close` | `{session}` | `true/false` |
| `navigate` | `{session, url}` | `true` |
| `eval` | `{session, script}` | valeur JSON (expression JS, `undefined`→`null`) |

`script` est une **expression JS** (comme Playwright `page.evaluate`). Le côté
IDE wrappe en `(function(){ return JSON.stringify((<script>)); })()` puis
décode — résultat toujours sérialisable.

## 5. Côté panda-ai (ce dépôt)

- `src/browser/android_page.py` — `AndroidPage(session_id=...)` :
  - chaque `_bridge()` envoie `"session"`;
  - `ensure_session(url)` / `close_session()` / `AndroidPage.list_sessions()`.
- `src/api/server.py` (mode android) :
  - **une session par fournisseur** : primaire + `PROVIDER_CHAIN`;
  - sessions démarrées au boot (`ensure_session(url_du_fournisseur)`);
  - fallback enregistré via `set_fallback_chain()` → le routage/fallback
    OpenAI fonctionne sur Android.

### Config Android multi-fournisseurs

```bash
# .env (ou android.env côté IDE)
BROWSER_MODE=android
WEBVIEW_BRIDGE_PORT=9221
PROVIDER=chatgpt
PROVIDER_CHAIN=chatgpt,claude,gemini   # 3 sessions simultanées
```

```python
from openai import OpenAI
c = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="pnd_xxx")
c.chat.completions.create(model="gemini-2.0-flash", messages=[...])  # session gemini
```

Parallélisme : verrou **par handle fournisseur** (`_get_handle_lock`) — deux
fournisseurs différents répondent en parallèle ; les requêtes d'un même
fournisseur restent sérialisées (une UI de chat = 1 message à la fois).

## 6. Côté panda-ide (implémentation de référence)

Fichiers de référence (à porter dans le dépôt panda-ide) :

| Fichier | Rôle |
|---|---|
| `reference/panda-ide/lib/gateway/gateway_webview_bridge.dart` | Serveur HTTP :9221, protocole v2, normalisation de session |
| `reference/panda-ide/lib/gateway/gateway_session_manager.dart` | Sessions → onglets du navigateur intégré + profils `AI · *` + eval JSON-safe |

Branchement minimal :

```dart
final bridge = GatewayWebViewBridge();
final sessions = GatewaySessionManager(browser: browserController);
bridge.onCommand = sessions.handleCommand;
await bridge.start();
```

`GatewayManager.start()` passe déjà `BROWSER_MODE=android` et
`WEBVIEW_BRIDGE_PORT=9221` au processus Python — rien à changer de ce côté.

## 7. Garanties

- **Idempotence** : `session.create` sur session existante = no-op (+ nav si `url`).
- **Auto-réparation** : onglet fermé par l'utilisateur → `_tabIdFor` recrée la session.
- **Rétrocompat v1** : commandes sans `session` → `"default"`.
- **Arrêt propre** : `page.close()` ferme la session (onglet) sauf
  `close_session_on_exit=False`.
