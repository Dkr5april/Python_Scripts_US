# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/backup/US_word_files/Interview_learnings/python_scripts/Projects/Parasara_Class_Scripts/5FOLD_MATTERS\\secured_5Fold_Matters_Telugu5.py'],
    pathex=['C:\\backup\\US_word_files\\Interview_learnings\\python_scripts\\Projects\\License'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='secured_5Fold_Matters_Telugu5',
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
