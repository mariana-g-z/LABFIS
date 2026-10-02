from datetime import datetime, date, timedelta
from backend import data_manager as dm
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

class LoanStatus(Enum):
    ACTIVE = "Activo"
    RETURNED = "Devuelto"
    OVERDUE = "Vencido"
    LOST = "Perdido"
    RESERVED = "Reservado"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [status.value for status in cls]

    @classmethod
    def get_filter_options(cls) -> List[str]:
        return ["Todos los estados"] + cls.get_all_values()

@dataclass
class LoanRecord:
    """Data class."""

    loan_id: str
    student_name: str
    student_id: str
    becario_name: str
    material_name: str
    material_code: str
    quantity: int
    loan_date: str
    return_date: Optional[str]
    status: LoanStatus
    due_date: str
    days_overdue: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoanRecord':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = LoanStatus(data['status'])
        return cls(**data)

    def get_status_display(self) -> str:
        return self.status.value

    def is_active(self) -> bool:
        return self.status == LoanStatus.ACTIVE

    def is_overdue(self) -> bool:
        return self.status == LoanStatus.OVERDUE

    def calculate_days_overdue(self) -> int:
        if self.status != LoanStatus.OVERDUE and self.status != LoanStatus.ACTIVE:
            return 0

        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d")
            today = datetime.now()
            if today > due:
                return (today - due).days
        except ValueError:
            pass
        return 0

    def get_formatted_loan_date(self) -> str:
        try:
            dt = datetime.strptime(self.loan_date, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return self.loan_date

    def get_formatted_return_date(self) -> str:
        if not self.return_date:
            return "—"
        try:
            dt = datetime.strptime(self.return_date, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return self.return_date

@dataclass
class FilterCriteria:
    """Data class."""

    search_text: str = ""
    status: str = "Todos los estados"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def is_active(self) -> bool:
        return (bool(self.search_text) or
                self.status != "Todos los estados" or
                self.start_date or
                self.end_date)

class HistorialPrestamosBackend:


    def __init__(self):
        self._loan_records = []
        self._current_filters = FilterCriteria()
        self._loaded = False
        dm.register_reload_callback(self.reload)

    def get_table_headers(self) -> List[str]:
        return [
            "ID Préstamo",
            "Estudiante",
            "Becario",
            "Material",
            "Cantidad",
            "Fecha Préstamo",
            "Fecha Devolución",
            "Estado",
        ]

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_from_file()

    def _load_from_file(self):
        """Carga historial de préstamos desde data_manager."""
        from datetime import datetime as _dt
        self._loan_records = []
        for p in dm.get_all_prestamos():
            try:
                status_str = str(p.get('status', 'Activo'))
                try:
                    status = LoanStatus(status_str)
                except ValueError:
                    status = LoanStatus.ACTIVE

                loan_date_str  = str(p.get('loan_date', '') or '')
                return_date_str = str(p.get('return_date', '') or '') or None
                due_date_str   = str(p.get('due_date', '') or '')

                days_overdue = 0
                if status == LoanStatus.OVERDUE or (status == LoanStatus.ACTIVE and due_date_str):
                    try:
                        due = _dt.strptime(due_date_str[:10], '%Y-%m-%d')
                        days_overdue = max(0, (_dt.now() - due).days)
                    except Exception:
                        days_overdue = 0

                self._loan_records.append(LoanRecord(
                    loan_id       = str(p.get('loan_id', '')),
                    student_name  = str(p.get('student_name', '')),
                    student_id    = str(p.get('student_id', '')),
                    becario_name  = str(p.get('becario', '') or ''),
                    material_name = str(p.get('material_name', '')),
                    material_code = str(p.get('material_code', '')),
                    quantity      = int(p.get('quantity', 1) or 1),
                    loan_date     = loan_date_str,
                    return_date   = return_date_str,
                    status        = status,
                    due_date      = due_date_str,
                    days_overdue  = days_overdue,
                ))
            except Exception as e:
                print(f"[HistorialBackend] Error cargando préstamo: {e}")
        self._loaded = True

    def reload(self):
        self._loaded = False
        self._loan_records = []
        self._load_from_file()

    def refresh_data(self):
        self.reload()

    def get_all_loans(self) -> List[LoanRecord]:

        self._ensure_loaded()
        return self._loan_records.copy()

    def get_filtered_loans(self, filters: Optional[FilterCriteria] = None) -> List[LoanRecord]:

        self._ensure_loaded()
        if filters is None:
            filters = self._current_filters

        filtered = self._loan_records.copy()

        # Aplicar filtro de búsqueda
        if filters.search_text:
            search_lower = filters.search_text.lower()
            filtered = [loan for loan in filtered if (
                search_lower in loan.loan_id.lower() or
                search_lower in loan.student_name.lower() or
                search_lower in loan.material_name.lower() or
                search_lower in loan.becario_name.lower()
            )]

        # Aplicar filtro de estado
        if filters.status != "Todos los estados":
            filtered = [loan for loan in filtered if loan.status.value == filters.status]

        # Aplicar filtro de rango de fechas
        if filters.start_date:
            start = datetime.strptime(filters.start_date, "%Y-%m-%d")
            filtered = [loan for loan in filtered if self._parse_date(loan.loan_date) >= start]

        if filters.end_date:
            end = datetime.strptime(filters.end_date, "%Y-%m-%d")
            filtered = [loan for loan in filtered if self._parse_date(loan.loan_date) <= end]

        # Ordenar por fecha de préstamo descendente
        filtered.sort(key=lambda x: x.loan_date, reverse=True)

        return filtered

    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        except (ValueError, IndexError):
            return datetime.now()

    def get_loan_by_id(self, loan_id: str) -> Optional[LoanRecord]:

        self._ensure_loaded()
        for loan in self._loan_records:
            if loan.loan_id == loan_id:
                return loan
        return None

    def return_loan(self, loan_id: str) -> Tuple[bool, str]:

        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return False, f"No se encontró el préstamo con ID {loan_id}"

        if loan.status == LoanStatus.RETURNED:
            return False, "Este préstamo ya fue devuelto"

        loan.status = LoanStatus.RETURNED
        loan.return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True, f"Préstamo {loan_id} devuelto exitosamente"

    def get_statistics(self, loans: Optional[List[LoanRecord]] = None) -> Dict[str, Any]:

        self._ensure_loaded()
        if loans is None:
            loans = self._loan_records

        total = len(loans)
        active = sum(1 for loan in loans if loan.status == LoanStatus.ACTIVE)
        returned = sum(1 for loan in loans if loan.status == LoanStatus.RETURNED)
        overdue = sum(1 for loan in loans if loan.status == LoanStatus.OVERDUE)

        # Materiales más prestados
        material_count = {}
        for loan in loans:
            material_count[loan.material_name] = material_count.get(loan.material_name, 0) + loan.quantity

        top_materials = sorted(material_count.items(), key=lambda x: x[1], reverse=True)[:5]

        # Estudiantes más activos
        student_count = {}
        for loan in loans:
            student_count[loan.student_name] = student_count.get(loan.student_name, 0) + 1

        top_students = sorted(student_count.items(), key=lambda x: x[1], reverse=True)[:5]

        # Becarios más activos
        becario_count = {}
        for loan in loans:
            becario_count[loan.becario_name] = becario_count.get(loan.becario_name, 0) + 1

        top_becarios = sorted(becario_count.items(), key=lambda x: x[1], reverse=True)[:3]

        # Préstamos por mes
        loans_by_month = {}
        for loan in loans:
            try:
                month = loan.loan_date[:7]  # YYYY-MM
                loans_by_month[month] = loans_by_month.get(month, 0) + loan.quantity
            except (IndexError, ValueError):
                pass

        return {
            'total': total,
            'active': active,
            'returned': returned,
            'overdue': overdue,
            'active_percentage': round(active / total * 100, 2) if total > 0 else 0,
            'returned_percentage': round(returned / total * 100, 2) if total > 0 else 0,
            'overdue_percentage': round(overdue / total * 100, 2) if total > 0 else 0,
            'top_materials': top_materials,
            'top_students': top_students,
            'top_becarios': top_becarios,
            'loans_by_month': loans_by_month,
            'total_quantity': sum(loan.quantity for loan in loans)
        }

    def get_status_options(self) -> List[str]:

        return LoanStatus.get_filter_options()

    def get_becarios_list(self) -> List[str]:

        becarios = sorted(set(loan.becario_name for loan in self._loan_records))
        return becarios

    def get_students_list(self) -> List[str]:

        students = sorted(set(loan.student_name for loan in self._loan_records))
        return students

    def get_materials_list(self) -> List[str]:

        materials = sorted(set(loan.material_name for loan in self._loan_records))
        return materials

    def search_loans(self, search_text: str) -> List[LoanRecord]:

        filters = FilterCriteria(search_text=search_text)
        return self.get_filtered_loans(filters)

    def export_loans(self, loans: List[LoanRecord], format: str = "csv") -> str:

        if format.lower() == "csv":
            return self._export_to_csv(loans)
        elif format.lower() == "json":
            return self._export_to_json(loans)
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _export_to_csv(self, loans: List[LoanRecord]) -> str:
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow([
            "ID Préstamo", "Estudiante", "Matrícula", "Becario",
            "Material", "Código Material", "Cantidad", "Fecha Préstamo",
            "Fecha Devolución", "Estado", "Fecha Límite", "Días Retraso"
        ])

        # Escribir datos
        for loan in loans:
            writer.writerow([
                loan.loan_id,
                loan.student_name,
                loan.student_id,
                loan.becario_name,
                loan.material_name,
                loan.material_code,
                loan.quantity,
                loan.get_formatted_loan_date(),
                loan.get_formatted_return_date(),
                loan.status.value,
                loan.due_date,
                loan.days_overdue
            ])

        return output.getvalue()

    def _export_to_json(self, loans: List[LoanRecord]) -> str:
        import json
        data = [loan.to_dict() for loan in loans]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_date_range_stats(self, start_date: str, end_date: str) -> Dict[str, Any]:

        filters = FilterCriteria(start_date=start_date, end_date=end_date)
        loans = self.get_filtered_loans(filters)
        return self.get_statistics(loans)

    def get_overdue_loans(self) -> List[LoanRecord]:

        self._ensure_loaded()
        return [loan for loan in self._loan_records if loan.status == LoanStatus.OVERDUE]

    def get_active_loans(self) -> List[LoanRecord]:

        self._ensure_loaded()
        return [loan for loan in self._loan_records if loan.status == LoanStatus.ACTIVE]

    def refresh_data(self) -> None:

        # Actualizar días de retraso para préstamos activos
        for loan in self._loan_records:
            if loan.status == LoanStatus.ACTIVE:
                days_overdue = loan.calculate_days_overdue()
                if days_overdue > 0:
                    loan.status = LoanStatus.OVERDUE
                    loan.days_overdue = days_overdue

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_historial_backend() -> HistorialPrestamosBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = HistorialPrestamosBackend()
    return _backend_instance