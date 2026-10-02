#!/bin/bash
# ============================================================
#  build_macos.sh — Genera LabManager.app para macOS
#  Ejecutar desde la carpeta LABFIS_FIXED13/
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Lab Manager — Build macOS              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Buscar Python 3.11 o 3.12 (evitar 3.13/3.14 con bugs de ensurepip) ──
find_python() {
  for candidate in \
    "$HOME/.pyenv/versions/3.12.8/bin/python3" \
    "$HOME/.pyenv/versions/3.12.7/bin/python3" \
    "$HOME/.pyenv/versions/3.12.6/bin/python3" \
    "$HOME/.pyenv/versions/3.12.5/bin/python3" \
    "$HOME/.pyenv/versions/3.12.4/bin/python3" \
    "$HOME/.pyenv/versions/3.12.3/bin/python3" \
    "$HOME/.pyenv/versions/3.12.2/bin/python3" \
    "$HOME/.pyenv/versions/3.12.1/bin/python3" \
    "$HOME/.pyenv/versions/3.12.0/bin/python3" \
    "$HOME/.pyenv/versions/3.11.9/bin/python3" \
    "$HOME/.pyenv/versions/3.11.8/bin/python3" \
    "$HOME/.pyenv/versions/3.11.7/bin/python3" \
    "/usr/local/bin/python3.12" \
    "/usr/local/bin/python3.11" \
    "/opt/homebrew/bin/python3.12" \
    "/opt/homebrew/bin/python3.11" \
  ; do
    if [ -f "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done

  # Último recurso: buscar con pyenv cualquier 3.11 o 3.12
  if command -v pyenv &>/dev/null; then
    for v in $(pyenv versions --bare 2>/dev/null | grep -E '^3\.(11|12)\.' | sort -rV); do
      local p="$HOME/.pyenv/versions/$v/bin/python3"
      [ -f "$p" ] && echo "$p" && return 0
    done
  fi

  return 1
}

PYTHON=$(find_python) || {
  echo "❌  No se encontró Python 3.11 o 3.12."
  echo "    Instala con: pyenv install 3.12.8"
  exit 1
}
echo "► Usando Python: $PYTHON ($($PYTHON --version))"

# ── Entorno virtual ───────────────────────────────────────────
if [ -d ".venv" ]; then
  # Verificar que el .venv usa el Python correcto
  VENV_PY=".venv/bin/python3"
  VENV_VER=$("$VENV_PY" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
  MAJOR=$(echo "$VENV_VER" | cut -d. -f1)
  MINOR=$(echo "$VENV_VER" | cut -d. -f2)
  if [ "$MAJOR" -ne 3 ] || [ "$MINOR" -gt 12 ]; then
    echo "► .venv existente usa Python $VENV_VER (incompatible), recreando..."
    rm -rf .venv
  fi
fi

if [ ! -d ".venv" ]; then
  echo "► Creando entorno virtual con Python $($PYTHON --version)..."
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
echo "► Python activo: $(python3 --version)"

# ── Dependencias ─────────────────────────────────────────────
echo "► Instalando dependencias..."
pip install --upgrade pip -q
pip install PySide6 pyinstaller openpyxl reportlab -q
echo "  ✓ Dependencias instaladas"

# ── Generar .icns ────────────────────────────────────────────
echo "► Generando ícono .icns..."
ICONSET="assets/icon.iconset"
PNG="assets/icon_512.png"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"

sips -z 16   16   "$PNG" --out "$ICONSET/icon_16x16.png"      > /dev/null 2>&1
sips -z 32   32   "$PNG" --out "$ICONSET/icon_16x16@2x.png"   > /dev/null 2>&1
sips -z 32   32   "$PNG" --out "$ICONSET/icon_32x32.png"      > /dev/null 2>&1
sips -z 64   64   "$PNG" --out "$ICONSET/icon_32x32@2x.png"   > /dev/null 2>&1
sips -z 128  128  "$PNG" --out "$ICONSET/icon_128x128.png"    > /dev/null 2>&1
sips -z 256  256  "$PNG" --out "$ICONSET/icon_128x128@2x.png" > /dev/null 2>&1
sips -z 256  256  "$PNG" --out "$ICONSET/icon_256x256.png"    > /dev/null 2>&1
sips -z 512  512  "$PNG" --out "$ICONSET/icon_256x256@2x.png" > /dev/null 2>&1
sips -z 512  512  "$PNG" --out "$ICONSET/icon_512x512.png"    > /dev/null 2>&1
cp "$PNG"                    "$ICONSET/icon_512x512@2x.png"
iconutil -c icns "$ICONSET" -o assets/icon.icns
rm -rf "$ICONSET"
echo "  ✓ icon.icns generado"

# ── Limpiar y compilar ────────────────────────────────────────
rm -rf build/ dist/
echo "► Compilando con PyInstaller (puede tardar 1-2 minutos)..."
pyinstaller --clean labmanager.spec

# ── Resultado ────────────────────────────────────────────────
if [ -d "dist/LabManager.app" ]; then
  SIZE=$(du -sh dist/LabManager.app | cut -f1)
  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  ✅  BUILD EXITOSO                           ║"
  echo "║                                              ║"
  printf "║  Archivo:  dist/LabManager.app  (%s)   ║\n" "$SIZE"
  echo "║                                              ║"
  echo "║  Para instalar:                              ║"
  echo "║  Arrastra LabManager.app a /Aplicaciones     ║"
  echo "║                                              ║"
  echo "║  Si macOS bloquea la app la primera vez:     ║"
  echo "║  Preferencias → Privacidad → Abrir de todas  ║"
  echo "║  formas                                      ║"
  echo "╚══════════════════════════════════════════════╝"
  echo ""
  # Abrir carpeta dist en Finder
  open dist/
else
  echo "❌  Error: no se generó dist/LabManager.app"
  exit 1
fi
