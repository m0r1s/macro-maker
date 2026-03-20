# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["macro_maker/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pynput.keyboard._darwin",
        "pynput.mouse._darwin",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "Quartz",
        "HIServices",
        "AppKit",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MorisMacroMaker",
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MorisMacroMaker",
)

app = BUNDLE(
    coll,
    name="MorisMacroMaker.app",
    icon="icon.icns",
    bundle_identifier="com.moris.macromaker",
    info_plist={
        "CFBundleName": "MorisMacroMaker",
        "CFBundleDisplayName": "Moris Macro Maker",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "NSInputMonitoringUsageDescription":
            "Macro Maker needs Input Monitoring to record keyboard inputs.",
        "NSAppleEventsUsageDescription":
            "Macro Maker needs Accessibility to replay keyboard and mouse inputs.",
        "com.apple.security.automation.apple-events": True,
    },
)
