#!/usr/bin/env python3
import os, json, sys, urllib.request, urllib.error
T = "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"
R = "ferelking242/panda-ai"
PROJ = "/home/daytona/codebase"
SKIP_D = {".git", "node_modules", "__pycache__", ".vite", "dist", "isolate", ".agents"}
SKIP_F = {".env.local", "bun.lock", "package-lock.json", "pnpm-lock.yaml"}

def api(method, path, data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {T}")
    req.add_header("Accept", "application/vnd.github+json")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  ERR {e.code}: {e.read().decode()[:200]}")
        return None

def collect():
    files = []
    for root, dirs, fnames in os.walk(PROJ):
        dirs[:] = [d for d in dirs if d not in SKIP_D]
        for fname in fnames:
            if fname in SKIP_F:
                continue
            full_path = os.path.join(root, fname)
            rel = os.path.relpath(full_path, PROJ)
            sz = os.path.getsize(full_path)
            if sz > 500000 and fname.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.lock')):
                continue
            files.append((rel, full_path))
    return sorted(files)

def main():
    files = collect()
    print(f"Files: {len(files)}")
    ref = api("GET", f"/repos/{R}/git/ref/heads/main")
    base = ref["object"]["sha"]
    blob_map = {}
    for i, (rel, full) in enumerate(files):
        try:
            with open(full, "r", errors="replace") as fh:
                content = fh.read()
        except Exception:
            continue
        blob = api("POST", f"/repos/{R}/git/blobs", {"encoding": "utf-8", "content": content})
        if blob and "sha" in blob:
            blob_map[rel] = blob["sha"]
        if (i + 1) % 50 == 0:
            print(f"  Blobs: {i + 1}/{len(files)}")
    print(f"Blobs: {len(blob_map)}/{len(files)}")
    items = [{"path": p, "mode": "100644", "type": "blob", "sha": s} for p, s in blob_map.items()]
    tree = api("POST", f"/repos/{R}/git/trees", {"tree": items, "base_tree": base})
    if not tree or "sha" not in tree:
        print("FAILED: tree"); sys.exit(1)
    cm = api("POST", f"/repos/{R}/git/commits", {
        "message": "fix: CI all uploads continue-on-error + Android settings.gradle fix",
        "tree": tree["sha"], "parents": [base]
    })
    if not cm or "sha" not in cm:
        print("FAILED: commit"); sys.exit(1)
    api("PATCH", f"/repos/{R}/git/refs/heads/main", {"sha": cm["sha"], "force": True})
    print(f"PUSHED: https://github.com/{R} @ {cm['sha'][:12]}")

if __name__ == "__main__":
    main()
