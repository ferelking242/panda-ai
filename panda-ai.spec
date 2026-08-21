# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — builds a single-binary gateway server.

Usage:
    pip install pyinstaller
    python -m PyInstaller panda-ai.spec --clean

Output:
    dist/panda-ai        (Linux / macOS)
    dist/panda-ai.exe    (Windows)
"""

import sys
import os

a = Analysis(
    ['src/api/server.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('.env.example', '.'),
    ],
    hiddenimports=[
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
        'uvicorn.lifespan.on.off',
        'fastapi',
        'fastapi.middleware.cors',
        'pydantic',
        'pydantic.fields',
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'starlette',
        'starlette.responses',
        'starlette.requests',
        'starlette.types',
        'rich',
        'rich.console',
        'rich.logging',
        'textual',
        'typer',
        'dotenv',
        'dotenv.main',
        'langchain',
        'langchain_openai',
        'openai',
        'pypdf',
        'secrets',
        'src',
        'src.config',
        'src.log',
        'src.cache',
        'src.tokens',
        'src.api',
        'src.api.server',
        'src.api.routes',
        'src.api.openai_routes',
        'src.api.openai_schemas',
        'src.api.schemas',
        'src.api.dashboard_routes',
        'src.browser',
        'src.browser.manager',
        'src.browser.stealth',
        'src.browser.human',
        'src.browser.pool',
        'src.chatgpt',
        'src.chatgpt.client',
        'src.chatgpt.detector',
        'src.chatgpt.models',
        'src.claude',
        'src.claude.client',
        'src.claude.detector',
        'src.claude.selectors',
        'src.gemini',
        'src.gemini.client',
        'src.gemini.detector',
        'src.gemini.selectors',
        'src.selectors',
        'src.dom_observer',
        'src.network_recorder',
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
        'pytest',
        'unittest',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
)
