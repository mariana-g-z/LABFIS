from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from backend import data_manager as dm

class PrestamoStep(Enum):
    SCAN_STUDENT = 0
    STUDENT_INFO = 1
    SCAN_MATERIAL = 2
    MATERIAL_INFO = 3
    SIGNATURE = 4
    CONFIRM = 5

@dataclass
class StudentInfo:
    student_id: str
    name: str
    career: str
    email: str
    active_loans: int
    max_loans: int = 5
    can_borrow: bool = True
    remaining_loans: int = 5

    def __post_init__(self):
        self.remaining_loans = self.max_loans - self.active_loans
        self.can_borrow = self.active_loans < self.max_loans

@dataclass
class MaterialInfo:
    code: str
    name: str
    category: str
    location: str
    available_stock: int
    control_type: str
    can_borrow: bool = True

    def __post_init__(self):
        self.can_borrow = self.available_stock > 0

@dataclass
class LoanRecord:
    loan_id: str
    student_id: str
    student_name: str
    material_code: str
    material_name: str
    quantity: int
    loan_date: str
    due_date: str
    becario_name: str
    status: str = "Activo"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'loan_id': self.loan_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'quantity': self.quantity,
            'loan_date': self.loan_date,
            'due_date': self.due_date,
            'becario_name': self.becario_name,
            'status': self.status
        }

class RegistrarPrestamoBackend:

    DEFAULT_LOAN_DAYS = 7

    def __init__(self):
        self.current_step = PrestamoStep.SCAN_STUDENT
        self.current_student: Optional[StudentInfo] = None
        self.current_material: Optional[MaterialInfo] = None
        self.current_quantity: int = 1

    # ── Búsqueda de estudiante ────────────────────────────────────────────────
    def get_student_by_id(self, student_id: str) -> Tuple[bool, str, Optional[StudentInfo]]:
        if not student_id or not student_id.strip():
            return False, "Por favor ingrese una matrícula", None

        sid = student_id.strip()
        row = dm.get_persona(sid)
        if not row:
            return False, f"No se encontró un estudiante con matrícula {sid}", None

        if str(row.get("role","")).lower() != "estudiante":
            return False, f"El usuario '{sid}' no es un estudiante", None

        if str(row.get("status","Activo")).lower() == "inactivo":
            return False, f"La cuenta del estudiante {row.get('full_name',sid)} está inactiva", None

        active_loans = int(row.get("active_loans", 0) or 0)
        student = StudentInfo(
            student_id=sid,
            name=str(row.get("full_name", sid)),
            career=str(row.get("career", "")),
            email=str(row.get("email", "")),
            active_loans=active_loans,
            max_loans=5
        )

        if not student.can_borrow:
            return False, f"El estudiante {student.name} ha alcanzado el límite de {student.max_loans} préstamos activos", student

        return True, f"Estudiante encontrado: {student.name}", student

    # ── Búsqueda de material ──────────────────────────────────────────────────
    def get_material_by_code(self, material_code: str) -> Tuple[bool, str, Optional[MaterialInfo]]:
        if not material_code or not material_code.strip():
            return False, "Por favor ingrese un código de material", None

        code = material_code.upper().strip()
        row = dm.get_material(code)
        if not row:
            return False, f"No se encontró un material con código {code}", None

        status = str(row.get("status","Activo"))
        if status.lower() != "activo":
            return False, f"El material {row.get('name',code)} no está activo (estado: {status})", None

        stock = int(row.get("stock", 0) or 0)
        material = MaterialInfo(
            code=code,
            name=str(row.get("name", "")),
            category=str(row.get("category", "")),
            location=str(row.get("description", "")),   # xlsx no tiene location separada
            available_stock=stock,
            control_type=str(row.get("control_type", "Individual"))
        )

        if not material.can_borrow:
            return False, f"El material {material.name} no tiene stock disponible", material

        return True, f"Material encontrado: {material.name}", material

    def validate_quantity(self, material: MaterialInfo, quantity: int) -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "La cantidad debe ser mayor a 0"
        if quantity > material.available_stock:
            return False, f"Cantidad no disponible. Stock actual: {material.available_stock}"
        return True, "Cantidad válida"

    # ── Verificación de firma ─────────────────────────────────────────────────
    def verify_student_password(self, student_id: str, password: str) -> Tuple[bool, str]:
        if not password:
            return False, "Por favor ingrese la contraseña"
        row = dm.get_persona(student_id)
        if not row:
            return False, "Estudiante no encontrado"
        stored_hash = str(row.get("password_hash", ""))
        if dm.verify_password(password, stored_hash):
            return True, "Firma verificada correctamente"
        # Fallback: matrícula == contraseña (primer uso)
        if password == student_id:
            return True, "Firma verificada correctamente"
        return False, "Contraseña incorrecta. No se puede autorizar el préstamo."

    # ── Resumen del préstamo ──────────────────────────────────────────────────
    def get_loan_summary(self, student: StudentInfo, materials_list: List[Tuple['MaterialInfo', int]],
                         becario_name: str) -> Dict[str, Any]:
        """materials_list: lista de (MaterialInfo, cantidad)"""
        loan_date = datetime.now()
        due_date = loan_date + timedelta(days=self.DEFAULT_LOAN_DAYS)

        # Descripción de materiales para el resumen
        if len(materials_list) == 1:
            mat, qty = materials_list[0]
            material_display = f"{mat.name} ({mat.code})"
            quantity_display = str(qty)
        else:
            material_display = f"{len(materials_list)} materiales"
            quantity_display = ", ".join(f"{m.name}×{q}" for m, q in materials_list)

        return {
            "student_id": student.student_id,
            "student_name": student.name,
            "student_career": student.career,
            "material_code": materials_list[0][0].code if len(materials_list)==1 else "MÚLTIPLE",
            "material_name": materials_list[0][0].name if len(materials_list)==1 else f"{len(materials_list)} materiales",
            "material_display": material_display,
            "quantity": quantity_display,
            "loan_date": loan_date.strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "becario_name": becario_name,
            "active_loans_after": student.active_loans + 1,
            "remaining_loans": student.remaining_loans - 1
        }

    # ── Registro del préstamo ─────────────────────────────────────────────────
    def register_loan(self, student: StudentInfo,
                      materials_list: List[Tuple['MaterialInfo', int]],
                      becario_name: str) -> Tuple[bool, str, Optional[List[LoanRecord]]]:
        """Registra uno o más materiales como un conjunto de préstamos."""
        if not student.can_borrow:
            return False, f"El estudiante {student.name} no puede realizar más préstamos", None
        if not materials_list:
            return False, "No hay materiales para registrar", None

        loans = []
        try:
            loan_date = datetime.now()
            due_date = loan_date + timedelta(days=self.DEFAULT_LOAN_DAYS)

            for material, quantity in materials_list:
                # Verificar stock actualizado
                row = dm.get_material(material.code)
                current_stock = int(row.get("stock", 0) or 0) if row else 0
                if quantity > current_stock:
                    return False, f"Sin stock para {material.name}. Disponible: {current_stock}", None

                loan_id = dm.get_next_loan_id()
                loan = LoanRecord(
                    loan_id=loan_id,
                    student_id=student.student_id,
                    student_name=student.name,
                    material_code=material.code,
                    material_name=material.name,
                    quantity=quantity,
                    loan_date=loan_date.strftime("%Y-%m-%d %H:%M:%S"),
                    due_date=due_date.strftime("%Y-%m-%d %H:%M"),
                    becario_name=becario_name,
                    status="Activo"
                )

                # Guardar préstamo
                dm.save_prestamo({
                    "loan_id": loan_id,
                    "student_id": student.student_id,
                    "student_name": student.name,
                    "material_code": material.code,
                    "material_name": material.name,
                    "quantity": quantity,
                    "loan_date": loan.loan_date,
                    "due_date": loan.due_date,
                    "return_date": "",
                    "status": "Activo",
                    "becario": becario_name,
                })

                # Actualizar stock del material
                if row:
                    row["stock"] = current_stock - quantity
                    dm.save_material(row)

                loans.append(loan)

            # Actualizar préstamos activos del estudiante
            p_row = dm.get_persona(student.student_id)
            if p_row:
                p_row["active_loans"] = int(p_row.get("active_loans", 0) or 0) + len(materials_list)
                dm.save_persona(p_row)

            ids = ", ".join(l.loan_id for l in loans)
            return True, f"Préstamo(s) {ids} registrado(s) exitosamente", loans

        except Exception as e:
            return False, f"Error al registrar préstamo: {str(e)}", None

    # ── Compat: versión de un solo material (usado en algunos frontends) ──────
    def register_loan_single(self, student: StudentInfo, material: MaterialInfo,
                             quantity: int, becario_name: str) -> Tuple[bool, str, Optional[LoanRecord]]:
        ok, msg, loans = self.register_loan(student, [(material, quantity)], becario_name)
        return ok, msg, (loans[0] if loans else None)

    # ── Otros métodos de consulta ─────────────────────────────────────────────
    def get_student_loans(self, student_id: str) -> List[Dict]:
        return [p for p in dm.get_all_prestamos() if str(p.get("student_id","")) == student_id]

    def get_material_loans(self, material_code: str) -> List[Dict]:
        return [p for p in dm.get_all_prestamos() if str(p.get("material_code","")).upper() == material_code.upper()]

    def get_becario_list(self) -> List[str]:
        usuarios = dm.get_usuarios_sistema()
        return [u.get("full_name", u.get("username","")) for u in usuarios if str(u.get("role","")).lower() == "becario"]

    def get_available_materials(self) -> List[MaterialInfo]:
        result = []
        for row in dm.get_all_materiales():
            if str(row.get("status","")).lower() == "activo":
                stock = int(row.get("stock", 0) or 0)
                if stock > 0:
                    result.append(MaterialInfo(
                        code=str(row.get("code","")),
                        name=str(row.get("name","")),
                        category=str(row.get("category","")),
                        location=str(row.get("description","")),
                        available_stock=stock,
                        control_type=str(row.get("control_type","Individual"))
                    ))
        return result

    def check_student_eligibility(self, student_id: str) -> Tuple[bool, str, Optional[StudentInfo]]:
        return self.get_student_by_id(student_id)

    def reset_process(self):
        self.current_step = PrestamoStep.SCAN_STUDENT
        self.current_student = None
        self.current_material = None
        self.current_quantity = 1

    def get_current_step_info(self) -> Dict[str, Any]:
        steps_info = {
            0: {"name": "Escanear Estudiante",        "description": "Identificar al estudiante"},
            1: {"name": "Información del Estudiante", "description": "Verificar datos del estudiante"},
            2: {"name": "Escanear Material",          "description": "Identificar el material"},
            3: {"name": "Información del Material",   "description": "Verificar disponibilidad"},
            4: {"name": "Firma Digital",              "description": "Autorización del estudiante"},
            5: {"name": "Confirmar Préstamo",         "description": "Revisar y confirmar"}
        }
        idx = self.current_step.value if hasattr(self.current_step, 'value') else self.current_step
        return steps_info.get(idx, {"name": "Desconocido", "description": ""})

# Singleton
_backend_instance = None

def get_prestamo_backend() -> RegistrarPrestamoBackend:
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = RegistrarPrestamoBackend()
    return _backend_instance
