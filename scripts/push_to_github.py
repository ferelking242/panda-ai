#!/usr/bin/env python3
"""Push all project files to GitHub via Git Data API (blobs -> tree -> commit)."""
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

def collect_files():
    files = []
    for root, dirs, fnames in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in fnames:
            if fname in SKIP_FILES:
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, PROJECT)
            size = os.path.getsize(full)
            if size > 500_000 and fname.endswith(('.png', '.jpeg', '.jpg', '.gif', '.webp', '.lock')):
                continue
            files.append((rel, full, size))
    return sorted(files, key=lambda x: x[0])

def main():
    print("Collecting files...")
    files = collect_files()
    print(f"Found {len(files)} files to push\n")

    # Get current ref
    ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    if ref:
        base_sha = ref["object"]["sha"]
        print(f"Base: {base_sha[:12]}")
    else:
        base_sha = None
        print("Empty repo")

    # Create blobs
    blob_map = {}
    for i, (rel, full, size) in enumerate(files):
        try:
            with open(full, "r", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"  SKIP {rel}: {e}")
            continue
        blob = api("POST", f"/repos/{REPO}/git/blobs", {"encoding": "utf-8", "content": content})
        if blob and "sha" in blob:
            blob_map[rel] = blob["sha"]
        if (i+1) % 30 == 0:
            print(f"  Blobs: {i+1}/{len(files)}")

    print(f"\nBlobs: {len(blob_map)}/{len(files)}")

    # Create tree
    tree_items = [{"path": p, "mode": "100644", "type": "blob", "sha": s} for p, s in blob_map.items()]
    tree_data = {"tree": tree_items}
    if base_sha:
        tree_data["base_tree"] = base_sha
    
    tree = api("POST", f"/repos/{REPO}/git/trees", tree_data)
    if not tree or "sha" not in tree:
        print("FAILED: tree"); sys.exit(1)
    print(f"Tree: {tree['sha'][:12]}")

    # Create commit
    msg = "Restructure: root layout, 8 providers, new README, unit tests\n\n- All code at root (no subfolder)\n- Remove Replit files\n- 8 providers: ChatGPT, Claude, Gemini, DeepSeek, Grok, Mistral, Qwen, Kimi\n- New README with full provider matrix\n- 12 unit tests passing\n- Dashboard separated"
    commit_data = {"message": msg, "tree": tree["sha"]}
    if base_sha:
        commit_data["parents"] = [base_sha]
    
    commit = api("POST", f"/repos/{REPO}/git/commits", commit_data)
    if not commit or "sha" not in commit:
        print("FAILED: commit"); sys.exit(1)
    print(f"Commit: {commit['sha'][:12]}")

    # Update ref
    if base_sha:
        result = api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": True})
    else:
        result = api("POST", f"/repos/{REPO}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})

    if result:
        print(f"\n✅ PUSHED: https://github.com/{REPO}")
    else:
        print("\n❌ FAILED to update ref")

if __name__ == "__main__":
    main()
