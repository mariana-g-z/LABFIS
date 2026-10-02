from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from backend import data_manager as dm

class MaterialCategory(Enum):
    ALL = "Todas"
    INSTRUMENTS = "Instrumentos"
    COMPONENTS = "Componentes"
    ACCESSORIES = "Accesorios"
    TOOLS = "Herramientas"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [cat.value for cat in cls]

class MaterialLocation(Enum):
    ALL = "Todas"
    SHELF_A1 = "Estante A-1"
    SHELF_A2 = "Estante A-2"
    SHELF_A3 = "Estante A-3"
    SHELF_B1 = "Estante B-1"
    DRAWER_C1 = "Cajón C-1"
    DRAWER_C5 = "Cajón C-5"
    DRAWER_D1 = "Cajón D-1"
    DRAWER_D2 = "Cajón D-2"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [loc.value for loc in cls]

class MaterialStatus(Enum):
    ALL = "Todos"
    AVAILABLE = "Disponible"
    OUT_OF_STOCK = "Agotado"
    LOW_STOCK = "Bajo Stock"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [status.value for status in cls]

    @classmethod
    def from_string(cls, status_str: str) -> 'MaterialStatus':
        for status in cls:
            if status.value == status_str:
                return status
        return cls.ALL

@dataclass
class Material:
    """Data class."""

    code: str
    name: str
    category: str
    location: str
    available_quantity: int
    borrowed_quantity: int
    status: str

    @property
    def total_quantity(self) -> int:
        return self.available_quantity + self.borrowed_quantity

    @property
    def availability_percentage(self) -> float:
        if self.total_quantity == 0:
            return 0
        return (self.available_quantity / self.total_quantity) * 100

    def update_status(self):
        if self.available_quantity <= 0:
            self.status = MaterialStatus.OUT_OF_STOCK.value
        elif self.available_quantity <= self.total_quantity * 0.2:  # 20% o menos
            self.status = MaterialStatus.LOW_STOCK.value
        else:
            self.status = MaterialStatus.AVAILABLE.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'location': self.location,
            'available_quantity': self.available_quantity,
            'borrowed_quantity': self.borrowed_quantity,
            'status': self.status,
            'total_quantity': self.total_quantity,
            'availability_percentage': self.availability_percentage
        }

@dataclass
class FilterCriteria:
    """Data class."""

    search_text: str = ""
    category: str = MaterialCategory.ALL.value
    location: str = MaterialLocation.ALL.value
    status: str = MaterialStatus.ALL.value

    def is_active(self) -> bool:
        return (bool(self.search_text) or
                self.category != MaterialCategory.ALL.value or
                self.location != MaterialLocation.ALL.value or
                self.status != MaterialStatus.ALL.value)

class ConsultaInventarioBackend:


    def __init__(self):
        dm.register_reload_callback(self.reload)
        #self._initialize_mock_data()
        self._current_filters = FilterCriteria()
        self.reload()

    def reload(self):
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        """Carga materiales desde data_manager."""
        self._materials = []
        for row in dm.get_all_materiales():
            try:
                stock = int(row.get("stock", 0) or 0)
                # No tenemos "borrowed" en el xlsx; lo calculamos
                code = str(row.get("code", "")).upper()
                borrowed = sum(
                    int(p.get("quantity", 0) or 0)
                    for p in dm.get_all_prestamos()
                    if str(p.get("material_code", "")).upper() == code
                    and str(p.get("status", "")) == "Activo"
                )
                mat = Material(
                    code=code,
                    name=str(row.get("name", "")),
                    category=str(row.get("category", "")),
                    location=str(row.get("description", "") or "—"),
                    available_quantity=stock,
                    borrowed_quantity=borrowed,
                    status="Disponible",
                )
                mat.update_status()
                self._materials.append(mat)
            except Exception as e:
                print(f"[Inventario] Error cargando {row}: {e}")

    def get_table_headers(self) -> List[str]:

        return ["Código", "Nombre", "Categoría", "Existencias", "Prestados", "Estado"]

    def get_all_materials(self) -> List[Material]:

        return self._materials.copy()

    def get_filtered_materials(self, filters: Optional[FilterCriteria] = None) -> List[Material]:

        if filters is None:
            filters = self._current_filters

        filtered = self._materials.copy()

        # Aplicar filtro de búsqueda
        if filters.search_text:
            search_lower = filters.search_text.lower()
            filtered = [m for m in filtered if
                       search_lower in m.code.lower() or
                       search_lower in m.name.lower()]

        # Aplicar filtro de categoría
        if filters.category != MaterialCategory.ALL.value:
            filtered = [m for m in filtered if m.category == filters.category]

        # Aplicar filtro de ubicación
        if filters.location != MaterialLocation.ALL.value:
            filtered = [m for m in filtered if m.location == filters.location]

        # Aplicar filtro de estado
        if filters.status != MaterialStatus.ALL.value:
            filtered = [m for m in filtered if m.status == filters.status]

        return filtered

    def get_material_by_code(self, code: str) -> Optional[Material]:

        for material in self._materials:
            if material.code == code:
                return material
        return None

    def update_material_quantity(self, code: str, borrowed_change: int) -> Tuple[bool, str]:

        material = self.get_material_by_code(code)
        if not material:
            return False, f"No se encontró el material con código {code}"

        # Validar cambio
        new_borrowed = material.borrowed_quantity + borrowed_change
        new_available = material.available_quantity - borrowed_change

        if new_borrowed < 0:
            return False, "No se puede devolver más de lo prestado"

        if new_available < 0:
            return False, "No hay suficientes existencias disponibles"

        # Actualizar cantidades
        material.borrowed_quantity = new_borrowed
        material.available_quantity = new_available
        material.update_status()

        return True, f"Material {code} actualizado correctamente"

    def get_categories(self) -> List[str]:

        return MaterialCategory.get_all_values()

    def get_locations(self) -> List[str]:

        return MaterialLocation.get_all_values()

    def get_statuses(self) -> List[str]:

        return MaterialStatus.get_all_values()

    def get_statistics(self) -> Dict[str, Any]:

        total_materials = len(self._materials)
        total_available = sum(m.available_quantity for m in self._materials)
        total_borrowed = sum(m.borrowed_quantity for m in self._materials)
        low_stock_count = sum(1 for m in self._materials if m.status == MaterialStatus.LOW_STOCK.value)
        out_of_stock_count = sum(1 for m in self._materials if m.status == MaterialStatus.OUT_OF_STOCK.value)

        # Categorías más populares
        categories_count = {}
        for material in self._materials:
            categories_count[material.category] = categories_count.get(material.category, 0) + 1

        return {
            'total_materials': total_materials,
            'total_available': total_available,
            'total_borrowed': total_borrowed,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'categories_distribution': categories_count,
            'utilization_rate': (total_borrowed / (total_available + total_borrowed) * 100) if (total_available + total_borrowed) > 0 else 0
        }

    def search_materials(self, search_text: str) -> List[Material]:

        filters = FilterCriteria(search_text=search_text)
        return self.get_filtered_materials(filters)

    def get_materials_by_category(self, category: str) -> List[Material]:

        return [m for m in self._materials if m.category == category]

    def get_materials_by_location(self, location: str) -> List[Material]:

        return [m for m in self._materials if m.location == location]

    def get_low_stock_materials(self, threshold_percentage: float = 20) -> List[Material]:

        low_stock = []
        for material in self._materials:
            if material.availability_percentage <= threshold_percentage and material.available_quantity > 0:
                low_stock.append(material)
        return low_stock

    def export_inventory(self, format: str = "csv") -> str:

        if format.lower() == "csv":
            return self._export_to_csv()
        elif format.lower() == "json":
            return self._export_to_json()
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _export_to_csv(self) -> str:
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow(["Código", "Nombre", "Categoría", "Ubicación", "Existencias", "Prestados", "Estado", "Total"])

        # Escribir datos
        for material in self._materials:
            writer.writerow([
                material.code,
                material.name,
                material.category,
                material.location,
                material.available_quantity,
                material.borrowed_quantity,
                material.status,
                material.total_quantity
            ])

        return output.getvalue()

    def _export_to_json(self) -> str:
        import json
        data = [material.to_dict() for material in self._materials]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def refresh_data(self) -> None:

        # Simular actualización de datos
        for material in self._materials:
            material.update_status()

    def add_material(self, material: Material) -> Tuple[bool, str]:

        # Verificar si ya existe
        if self.get_material_by_code(material.code):
            return False, f"Ya existe un material con el código {material.code}"

        # Validar datos
        if not material.code or not material.name:
            return False, "Código y nombre son campos requeridos"

        # Agregar material
        material.update_status()
        self._materials.append(material)

        return True, f"Material {material.code} agregado exitosamente"

    def update_material(self, code: str, updated_material: Material) -> Tuple[bool, str]:

        index = None
        for i, material in enumerate(self._materials):
            if material.code == code:
                index = i
                break

        if index is None:
            return False, f"No se encontró el material con código {code}"

        # Mantener el mismo código si no se especificó uno nuevo
        if not updated_material.code:
            updated_material.code = code

        updated_material.update_status()
        self._materials[index] = updated_material

        return True, f"Material {code} actualizado exitosamente"

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_inventory_backend() -> ConsultaInventarioBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = ConsultaInventarioBackend()
    return _backend_instance