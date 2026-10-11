# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 只打包程序自带资源；input/data/output 是用户数据，
        # 由 launcher.py 在 exe 所在目录创建，绝不能打进 exe
        ('frontend', 'frontend'),
        ('backend', 'backend'),
        ('config/settings.example.json', 'config'),
        ('PRODUCT.md', '.'),
    ],
    hiddenimports=[
        'backend', 'backend.database', 'backend.config', 'backend.main', 'backend.paths',
        'backend.version',
        'backend.models', 'backend.models.organization', 'backend.models.monitor',
        'backend.routes', 'backend.routes.organizations', 'backend.routes.monitor',
        'backend.routes.files', 'backend.routes.writing', 'backend.routes.projects',
        'backend.routes.export', 'backend.routes.settings_api',
        'backend.services', 'backend.services.file_analyzer', 'backend.services.file_watcher',
        'backend.services.archiver', 'backend.services.writing_engine',
        'backend.services.template_service', 'backend.services.project_service',
        'backend.services.file_extractor',
        'backend.utils', 'backend.utils.content_extractor', 'backend.utils.naming',
        # 以下两个是函数内部 import，显式列出避免 PyInstaller 漏打包
        'backend.utils.rule_classifier',
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols',
        'watchdog', 'docx', 'PyPDF2', 'openpyxl', 'pptx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        '.claude', '.superpowers', '.git', 'test_*',
        'FileOrganizer', 'landing', 'docs', 'node_modules',
        '__pycache__', '*.pyc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CampusOS',
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
