import hashlib
import re
from datetime import datetime
from backend import data_manager as dm
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from backend import data_manager as dm


class StudentStatus(Enum):
    ACTIVE = "Activo"
    INACTIVE = "Inactivo"
    SUSPENDED = "Suspendido"
    GRADUATED = "Graduado"

class Career(Enum):
    ENGINEERING_PHYSICS = "Ingeniería Física"
    PHYSICS = "Física"
    ELECTRICAL_ENGINEERING = "Ingeniería Eléctrica"
    MECHANICAL_ENGINEERING = "Ingeniería Mecánica"
    COMPUTER_SCIENCE = "Ciencias de la Computación"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [career.value for career in cls]

@dataclass
class Student:
    """Data class."""

    student_id: str
    name: str
    career: str
    active_loans: int
    status: StudentStatus
    email: Optional[str] = None
    phone: Optional[str] = None
    registration_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    password_hash: str = ""
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        data['status'] = StudentStatus(data['status']) if 'status' in data else StudentStatus.ACTIVE
        return cls(**data)

    def get_status_display(self) -> str:
        return self.status.value

    def is_active(self) -> bool:
        return self.status == StudentStatus.ACTIVE

    def can_borrow(self) -> bool:
        return self.status == StudentStatus.ACTIVE and self.active_loans < 5  # Máximo 5 préstamos activos

    def get_remaining_loans(self) -> int:
        if not self.can_borrow():
            return 0
        return 5 - self.active_loans

    def set_password(self, password: str) -> None:
        self.password_hash = self._hash_password(password)

    def verify_password(self, password: str) -> bool:
        return self.password_hash == self._hash_password(password)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

@dataclass
class StudentLoanHistory:
    """Data class."""

    student_id: str
    loan_id: str
    material_name: str
    loan_date: str
    return_date: Optional[str]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class GestionEstudiantesBackend:


    def __init__(self):
        dm.register_reload_callback(self.reload)  
        self._load_from_file()

    def _load_from_file(self):
        """Carga estudiantes desde data_manager (xlsx)."""
        self._students = []
        self._loan_history = {}
        for row in dm.get_estudiantes():
            try:
                status_str = str(row.get('status', 'Activo'))
                try:
                    status = StudentStatus(status_str)
                except ValueError:
                    status = StudentStatus.ACTIVE
                stu = Student(
                    student_id        = str(row.get('username', '')),
                    name              = str(row.get('full_name', '')),
                    career            = str(row.get('career', '')),
                    active_loans      = int(row.get('active_loans', 0) or 0),
                    status            = status,
                    email             = str(row.get('email', '') or ''),
                    phone             = '',
                    registration_date = str(row.get('created_at', '') or ''),
                    password_hash     = str(row.get('password_hash', '') or ''),
                    notes             = str(row.get('notes', '') or ''),
                )
                self._students.append(stu)
                self._loan_history[stu.student_id] = []
            except Exception as e:
                print(f"[GestionEstudiantes] Error cargando estudiante {row}: {e}")
        # Poblar historial desde préstamos
        for p in dm.get_all_prestamos():
            sid = str(p.get('student_id', ''))
            if sid not in self._loan_history:
                self._loan_history[sid] = []
            self._loan_history[sid].append(StudentLoanHistory(
                student_id   = sid,
                loan_id      = str(p.get('loan_id', '')),
                material_name= str(p.get('material_name', '')),
                loan_date    = str(p.get('loan_date', '')),
                return_date  = str(p.get('return_date', '')) or None,
                status       = str(p.get('status', 'Activo')),
            ))

    def reload(self):
        self._load_from_file()

    def get_table_headers(self) -> List[str]:

        return ["Matrícula", "Nombre", "Carrera", "Préstamos Activos", "Estado", "Acciones"]

    def get_all_students(self) -> List[Student]:

        return self._students.copy()

    def get_student_by_id(self, student_id: str) -> Optional[Student]:

        for student in self._students:
            if student.student_id == student_id:
                return student
        return None

    def search_students(self, search_text: str) -> List[Student]:

        if not search_text:
            return self.get_all_students()

        search_lower = search_text.lower()
        results = []
        for student in self._students:
            if (search_lower in student.student_id.lower() or
                search_lower in student.name.lower()):
                results.append(student)
        return results

    def add_student(self, student_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Student]]:

        # Validar datos requeridos
        required_fields = ['student_id', 'name', 'career', 'password']
        for field in required_fields:
            if field not in student_data or not student_data[field]:
                return False, f"El campo {field} es requerido", None

        # Validar formato de matrícula
        if not self._validate_student_id(student_data['student_id']):
            return False, "Formato de matrícula inválido (debe ser 7 dígitos numéricos)", None

        # Verificar si ya existe
        if self.get_student_by_id(student_data['student_id']):
            return False, f"Ya existe un estudiante con la matrícula {student_data['student_id']}", None

        # Crear nuevo estudiante
        try:
            new_student = Student(
                student_id=student_data['student_id'],
                name=student_data['name'],
                career=student_data['career'],
                active_loans=0,
                status=StudentStatus.ACTIVE,
                email=student_data.get('email', ''),
                phone=student_data.get('phone', ''),
                notes=student_data.get('notes', '')
            )
            new_student.set_password(student_data['password'])

            self._students.append(new_student)
            self._loan_history[new_student.student_id] = []
            dm.save_persona({
                'username': s.student_id, 'full_name': s.name,
                'role': 'Estudiante', 'career': s.career,
                'email': s.email or '', 'notes': s.notes or '',
                'status': s.status.value, 'password_hash': s.password_hash,
                'active_loans': s.active_loans,
                'created_at': s.registration_date,
            })
            return True, f"Estudiante {new_student.name} registrado exitosamente", new_student
        except Exception as e:
            return False, f"Error al registrar estudiante: {str(e)}", None

    def update_student(self, student_id: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:

        student = self.get_student_by_id(student_id)
        if not student:
            return False, f"No se encontró el estudiante con matrícula {student_id}"

        # Actualizar campos permitidos
        allowed_fields = ['name', 'career', 'email', 'phone', 'notes']
        for field in allowed_fields:
            if field in update_data:
                setattr(student, field, update_data[field])

        # Actualizar estado si viene
        if 'status' in update_data:
            try:
                new_status = StudentStatus(update_data['status'])
                student.status = new_status
            except ValueError:
                return False, f"Estado inválido: {update_data['status']}"

        # Actualizar contraseña si viene
        if 'password' in update_data and update_data['password']:
            student.set_password(update_data['password'])

        dm.save_persona({
                'username': s.student_id, 'full_name': s.name,
                'role': 'Estudiante', 'career': s.career,
                'email': s.email or '', 'notes': s.notes or '',
                'status': s.status.value, 'password_hash': s.password_hash,
                'active_loans': s.active_loans,
                'created_at': s.registration_date,
            })
        return True, f"Estudiante {student.name} actualizado exitosamente"

    def toggle_student_status(self, student_id: str) -> Tuple[bool, str]:

        student = self.get_student_by_id(student_id)
        if not student:
            return False, f"No se encontró el estudiante con matrícula {student_id}"

        if student.status == StudentStatus.ACTIVE:
            # Verificar si tiene préstamos activos
            if student.active_loans > 0:
                return False, f"No se puede desactivar al estudiante porque tiene {student.active_loans} préstamos activos"
            student.status = StudentStatus.INACTIVE
            dm.save_persona({
                'username': s.student_id, 'full_name': s.name,
                'role': 'Estudiante', 'career': s.career,
                'email': s.email or '', 'notes': s.notes or '',
                'status': s.status.value, 'password_hash': s.password_hash,
                'active_loans': s.active_loans,
                'created_at': s.registration_date,
            })
            return True, f"Estudiante {student.name} desactivado"
        else:
            student.status = StudentStatus.ACTIVE
            dm.save_persona({
                'username': s.student_id, 'full_name': s.name,
                'role': 'Estudiante', 'career': s.career,
                'email': s.email or '', 'notes': s.notes or '',
                'status': s.status.value, 'password_hash': s.password_hash,
                'active_loans': s.active_loans,
                'created_at': s.registration_date,
            })
            return True, f"Estudiante {student.name} activado"

    def delete_student(self, student_id: str) -> Tuple[bool, str]:

        student = self.get_student_by_id(student_id)
        if not student:
            return False, f"No se encontró el estudiante con matrícula {student_id}"

        # Verificar si tiene préstamos activos
        if student.active_loans > 0:
            return False, f"No se puede eliminar al estudiante porque tiene {student.active_loans} préstamos activos"

        # Soft delete - cambiar estado a graduado o inactivo
        student.status = StudentStatus.GRADUATED
        student.active_loans = 0

        return True, f"Estudiante {student.name} eliminado del sistema"

    def get_student_loan_history(self, student_id: str) -> List[StudentLoanHistory]:

        return self._loan_history.get(student_id, [])

    def add_loan_to_student(self, student_id: str, loan_data: Dict[str, Any]) -> Tuple[bool, str]:

        student = self.get_student_by_id(student_id)
        if not student:
            return False, "Estudiante no encontrado"

        if not student.can_borrow():
            return False, f"El estudiante no puede realizar más préstamos (máximo 5 activos)"

        # Crear registro de préstamo
        loan = StudentLoanHistory(
            student_id=student_id,
            loan_id=loan_data.get('loan_id', f"LOAN_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            material_name=loan_data.get('material_name', ''),
            loan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            return_date=None,
            status="Activo"
        )

        # Agregar al historial
        if student_id not in self._loan_history:
            self._loan_history[student_id] = []
        self._loan_history[student_id].insert(0, loan)

        # Actualizar contador de préstamos activos
        student.active_loans += 1

        return True, f"Préstamo registrado para {student.name}"

    def return_loan(self, student_id: str, loan_id: str) -> Tuple[bool, str]:

        student = self.get_student_by_id(student_id)
        if not student:
            return False, "Estudiante no encontrado"

        history = self._loan_history.get(student_id, [])
        for loan in history:
            if loan.loan_id == loan_id and loan.status == "Activo":
                loan.return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                loan.status = "Devuelto"
                student.active_loans = max(0, student.active_loans - 1)
                return True, f"Préstamo {loan_id} devuelto"

        return False, f"No se encontró el préstamo {loan_id}"

    def get_careers(self) -> List[str]:

        return Career.get_all_values()

    def get_statistics(self) -> Dict[str, Any]:

        total = len(self._students)
        active = sum(1 for s in self._students if s.status == StudentStatus.ACTIVE)
        inactive = sum(1 for s in self._students if s.status == StudentStatus.INACTIVE)
        graduated = sum(1 for s in self._students if s.status == StudentStatus.GRADUATED)
        total_active_loans = sum(s.active_loans for s in self._students)
        students_with_loans = sum(1 for s in self._students if s.active_loans > 0)

        # Distribución por carrera
        career_distribution = {}
        for student in self._students:
            career_distribution[student.career] = career_distribution.get(student.career, 0) + 1

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'graduated': graduated,
            'total_active_loans': total_active_loans,
            'students_with_loans': students_with_loans,
            'avg_loans_per_student': round(total_active_loans / total, 2) if total > 0 else 0,
            'career_distribution': career_distribution
        }

    def export_students(self, format: str = "csv") -> str:

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
        writer.writerow(["Matrícula", "Nombre", "Carrera", "Préstamos Activos", "Estado", "Email", "Teléfono"])

        # Escribir datos
        for student in self._students:
            writer.writerow([
                student.student_id,
                student.name,
                student.career,
                student.active_loans,
                student.status.value,
                student.email or "",
                student.phone or ""
            ])

        return output.getvalue()

    def _export_to_json(self) -> str:
        import json
        data = [student.to_dict() for student in self._students]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _validate_student_id(self, student_id: str) -> bool:

        # Formato: 7 dígitos numéricos (ej: 2024001)
        pattern = r'^\d{7}$'
        return bool(re.match(pattern, student_id))

    def refresh_data(self) -> None:

        # Simular actualización
        pass

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_students_backend() -> GestionEstudiantesBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = GestionEstudiantesBackend()
    return _backend_instance