# Déploiement VPS — Panda AI

Guide de déploiement du gateway Panda AI sur un VPS (Debian/Ubuntu).

## Démarrage rapide

### Option A — Script natif (recommandé pour tester)

```bash
git clone https://github.com/ferelking242/Panda-Ai.git
cd Panda-Ai
sudo bash scripts/install_vps.sh
```

Le script installe tout : dépendances système, venv Python, Chromium,
dashboard Next.js, services systemd (`panda-ai` + `panda-dashboard`),
et génère un `.env` avec un `API_TOKEN` aléatoire (chmod 600).

- API       → `http://VPS_IP:8000`
- Dashboard → `http://VPS_IP:5000`
- Token     → `grep API_TOKEN .env`

```bash
sudo ufw allow 8000/tcp 5000/tcp   # ouvrir les ports
journalctl -u panda-ai -f          # suivre les logs
```

### Option B — Docker Compose

```bash
cp .env.example .env       # éditer PROVIDER / API_TOKEN
docker compose up -d --build
```

Deux conteneurs : `panda-ai` (:8000) et `panda-dashboard` (:5000).
Le dashboard compile au premier démarrage (~1-2 min).

> Sans `API_TOKEN`, le gateway génère automatiquement un token de
> bootstrap au premier lancement :
> `cat .panda_bootstrap_token`

## Connecter le navigateur (mode headless)

Sur un VPS sans écran, `HEADLESS=true` est obligatoire (fait par le
script/compose). Pour se connecter aux fournisseurs (ChatGPT, Claude…)
sans interface graphique :

1. Ouvre le dashboard → **Cookies** (`/dashboard/cookies`)
2. Sur ton PC, exporte les cookies de ta session avec une extension
   type "Get cookies.txt LOCALLY" (format JSON)
3. Colle le JSON dans le dashboard → **Import** → la session est
   rechargée et `logged_in` passe à `true`

Alternative en ligne de commande :

```bash
TOKEN=$(grep API_TOKEN .env | cut -d= -f2)
curl -X POST http://127.0.0.1:8000/api/dashboard/cookies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cookies": [ ... ]}'
```

## Tester que tout marche

```bash
TOKEN=$(grep API_TOKEN .env | cut -d= -f2)

# 1. Backend vivant
curl -s http://127.0.0.1:8000/healthz
# → {"status":"ok"}

# 2. Auth OK + modèles listés
curl -s http://127.0.0.1:8000/v1/models -H "Authorization: Bearer $TOKEN"

# 3. Chat complet (OpenAI-compatible)
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"ping"}]}'

# 4. Dashboard : stats accessibles avec le même token
curl -s http://127.0.0.1:5000/api/dashboard/stats -H "Authorization: Bearer $TOKEN"
```

Depuis un client OpenAI :

```python
from openai import OpenAI
client = OpenAI(base_url="http://VPS_IP:8000/v1", api_key="pnd_...")
print(client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
).choices[0].message.content)
```

## Sécurité

- `.panda_tokens.json` stocke uniquement des hash SHA-256 (chmod 600).
  Les tokens survivent aux redémarrages.
- Le bootstrap token n'est jamais loggé, seulement écrit dans
  `.panda_bootstrap_token` (chmod 600) — supprime-le après avoir créé
  un vrai token depuis le dashboard.
- Devant Internet ouvert, mets un reverse proxy HTTPS (Caddy/Nginx +
  Let's Encrypt) et n'expose pas 8000 directement :

```
# Caddyfile exemple
api.tondomaine.com {
    reverse_proxy 127.0.0.1:8000
}
app.tondomaine.com {
    reverse_proxy 127.0.0.1:5000
}
```

## Dépannage

| Symptôme | Cause probable | Fix |
|---|---|---|
| Chromium ne démarre pas | libs manquantes | `patchright install-deps chromium` |
| `Not logged in to …` au boot | session absente | importer les cookies (voir ci-dessus) |
| Dashboard vide / erreurs réseau | API injoignable | vérifier `API_ORIGIN` (compose: `http://panda-ai:8000`) |
| 401 partout | mauvais token | `grep API_TOKEN .env` ou `cat .panda_bootstrap_token` |
| Le port est occupé | ancien process | `systemctl restart panda-ai` |

## Gestion des services

```bash
systemctl status panda-ai panda-dashboard
systemctl restart panda-ai
journalctl -u panda-dashboard -n 50
```

Mode Android (panda-ide) : laisser `BROWSER_MODE=android` côté IDE ;
sur VPS utiliser le mode par défaut `launch`.
