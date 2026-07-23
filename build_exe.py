# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 单文件 exe 输出。

运行方式:
    C:\Python314\python.exe -m PyInstaller --onefile --noconsole --clean --name "绝夜之旅" --add-data "game;game" main.py
"""

# 也可作为 .spec 文件直接使用:
#   C:\Python314\python.exe -m PyInstaller build_exe.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('game/', 'game/')],
    hiddenimports=[
        'pygame', 'game', 'game.engine', 'game.dice', 'game.character',
        'game.combat', 'game.event', 'game.chapter', 'game.ui', 'game.save',
        'game.items', 'game.equipment', 'game.skill_tree', 'game.shop',
        'game.faction', 'game.scene_renderer',
        'game.story', 'game.story.chapter1', 'game.story.chapter2',
        'game.story.chapter3', 'game.story.chapter4',
    ],
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
    name='绝夜之旅',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
