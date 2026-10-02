import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from backend import data_manager as dm

class BackupFrequency(Enum):
    HOURLY  = "Cada hora"
    DAILY   = "Diario"
    WEEKLY  = "Semanal"
    MONTHLY = "Mensual"

DEFAULT_PERSONAS   = "personas.xlsx"
DEFAULT_MATERIALES = "materiales.xlsx"
DEFAULT_PRESTAMOS  = "prestamos.xlsx"
DEFAULT_BAJAS      = "bajas.xlsx"

@dataclass
class FileConfig:
    personas_path:   str = "personas.xlsx"
    materiales_path: str = "materiales.xlsx"
    prestamos_path:  str = "prestamos.xlsx"
    bajas_path:      str = "bajas.xlsx"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(
            personas_path   = d.get("personas_path",   DEFAULT_PERSONAS),
            materiales_path = d.get("materiales_path", DEFAULT_MATERIALES),
            prestamos_path  = d.get("prestamos_path",  DEFAULT_PRESTAMOS),
            bajas_path      = d.get("bajas_path",      DEFAULT_BAJAS),
        )

@dataclass
class BackupConfig:
    auto_backup:  bool             = True
    frequency:    BackupFrequency  = BackupFrequency.DAILY
    backup_path:  str              = ""
    last_backup:  Optional[str]    = None

    def to_dict(self):
        return {
            'auto_backup':  self.auto_backup,
            'frequency':    self.frequency.value,
            'backup_path':  self.backup_path,
            'last_backup':  self.last_backup,
        }

    @classmethod
    def from_dict(cls, d):
        freq = BackupFrequency(d['frequency']) if 'frequency' in d else BackupFrequency.DAILY
        return cls(
            auto_backup = d.get('auto_backup', True),
            frequency   = freq,
            backup_path = d.get('backup_path', ''),
            last_backup = d.get('last_backup'),
        )

@dataclass
class SystemInfo:
    version:        str = "1.0.0"
    database_type:  str = "Archivos Excel (.xlsx)"
    total_loans:    int = 0
    total_materials:int = 0
    total_students: int = 0
    last_backup:    str = "—"

    def get_info_items(self) -> List[Tuple[str, str]]:
        return [
            ("Versión del Sistema",  self.version),
            ("Almacenamiento",       self.database_type),
            ("Total Préstamos",      str(self.total_loans)),
            ("Total Materiales",     str(self.total_materials)),
            ("Total Estudiantes",    str(self.total_students)),
            ("Último Respaldo",      self.last_backup),
        ]

class ConfiguracionBackend:

    CONFIG_FILE = "system_config.json"

    def __init__(self):
        self.file_config   = FileConfig()
        self.backup_config = BackupConfig()
        self.system_info   = SystemInfo()
        self._load_configurations()
        # Aplicar rutas guardadas al data_manager
        self._apply_paths()

    # ── Config JSON ───────────────────────────────────────────────────────────
    def _load_configurations(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'file_config' in data:
                    self.file_config = FileConfig.from_dict(data['file_config'])
                if 'backup_config' in data:
                    self.backup_config = BackupConfig.from_dict(data['backup_config'])
            except Exception as e:
                print(f"[Config] Error al cargar: {e}")

    def _save_configurations(self) -> bool:
        try:
            data = {
                'file_config':   self.file_config.to_dict(),
                'backup_config': self.backup_config.to_dict(),
                'saved_at':      datetime.now().isoformat(),
            }
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Config] Error al guardar: {e}")
            return False

    def _apply_paths(self):
        """Actualiza data_manager con las rutas configuradas."""
        dm.set_paths(
            personas   = self.file_config.personas_path,
            materiales = self.file_config.materiales_path,
            prestamos  = self.file_config.prestamos_path,
            bajas      = self.file_config.bajas_path,
        )

    # ── API pública ───────────────────────────────────────────────────────────
    def get_file_config(self) -> FileConfig:
        return self.file_config

    def update_file_config(self, personas: str, materiales: str,
                           prestamos: str, bajas: str) -> Tuple[bool, str]:
        """Actualiza rutas (convierte a absolutas) y recarga datos."""
        def _abs(p): return os.path.abspath(p) if p and os.path.exists(p) else p
        self.file_config.personas_path   = _abs(personas)
        self.file_config.materiales_path = _abs(materiales)
        self.file_config.prestamos_path  = _abs(prestamos)
        self.file_config.bajas_path      = _abs(bajas)
        self._save_configurations()
        self._apply_paths()   # recarga automática via data_manager
        return True, "Rutas actualizadas. Datos recargados desde los nuevos archivos."

    def get_backup_config(self) -> BackupConfig:
        return self.backup_config

    def update_backup_config(self, auto_backup: bool, frequency: BackupFrequency,
                             backup_path: str) -> bool:
        self.backup_config.auto_backup = auto_backup
        self.backup_config.frequency   = frequency
        self.backup_config.backup_path = backup_path
        return self._save_configurations()

    def get_system_info(self) -> SystemInfo:
        self._refresh_system_info()
        return self.system_info

    def _refresh_system_info(self):
        try:
            self.system_info.total_loans     = len(dm.get_all_prestamos())
            self.system_info.total_materials = len(dm.get_all_materiales())
            self.system_info.total_students  = len(dm.get_estudiantes())
            if self.backup_config.last_backup:
                self.system_info.last_backup = self.backup_config.last_backup
        except Exception as e:
            print(f"[Config] Error al refrescar info: {e}")

    def create_manual_backup(self) -> Tuple[bool, str]:
        try:
            backup_dir = self.backup_config.backup_path or "backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"lab_backup_{timestamp}")
            os.makedirs(backup_path)

            for name, path in [
                ("personas.xlsx",   self.file_config.personas_path),
                ("materiales.xlsx", self.file_config.materiales_path),
                ("prestamos.xlsx",  self.file_config.prestamos_path),
                ("bajas.xlsx",      self.file_config.bajas_path),
                (self.CONFIG_FILE,  self.CONFIG_FILE),
            ]:
                if os.path.exists(path):
                    shutil.copy2(path, os.path.join(backup_path, name))

            self.backup_config.last_backup = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save_configurations()
            return True, f"Respaldo creado en: {backup_path}"
        except Exception as e:
            return False, f"Error al crear respaldo: {e}"

    def validate_file_path(self, path: str) -> Tuple[bool, str]:
        if not path:
            return False, "La ruta no puede estar vacía"
        if not os.path.exists(path):
            return False, f"Archivo no encontrado: {path}"
        if not path.lower().endswith(('.xlsx','.xls','.csv')):
            return False, "El archivo debe ser .xlsx o .csv"
        return True, "Ruta válida"

    def get_available_frequencies(self) -> List[str]:
        return [f.value for f in BackupFrequency]

    def reset_to_defaults(self) -> bool:
        self.file_config   = FileConfig()
        self.backup_config = BackupConfig()
        self._apply_paths()
        return self._save_configurations()

    # Compat con el frontend antiguo
    def validate_excel_path(self, path: str) -> Tuple[bool, str]:
        return True, "OK"   # no bloqueamos al guardar ruta

    def export_configuration(self, path: str) -> Tuple[bool, str]:
        try:
            data = {'file_config': self.file_config.to_dict(),
                    'backup_config': self.backup_config.to_dict(),
                    'exported_at': datetime.now().isoformat()}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True, f"Configuración exportada a: {path}"
        except Exception as e:
            return False, f"Error al exportar: {e}"

    def import_configuration(self, path: str) -> Tuple[bool, str]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'file_config' in data:
                self.file_config = FileConfig.from_dict(data['file_config'])
            if 'backup_config' in data:
                self.backup_config = BackupConfig.from_dict(data['backup_config'])
            self._save_configurations()
            self._apply_paths()
            return True, "Configuración importada y datos recargados."
        except Exception as e:
            return False, f"Error al importar: {e}"

_backend_instance = None

def get_config_backend() -> ConfiguracionBackend:
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = ConfiguracionBackend()
    return _backend_instance
