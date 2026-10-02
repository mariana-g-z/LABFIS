# Cómo generar el instalable de Lab Manager

## macOS (.app)

**Requisitos:** macOS 12+, Python 3.11+ instalado

```bash
# 1. Abre Terminal en la carpeta LABFIS_FIXED13
cd ~/Desktop/LABFIS_MANAGER

# 2. Ejecuta el script de build
bash build_macos.sh

# 3. Cuando termine, aparece dist/LabManager.app
# 4. Arrastra LabManager.app a tu carpeta /Aplicaciones
```

Eso es todo. Desde ese momento puedes abrir la app con doble clic
desde /Aplicaciones o desde el Launchpad como cualquier otra app de Mac.

---

## Windows (.exe)

**Requisitos:** Windows 10/11, Python 3.11+ instalado y en PATH

```
1. Abre la carpeta LABFIS_MANAGER en el Explorador de archivos
2. Doble clic en  build_windows.bat
3. Cuando termine, aparece dist\LabManager.exe
4. Copia LabManager.exe a donde quieras (escritorio, Archivos de programa, etc.)
5. Clic derecho → "Crear acceso directo" para ponerlo en el escritorio
```

---

## Notas importantes

- El build **debe hacerse en el sistema destino**: el .exe de Windows
  se genera en Windows, el .app de macOS se genera en macOS.
- El ejecutable resultante **incluye Python y todas las dependencias**,
  así que en la computadora donde se instale NO necesitan tener Python.
- La primera vez que se ejecuta en macOS puede tardar 2-3 segundos más
  en abrirse (es normal, macOS verifica la app).
- En macOS, si aparece el mensaje "no se puede abrir porque el desarrollador
  no está verificado", ve a  Preferencias del Sistema → Privacidad y Seguridad
  → clic en "Abrir de todas formas".

