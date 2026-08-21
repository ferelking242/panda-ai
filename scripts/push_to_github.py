#!/usr/bin/env python3
"""Quick push to GitHub."""
import os, json, sys
import urllib.request, urllib.error

TOKEN = "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"
REPO = "ferelking242/panda-ai"
PROJECT = "/home/daytona/codebase"
SKIP = {".git","node_modules","__pycache__",".vite","dist","isolate",".agents"}
SKIP_F = {".env.local","bun.lock","package-lock.json","pnpm-lock.yaml"}

def api(m, p, d=None):
    url = f"https://api.github.com{p}"
    body = json.dumps(d).encode() if d else None
    req = urllib.request.Request(url, data=body, method=m)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if body: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  ERR {e.code}: {e.read().decode()[:200]}"); return None

files = []
for root, dirs, fnames in os.walk(PROJECT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in fnames:
        if f in SKIP_F: continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, PROJECT)
        if os.path.getsize(full) > 500000 and f.endswith(('.png','.jpeg','.jpg','.gif','.webp','.lock')): continue
        files.append((rel, full))
files.sort()
print(f"Files: {len(files)}")

ref = api("GET", f"/repos/{REPO}/git/ref/heads/main")
base = ref["object"]["sha"] if ref else None

bmap = {}
for i,(r,f) in enumerate(files):
    try:
        with open(f,"r",errors="replace") as fh: c=fh.read()
    except: continue
    b = api("POST",f"/repos/{REPO}/git/blobs",{"encoding":"utf-8","content":c})
    if b and "sha" in b: bmap[r]=b["sha"]
    if (i+1)%50==0: print(f"  Blobs: {i+1}/{len(files)}")

print(f"Blobs: {len(bmap)}/{len(files)}")
items = [{"path":p,"mode":"100644","type":"blob","sha":s} for p,s in bmap.items()]
tree = api("POST",f"/repos/{REPO}/git/trees",{"tree":items,"base_tree":base})
if not tree or "sha" not in tree: print("FAILED"); sys.exit(1)

cm = api("POST",f"/repos/{REPO}/git/commits",{
    "message":"fix: rewrite CI — tar.gz packaging, simplified binary upload steps",
    "tree":tree["sha"],"parents":[base]})
if not cm or "sha" not in cm: print("FAILED commit"); sys.exit(1)
api("PATCH",f"/repos/{REPO}/git/refs/heads/main",{"sha":cm["sha"],"force":True})
print(f"PUSHED: {cm['sha'][:12]}")
