#!/usr/bin/env python3
"""Push to GitHub via Git Data API."""
import os, json, sys
import urllib.request, urllib.error

TOKEN = "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"
REPO = "ferelking242/panda-ai"
BRANCH = "main"
PROJECT = "/home/daytona/codebase"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".vite", "dist", "isolate", ".agents"}
SKIP_FILES = {".env.local", "bun.lock", "package-lock.json", "pnpm-lock.yaml"}

def api(method, path, data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API ERROR {e.code}: {err[:200]}")
        return None

def main():
    files = []
    for root, dirs, fnames in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in fnames:
            if fname in SKIP_FILES: continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, PROJECT)
            size = os.path.getsize(full)
            if size > 500_000 and fname.endswith(('.png', '.jpeg', '.jpg', '.gif', '.webp', '.lock')): continue
            files.append((rel, full))
    files.sort()
    print(f"Files: {len(files)}")

    ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    base_sha = ref["object"]["sha"] if ref else None
    print(f"Base: {base_sha[:12] if base_sha else 'empty'}")

    blob_map = {}
    for i, (rel, full) in enumerate(files):
        try:
            with open(full, "r", errors="replace") as f: content = f.read()
        except: continue
        blob = api("POST", f"/repos/{REPO}/git/blobs", {"encoding": "utf-8", "content": content})
        if blob and "sha" in blob: blob_map[rel] = blob["sha"]
        if (i+1) % 50 == 0: print(f"  Blobs: {i+1}/{len(files)}")

    print(f"Blobs: {len(blob_map)}/{len(files)}")
    tree_items = [{"path": p, "mode": "100644", "type": "blob", "sha": s} for p, s in blob_map.items()]
    tree_data = {"tree": tree_items}
    if base_sha: tree_data["base_tree"] = base_sha
    tree = api("POST", f"/repos/{REPO}/git/trees", tree_data)
    if not tree or "sha" not in tree: print("FAILED tree"); sys.exit(1)

    commit_data = {
        "message": "fix: CI artifact upload paths, duplicate hidden imports\n\n- Fix artifact upload with directory fallback and if-no-files-found: ignore\n- Remove duplicate 'secrets' in PyInstaller hidden imports",
        "tree": tree["sha"],
    }
    if base_sha: commit_data["parents"] = [base_sha]
    commit = api("POST", f"/repos/{REPO}/git/commits", commit_data)
    if not commit or "sha" not in commit: print("FAILED commit"); sys.exit(1)

    if base_sha:
        api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": True})
    else:
        api("POST", f"/repos/{REPO}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})

    print(f"PUSHED: https://github.com/{REPO} @ {commit['sha'][:12]}")

if __name__ == "__main__":
    main()
