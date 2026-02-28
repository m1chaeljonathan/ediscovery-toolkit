# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for eDiscovery Toolkit desktop app.

Build:
    pip install pyinstaller
    pyinstaller ediscovery-toolkit.spec

Output:
    dist/eDiscovery Toolkit.app  (macOS)
    dist/eDiscovery Toolkit.exe  (Windows)
"""

import os
import importlib
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# Locate Streamlit's package data (static frontend assets)
streamlit_dir = os.path.dirname(importlib.import_module('streamlit').__file__)

# Collect package metadata required at runtime by importlib.metadata
metadata_datas = []
for pkg in ['streamlit', 'altair', 'openai', 'pydantic', 'pydantic-core',
            'pandas', 'requests', 'pdfplumber', 'openpyxl', 'pyarrow',
            'rich', 'packaging', 'importlib-metadata']:
    try:
        metadata_datas += copy_metadata(pkg)
    except Exception:
        pass  # skip if package not installed

# Collect Streamlit's full data files (config defaults, etc.)
streamlit_data = collect_data_files('streamlit')

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Application code
        ('app.py', '.'),
        ('config.py', '.'),
        ('modules/', 'modules/'),
        ('parsers/', 'parsers/'),
        ('llm/', 'llm/'),
        ('ui/', 'ui/'),
        # Streamlit frontend assets (required at runtime)
        (os.path.join(streamlit_dir, 'static'), 'streamlit/static'),
        (os.path.join(streamlit_dir, 'runtime'), 'streamlit/runtime'),
    ] + metadata_datas + streamlit_data,
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.caching',
        'streamlit.runtime.state',
        'pdfplumber',
        'openpyxl',
        'openai',
        'yaml',
        'dateutil',
        'requests',
        'altair',
        'pandas',
        'pyarrow',
        'pydantic',
        'toml',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'notebook'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='eDiscovery Toolkit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eDiscovery Toolkit',
)

# macOS .app bundle
import platform
if platform.system() == 'Darwin':
    app = BUNDLE(
        coll,
        name='eDiscovery Toolkit.app',
        bundle_identifier='com.ediscovery-toolkit.app',
        info_plist={
            'CFBundleShortVersionString': '0.2.0',
            'CFBundleDisplayName': 'eDiscovery Toolkit',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
