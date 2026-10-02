import re
from datetime import datetime
from backend import data_manager as dm
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

class MaterialCategory(Enum):
    MEASUREMENT_INSTRUMENTS = "Instrumentos de Medición"
    ELECTRONIC_COMPONENTS = "Componentes Electrónicos"
    ACCESSORIES = "Accesorios"
    TOOLS = "Herramientas"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [cat.value for cat in cls]

class ControlType(Enum):
    INDIVIDUAL = "Individual"
    INVENTORY = "Inventario (por cantidad)"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [control.value for control in cls]

class MaterialStatus(Enum):
    ACTIVE = "Activo"
    INACTIVE = "Inactivo"
    MAINTENANCE = "En Mantenimiento"
    DISCONTINUED = "Descontinuado"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [status.value for status in cls]

@dataclass
class Material:
    """Data class."""

    code: str
    name: str
    category: str
    control_type: str
    location: str
    stock: int
    status: MaterialStatus = MaterialStatus.ACTIVE
    description: Optional[str] = None
    min_stock: int = 5
    max_stock: int = 1000
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = MaterialStatus(data['status'])
        return cls(**data)

    def get_status_display(self) -> str:
        return self.status.value

    def is_active(self) -> bool:
        return self.status == MaterialStatus.ACTIVE

    def can_borrow(self) -> bool:
        return self.is_active() and self.stock > 0

    def is_low_stock(self) -> bool:
        return self.stock <= self.min_stock

    def is_over_stock(self) -> bool:
        return self.stock >= self.max_stock

    def update_stock(self, quantity: int) -> Tuple[bool, str]:

        new_stock = self.stock + quantity

        if new_stock < 0:
            return False, f"No hay suficiente stock disponible. Stock actual: {self.stock}"

        if new_stock > self.max_stock:
            return False, f"Superaría el stock máximo permitido de {self.max_stock}"

        self.stock = new_stock
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True, f"Stock actualizado a {self.stock}"

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        if not isinstance(other, Material):
            return False
        return self.code == other.code

@dataclass
class MaterialLoanHistory:
    """Data class."""

    material_code: str
    loan_id: str
    student_name: str
    loan_date: str
    return_date: Optional[str]
    quantity: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class GestionMaterialesBackend:


    def __init__(self):
        self._materials    = []
        self._loan_history = {}
        self._loaded       = False   # carga lazy: se carga al primer acceso
        dm.register_reload_callback(self.reload)  # recargar cuando cambien rutas

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_from_file()

    def _load_from_file(self):
        """Carga materiales desde data_manager (xlsx)."""
        self._materials = []
        self._loan_history = {}
        for row in dm.get_all_materiales():
            try:
                status_str = str(row.get('status', 'Activo'))
                try:
                    status = MaterialStatus(status_str)
                except ValueError:
                    status = MaterialStatus.ACTIVE
                mat = Material(
                    code        = str(row.get('code', '')),
                    name        = str(row.get('name', '')),
                    category    = str(row.get('category', '')),
                    control_type= str(row.get('control_type', 'Individual')),
                    location    = str(row.get('description', '')),
                    stock       = int(row.get('stock', 0) or 0),
                    status      = status,
                    description = str(row.get('description', '') or ''),
                    min_stock   = 5,
                    max_stock   = 100,
                    created_at  = str(row.get('created_at', '') or ''),
                )
                self._materials.append(mat)
                # historial de préstamos del material desde prestamos xlsx
                self._loan_history[mat.code] = []
            except Exception as e:
                print(f"[GestionMateriales] Error cargando material {row}: {e}")
        # Poblar historial desde préstamos
        for p in dm.get_all_prestamos():
            code = str(p.get('material_code', '')).upper()
            if code not in self._loan_history:
                self._loan_history[code] = []
            self._loan_history[code].append(MaterialLoanHistory(
                material_code = code,
                loan_id       = str(p.get('loan_id', '')),
                student_name  = str(p.get('student_name', '')),
                loan_date     = str(p.get('loan_date', '')),
                return_date   = str(p.get('return_date', '')) or None,
                quantity      = int(p.get('quantity', 1) or 1),
                status        = str(p.get('status', 'Activo')),
            ))

        self._loaded = True   # marcar como cargado

    def reload(self):
        """Recarga desde archivo (llamar después de cambiar rutas en Configuración)."""
        self._loaded = False
        self._materials    = []
        self._loan_history = {}
        self._load_from_file()



    def get_table_headers(self) -> List[str]:

        self._ensure_loaded()
        return ["Código", "Nombre", "Categoría", "Tipo Control", "Existencias", "Estado", "Acciones"]

    def get_all_materials(self) -> List[Material]:

        self._ensure_loaded()
        return self._materials.copy()

    def get_material_by_code(self, code: str) -> Optional[Material]:

        self._ensure_loaded()
        for material in self._materials:
            if material.code == code:
                return material
        return None

    def search_materials(self, search_text: str) -> List[Material]:

        self._ensure_loaded()
        if not search_text:
            return self.get_all_materials()

        search_lower = search_text.lower()
        results = []
        for material in self._materials:
            if (search_lower in material.code.lower() or
                search_lower in material.name.lower()):
                results.append(material)
        return results

    def add_material(self, material_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Material]]:

        self._ensure_loaded()
        # Validar datos requeridos
        required_fields = ['code', 'name', 'category', 'control_type', 'location', 'stock']
        for field in required_fields:
            if field not in material_data or (field == 'stock' and material_data[field] is None):
                return False, f"El campo {field} es requerido", None

        # Validar formato de código
        if not self._validate_material_code(material_data['code']):
            return False, "Formato de código inválido (ejemplo: XXX-000)", None

        # Verificar si ya existe
        if self.get_material_by_code(material_data['code']):
            return False, f"Ya existe un material con el código {material_data['code']}", None

        # Validar stock
        try:
            stock = int(material_data['stock'])
            if stock < 0:
                return False, "El stock no puede ser negativo", None
        except (ValueError, TypeError):
            return False, "El stock debe ser un número válido", None

        # Crear nuevo material
        try:
            new_material = Material(
                code=material_data['code'],
                name=material_data['name'],
                category=material_data['category'],
                control_type=material_data['control_type'],
                location=material_data['location'],
                stock=stock,
                status=MaterialStatus.ACTIVE,
                description=material_data.get('description', ''),
                min_stock=material_data.get('min_stock', 5),
                max_stock=material_data.get('max_stock', 100)
            )

            self._materials.append(new_material)
            self._loan_history[new_material.code] = []
            # Persistir en xlsx
            dm.save_material({
                'code': new_material.code, 'name': new_material.name,
                'category': new_material.category, 'control_type': new_material.control_type,
                'stock': new_material.stock, 'status': new_material.status.value,
                'description': new_material.description or '',
                'created_at': new_material.created_at, 'folio_baja': '',
            })
            return True, f"Material {new_material.name} registrado exitosamente", new_material
        except Exception as e:
            return False, f"Error al registrar material: {str(e)}", None

    def update_material(self, code: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        material = self.get_material_by_code(code)
        if not material:
            return False, f"No se encontró el material con código {code}"

        # Actualizar campos permitidos
        allowed_fields = ['name', 'category', 'control_type', 'location',
                        'description', 'min_stock', 'max_stock']
        for field in allowed_fields:
            if field in update_data:
                setattr(material, field, update_data[field])

        if 'stock' in update_data:
            try:
                new_stock = int(update_data['stock'])
                if new_stock < 0:
                    return False, "El stock no puede ser negativo"
                material.stock = new_stock
            except (ValueError, TypeError):
                return False, "El stock debe ser un número válido"

        # Actualizar estado si viene
        if 'status' in update_data:
            try:
                new_status = MaterialStatus(update_data['status'])
                material.status = new_status
            except ValueError:
                return False, f"Estado inválido: {update_data['status']}"

        material.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dm.save_material({
            'code': material.code, 'name': material.name,
            'category': material.category, 'control_type': material.control_type,
            'stock': material.stock, 'status': material.status.value,
            'description': material.description or '',
            'created_at': material.created_at, 'folio_baja': '',
        })
        return True, f"Material {material.name} actualizado exitosamente"

    def toggle_material_status(self, code: str) -> Tuple[bool, str]:

        self._ensure_loaded()
        material = self.get_material_by_code(code)
        if not material:
            return False, f"No se encontró el material con código {code}"

        if material.status == MaterialStatus.ACTIVE:
            # Verificar si tiene préstamos activos
            active_loans = self.get_active_loans_count(code)
            if active_loans > 0:
                return False, f"No se puede desactivar el material porque tiene {active_loans} préstamos activos"
            material.status = MaterialStatus.INACTIVE
            dm.save_material({'code': material.code, 'name': material.name,
                'category': material.category, 'control_type': material.control_type,
                'stock': material.stock, 'status': 'Inactivo',
                'description': material.description or '', 'created_at': material.created_at, 'folio_baja': ''})
            return True, f"Material {material.name} desactivado"
        else:
            material.status = MaterialStatus.ACTIVE
            dm.save_material({'code': material.code, 'name': material.name,
                'category': material.category, 'control_type': material.control_type,
                'stock': material.stock, 'status': 'Activo',
                'description': material.description or '', 'created_at': material.created_at, 'folio_baja': ''})
            return True, f"Material {material.name} reactivado"

    def delete_material(self, code: str) -> Tuple[bool, str]:

        self._ensure_loaded()
        material = self.get_material_by_code(code)
        if not material:
            return False, f"No se encontró el material con código {code}"

        # Verificar si tiene préstamos activos
        active_loans = self.get_active_loans_count(code)
        if active_loans > 0:
            return False, f"No se puede eliminar el material porque tiene {active_loans} préstamos activos"

        # Eliminar material
        self._materials = [m for m in self._materials if m.code != code]
        dm.delete_material(code)

        return True, f"Material {material.name} eliminado del catálogo"

    def get_material_loan_history(self, code: str) -> List[MaterialLoanHistory]:

        self._ensure_loaded()
        return self._loan_history.get(code, [])

    def get_active_loans_count(self, code: str) -> int:

        self._ensure_loaded()
        history = self._loan_history.get(code, [])
        return sum(1 for loan in history if loan.status == "Activo")

    def add_loan_to_material(self, code: str, loan_data: Dict[str, Any]) -> Tuple[bool, str]:

        material = self.get_material_by_code(code)
        if not material:
            return False, "Material no encontrado"

        if not material.can_borrow():
            return False, "El material no está disponible para préstamo"

        # Validar cantidad para tipo inventario
        quantity = loan_data.get('quantity', 1)
        if material.control_type == ControlType.INVENTORY.value and quantity > material.stock:
            return False, f"No hay suficiente stock disponible. Stock actual: {material.stock}"

        # Crear registro de préstamo
        loan = MaterialLoanHistory(
            material_code=code,
            loan_id=loan_data.get('loan_id', f"LOAN_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            student_name=loan_data.get('student_name', ''),
            loan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            return_date=None,
            quantity=quantity,
            status="Activo"
        )

        # Agregar al historial
        if code not in self._loan_history:
            self._loan_history[code] = []
        self._loan_history[code].insert(0, loan)

        # Actualizar stock
        success, message = material.update_stock(-quantity)
        if not success:
            return False, message

        return True, f"Préstamo registrado para {material.name}"

    def return_loan(self, code: str, loan_id: str) -> Tuple[bool, str]:

        material = self.get_material_by_code(code)
        if not material:
            return False, "Material no encontrado"

        history = self._loan_history.get(code, [])
        for loan in history:
            if loan.loan_id == loan_id and loan.status == "Activo":
                loan.return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                loan.status = "Devuelto"

                # Devolver stock
                material.update_stock(loan.quantity)

                return True, f"Préstamo {loan_id} devuelto"

        return False, f"No se encontró el préstamo {loan_id}"

    def get_categories(self) -> List[str]:

        return MaterialCategory.get_all_values()

    def get_control_types(self) -> List[str]:

        return ControlType.get_all_values()

    def get_statuses(self) -> List[str]:

        return MaterialStatus.get_all_values()

    def get_statistics(self) -> Dict[str, Any]:

        total = len(self._materials)
        active = sum(1 for m in self._materials if m.status == MaterialStatus.ACTIVE)
        inactive = sum(1 for m in self._materials if m.status == MaterialStatus.INACTIVE)
        low_stock = sum(1 for m in self._materials if m.is_low_stock() and m.is_active())
        out_of_stock = sum(1 for m in self._materials if m.stock == 0)
        total_stock = sum(m.stock for m in self._materials)

        # Distribución por categoría
        category_distribution = {}
        for material in self._materials:
            category_distribution[material.category] = category_distribution.get(material.category, 0) + 1

        # Préstamos activos totales
        total_active_loans = sum(self.get_active_loans_count(m.code) for m in self._materials)

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_stock': total_stock,
            'total_active_loans': total_active_loans,
            'category_distribution': category_distribution,
            'utilization_rate': round((total_active_loans / total_stock * 100) if total_stock > 0 else 0, 2)
        }

    def get_low_stock_materials(self) -> List[Material]:

        self._ensure_loaded()
        return [m for m in self._materials if m.is_low_stock() and m.is_active()]

    def export_materials(self, format: str = "csv") -> str:

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
        writer.writerow(["Código", "Nombre", "Categoría", "Tipo Control", "Ubicación", "Stock", "Estado", "Descripción"])

        # Escribir datos
        for material in self._materials:
            writer.writerow([
                material.code,
                material.name,
                material.category,
                material.control_type,
                material.location,
                material.stock,
                material.status.value,
                material.description or ""
            ])

        return output.getvalue()

    def _export_to_json(self) -> str:
        import json
        data = [material.to_dict() for material in self._materials]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _validate_material_code(self, code: str) -> bool:

        # Formato: XXX-000 (tres letras mayúsculas, guión, tres dígitos)
        pattern = r'^[A-Z]{3}-\d{3}$'
        return bool(re.match(pattern, code))

    def get_next_available_code(self, prefix: str = "") -> str:

        if not prefix:
            prefix = "MAT"

        existing_numbers = []
        for material in self._materials:
            if material.code.startswith(prefix):
                try:
                    num = int(material.code.split('-')[1])
                    existing_numbers.append(num)
                except (IndexError, ValueError):
                    pass

        next_num = max(existing_numbers) + 1 if existing_numbers else 1
        return f"{prefix}-{next_num:03d}"

    def refresh_data(self) -> None:

        # Actualizar estados basados en stock
        for material in self._materials:
            if material.stock == 0 and material.status == MaterialStatus.ACTIVE:
                material.status = MaterialStatus.INACTIVE
            elif material.stock > 0 and material.status == MaterialStatus.INACTIVE:
                material.status = MaterialStatus.ACTIVE

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_materials_backend() -> GestionMaterialesBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = GestionMaterialesBackend()
    return _backend_instance