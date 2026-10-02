from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class DevolucionStep(Enum):
    SCAN_STUDENT = 0
    SELECT_LOAN = 1
    SCAN_MATERIAL = 2
    SIGNATURE = 3
    CONFIRM = 4

@dataclass
class ActiveLoan:
    """Data class."""

    loan_id: str
    material_code: str
    material_name: str
    quantity: int
    loan_date: str
    due_date: str
    is_overdue: bool = False
    days_overdue: int = 0

    def __post_init__(self):
        if not self.is_overdue and self.days_overdue > 0:
            self.is_overdue = True

@dataclass
class StudentInfo:
    """Data class."""

    student_id: str
    name: str
    career: str
    email: str
    active_loans_count: int

@dataclass
class DevolucionRecord:
    """Data class."""

    devolution_id: str
    loan_id: str
    student_id: str
    student_name: str
    material_code: str
    material_name: str
    quantity: int
    devolution_date: str
    becario_name: str
    signature_verified: bool = True
    condition_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'devolution_id': self.devolution_id,
            'loan_id': self.loan_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'quantity': self.quantity,
            'devolution_date': self.devolution_date,
            'becario_name': self.becario_name,
            'signature_verified': self.signature_verified,
            'condition_notes': self.condition_notes
        }

class RegistrarDevolucionBackend:


    def __init__(self):
        self._initialize_mock_data()
        self.current_step = DevolucionStep.SCAN_STUDENT
        self.current_student: Optional[StudentInfo] = None
        self.selected_loan: Optional[ActiveLoan] = None
        self.verified_material_code: Optional[str] = None

    def _initialize_mock_data(self):

        # Estudiantes
        self._students = {
            "2024001": StudentInfo(
                student_id="2024001",
                name="Juan Pérez García",
                career="Ingeniería Física",
                email="juan.perez@ejemplo.com",
                active_loans_count=3
            ),
            "2024002": StudentInfo(
                student_id="2024002",
                name="María García López",
                career="Ingeniería Física",
                email="maria.garcia@ejemplo.com",
                active_loans_count=2
            ),
            "2024003": StudentInfo(
                student_id="2024003",
                name="Carlos López Martínez",
                career="Física",
                email="carlos.lopez@ejemplo.com",
                active_loans_count=1
            ),
            "2024004": StudentInfo(
                student_id="2024004",
                name="Ana Martínez Ruiz",
                career="Ingeniería Física",
                email="ana.martinez@ejemplo.com",
                active_loans_count=4
            ),
        }

        # Préstamos activos
        self._active_loans = {
            "2024001": [
                ActiveLoan(
                    loan_id="P001",
                    material_code="MUL-001",
                    material_name="Multímetro Digital",
                    quantity=1,
                    loan_date="2026-05-30",
                    due_date="2026-06-06",
                    is_overdue=False
                ),
                ActiveLoan(
                    loan_id="P002",
                    material_code="OSC-003",
                    material_name="Osciloscopio",
                    quantity=1,
                    loan_date="2026-06-01",
                    due_date="2026-06-08",
                    is_overdue=False
                ),
                ActiveLoan(
                    loan_id="P005",
                    material_code="PRO-015",
                    material_name="Protoboard",
                    quantity=2,
                    loan_date="2026-05-31",
                    due_date="2026-06-02",
                    is_overdue=True,
                    days_overdue=1
                ),
            ],
            "2024002": [
                ActiveLoan(
                    loan_id="P003",
                    material_code="GEN-005",
                    material_name="Generador de Funciones",
                    quantity=1,
                    loan_date="2026-06-01",
                    due_date="2026-06-08",
                    is_overdue=False
                ),
            ],
            "2024003": [
                ActiveLoan(
                    loan_id="P004",
                    material_code="FUE-008",
                    material_name="Fuente de Poder",
                    quantity=1,
                    loan_date="2026-06-01",
                    due_date="2026-06-08",
                    is_overdue=False
                ),
            ],
            "2024004": [
                ActiveLoan(
                    loan_id="P006",
                    material_code="RES-100",
                    material_name="Resistencias (pack)",
                    quantity=1,
                    loan_date="2026-06-01",
                    due_date="2026-06-08",
                    is_overdue=False
                ),
                ActiveLoan(
                    loan_id="P007",
                    material_code="CAB-400",
                    material_name="Cables Banana",
                    quantity=5,
                    loan_date="2026-06-01",
                    due_date="2026-06-08",
                    is_overdue=False
                ),
            ],
        }

        # Materiales (para validación)
        self._materials = {
            "MUL-001": {"name": "Multímetro Digital", "category": "Instrumentos"},
            "OSC-003": {"name": "Osciloscopio", "category": "Instrumentos"},
            "GEN-005": {"name": "Generador de Funciones", "category": "Instrumentos"},
            "FUE-008": {"name": "Fuente de Poder", "category": "Instrumentos"},
            "PRO-015": {"name": "Protoboard", "category": "Componentes"},
            "RES-100": {"name": "Resistencias (pack)", "category": "Componentes"},
            "CAB-400": {"name": "Cables Banana", "category": "Accesorios"},
            "PIN-500": {"name": "Pinzas Caimán", "category": "Accesorios"},
        }

        # Historial de devoluciones
        self._devolutions: List[DevolucionRecord] = []

    def get_student_by_id(self, student_id: str) -> Tuple[bool, str, Optional[StudentInfo]]:

        if not student_id or not student_id.strip():
            return False, "Por favor ingrese una matrícula", None

        student = self._students.get(student_id)

        if not student:
            return False, f"No se encontró un estudiante con matrícula {student_id}", None

        return True, f"Estudiante encontrado: {student.name}", student

    def get_active_loans(self, student_id: str) -> List[ActiveLoan]:

        loans = self._active_loans.get(student_id, [])

        # Actualizar estado de vencidos
        for loan in loans:
            if not loan.is_overdue:
                try:
                    due_date = datetime.strptime(loan.due_date, "%Y-%m-%d")
                    if datetime.now() > due_date:
                        loan.is_overdue = True
                        loan.days_overdue = (datetime.now() - due_date).days
                except ValueError:
                    pass

        return loans

    def validate_material_for_loan(self, material_code: str, loan: ActiveLoan) -> Tuple[bool, str]:

        if not material_code or not material_code.strip():
            return False, "Por favor ingrese un código de material"

        material_code = material_code.upper().strip()

        # Verificar que el material existe
        material = self._materials.get(material_code)
        if not material:
            return False, f"Material no encontrado: {material_code}"

        # Verificar que coincide con el préstamo
        if material_code != loan.material_code:
            return False, f"El material escaneado no corresponde al préstamo seleccionado.\n\nEsperado: {loan.material_code} - {loan.material_name}\nEscaneado: {material_code} - {material['name']}"

        return True, f"Material verificado: {material['name']}"

    def verify_student_password(self, student_id: str, password: str) -> Tuple[bool, str]:

        # En producción, esto verificaría contra la base de datos
        # Por ahora, usamos una contraseña por defecto

        if not password:
            return False, "Por favor ingrese la contraseña"

        # Mock: la contraseña por defecto es la matrícula
        if password == student_id:
            return True, "Firma verificada correctamente"

        return False, "Contraseña incorrecta. No se puede verificar la firma."

    def register_devolution(self, loan: ActiveLoan, student: StudentInfo,
                            becario_name: str, condition_notes: str = "") -> Tuple[bool, str, Optional[DevolucionRecord]]:

        try:
            # Generar ID de devolución
            devolution_id = f"DEV_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Crear registro
            devolution = DevolucionRecord(
                devolution_id=devolution_id,
                loan_id=loan.loan_id,
                student_id=student.student_id,
                student_name=student.name,
                material_code=loan.material_code,
                material_name=loan.material_name,
                quantity=loan.quantity,
                devolution_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                becario_name=becario_name,
                signature_verified=True,
                condition_notes=condition_notes
            )

            # Guardar en historial
            self._devolutions.append(devolution)

            # Remover préstamo de activos
            if student.student_id in self._active_loans:
                self._active_loans[student.student_id] = [
                    l for l in self._active_loans[student.student_id]
                    if l.loan_id != loan.loan_id
                ]

            # Actualizar contador de préstamos activos del estudiante
            student.active_loans_count = len(self._active_loans.get(student.student_id, []))

            return True, f"Devolución registrada exitosamente para {loan.material_name}", devolution

        except Exception as e:
            return False, f"Error al registrar devolución: {str(e)}", None

    def get_devolution_summary(self, student: StudentInfo, loan: ActiveLoan,
                                becario_name: str) -> Dict[str, Any]:

        return {
            "student_id": student.student_id,
            "student_name": student.name,
            "student_career": student.career,
            "material_code": loan.material_code,
            "material_name": loan.material_name,
            "quantity": loan.quantity,
            "loan_date": loan.loan_date,
            "due_date": loan.due_date,
            "is_overdue": loan.is_overdue,
            "days_overdue": loan.days_overdue,
            "becario_name": becario_name,
            "devolution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def check_overdue_fines(self, loan: ActiveLoan) -> Tuple[float, str]:

        if not loan.is_overdue or loan.days_overdue <= 0:
            return 0.0, "Sin multas por retraso"

        # Calcular multa (ejemplo: $5 por día)
        fine_per_day = 5.0
        total_fine = loan.days_overdue * fine_per_day

        message = f"Material devuelto con {loan.days_overdue} días de retraso. Multa: ${total_fine:.2f}"

        return total_fine, message

    def get_becario_list(self) -> List[str]:
        # En producción, esto vendría de la base de datos
        return ["María López", "Carlos Ramírez", "Ana Torres"]

    def get_devolucion_history(self, student_id: str = None, limit: int = 50) -> List[DevolucionRecord]:

        devolutions = self._devolutions.copy()

        if student_id:
            devolutions = [d for d in devolutions if d.student_id == student_id]

        # Ordenar por fecha descendente
        devolutions.sort(key=lambda x: x.devolution_date, reverse=True)

        return devolutions[:limit]

    def get_material_condition_options(self) -> List[str]:
        return [
            "Buen estado",
            "Leve desgaste",
            "Daño menor",
            "Requiere mantenimiento",
            "Dañado (reportar)"
        ]

    def reset_process(self):
        self.current_step = DevolucionStep.SCAN_STUDENT
        self.current_student = None
        self.selected_loan = None
        self.verified_material_code = None

    def get_current_step_info(self) -> Dict[str, Any]:
        steps_info = {
            0: {"name": "Escanear Estudiante", "description": "Identificar al estudiante"},
            1: {"name": "Seleccionar Préstamo", "description": "Elegir qué material devuelve"},
            2: {"name": "Escanear Material", "description": "Verificar el material"},
            3: {"name": "Firma Digital", "description": "Validar identidad del estudiante"},
            4: {"name": "Confirmar", "description": "Revisar y confirmar"}
        }

        step_index = self.current_step.value if hasattr(self.current_step, 'value') else self.current_step
        return steps_info.get(step_index, {"name": "Desconocido", "description": ""})

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_devolucion_backend() -> RegistrarDevolucionBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = RegistrarDevolucionBackend()
    return _backend_instance