# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Panda AI Gateway.
Builds a single-file binary that bundles Python + all dependencies.

Usage:
    pip install pyinstaller
    pyinstaller panda-ai.spec --clean

Output: dist/panda-ai (Linux/macOS) or dist/panda-ai.exe (Windows)
"""

import os
import sys

block_cipher = None

a = Analysis(
    ['src/cli/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/cli/catgpt.tcss', 'src/cli'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.requests',
        'starlette.responses',
        'starlette.types',
        'textual',
        'textual.app',
        'textual.binding',
        'textual.containers',
        'textual.reactive',
        'textual.screen',
        'textual.widget',
        'textual.widgets',
        'typer',
        'rich',
        'rich.markdown',
        'httpx',
        'dotenv',
        'patchright',
        'playwright_stealth',
        'openai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='panda-ai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
