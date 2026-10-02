@echo off
REM ============================================================
REM  build_windows.bat — Genera LabManager.exe para Windows
REM  Ejecutar desde la carpeta LABFIS_FIXED13\
REM  Doble clic o desde CMD/PowerShell
REM ============================================================

echo.
echo ╔══════════════════════════════════════════╗
echo ║   Lab Manager — Build Windows            ║
echo ╚══════════════════════════════════════════╝
echo.

REM 1. Entorno virtual
if not exist ".venv" (
    echo ► Creando entorno virtual...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo ► Python: 
python --version

REM 2. Dependencias
echo ► Instalando dependencias...
pip install --upgrade pip -q
pip install PySide6 pyinstaller openpyxl reportlab -q
echo   OK Dependencias instaladas

REM 3. Limpiar builds anteriores
if exist "build" rmdir /s /q build
if exist "dist"  rmdir /s /q dist

REM 4. Compilar
echo ► Compilando con PyInstaller...
pyinstaller --clean labmanager.spec

REM 5. Verificar
if exist "dist\LabManager.exe" (
    echo.
    echo ╔══════════════════════════════════════════╗
    echo ║  OK  BUILD EXITOSO                       ║
    echo ║                                          ║
    echo ║  Archivo:  dist\LabManager.exe           ║
    echo ║                                          ║
    echo ║  Para instalar:                          ║
    echo ║  Copia LabManager.exe a donde quieras   ║
    echo ║  y crea un acceso directo en Escritorio  ║
    echo ╚══════════════════════════════════════════╝
) else (
    echo ERROR: no se genero dist\LabManager.exe
    pause
    exit /b 1
)

pause
