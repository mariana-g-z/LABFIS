# -*- mode: python ; coding: utf-8 -*-
# LabManager PyInstaller spec
# Usado por build_macos.sh y build_windows.bat
import sys, os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/icon.png',    'assets'),
        ('assets/icon_512.png','assets'),
        ('styles.py',          '.'),
        ('components.py',      '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'backend.login_backend',
        'backend.admin_dashboard_backend',
        'backend.becario_dashboard_backend',
        'backend.registrar_prestamo_backend',
        'backend.registrar_devolucion_backend',
        'backend.consulta_inventario_backend',
        'backend.historial_prestamos_backend',
        'backend.gestion_estudiantes_backend',
        'backend.gestion_usuarios_backend',
        'backend.gestion_materiales_backend',
        'backend.exportar_historial_backend',
        'backend.configuracion_backend',
        'openpyxl',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL', 'cv2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── macOS: bundle .app ────────────────────────────────────────
if sys.platform == 'darwin':
    icon_file = 'assets/icon.icns'  # generado por build_macos.sh
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name='LabManager',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        icon=icon_file,
    )
    coll = COLLECT(
        exe, a.binaries, a.zipfiles, a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='LabManager',
    )
    app = BUNDLE(
        coll,
        name='LabManager.app',
        icon=icon_file,
        bundle_identifier='mx.unam.labfisica.labmanager',
        info_plist={
            'CFBundleName': 'Lab Manager',
            'CFBundleDisplayName': 'Lab Manager',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleDocumentTypes': [],
        },
    )

# ── Windows: .exe en carpeta dist/ ───────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='LabManager',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,          # Sin ventana de consola negra
        disable_windowed_traceback=False,
        icon='assets\\icon.ico',
    )
