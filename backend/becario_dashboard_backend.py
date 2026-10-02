from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from backend import data_manager as dm

class LoanStatus(Enum):
    ACTIVE   = "Activo"
    RETURNED = "Devuelto"
    OVERDUE  = "Vencido"

@dataclass
class LoanRecord:
    loan_id:       str
    student_name:  str
    material_name: str
    date_time:     str
    status:        LoanStatus

    def get_formatted_date(self) -> str:
        try:
            dt = datetime.fromisoformat(self.date_time)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return self.date_time

    def is_overdue(self) -> bool:
        return self.status == LoanStatus.OVERDUE

    def can_be_returned(self) -> bool:
        return self.status in (LoanStatus.ACTIVE, LoanStatus.OVERDUE)

@dataclass
class BecarioDashboardStats:
    active_loans:            int
    daily_loans:             int
    most_requested_material: str
    overdue_loans:           int

class BecarioDashboardBackend:

    _table_headers = ["ID", "Estudiante", "Material", "Fecha/Hora", "Estado"]

    def __init__(self):
        dm.register_reload_callback(self.refresh_data)

    def _load_loans(self) -> List[LoanRecord]:
        today  = datetime.now().strftime("%Y-%m-%d")
        result = []
        for p in dm.get_all_prestamos():
            status_str = str(p.get("status","Activo"))
            try:
                status = LoanStatus(status_str)
            except ValueError:
                status = LoanStatus.ACTIVE
            # Recalcular vencidos al vuelo
            if status == LoanStatus.ACTIVE:
                due = str(p.get("due_date","") or "")
                if due and due[:10] < today:
                    status = LoanStatus.OVERDUE
            result.append(LoanRecord(
                loan_id       = str(p.get("loan_id","")),
                student_name  = str(p.get("student_name","")),
                material_name = str(p.get("material_name","")),
                date_time     = str(p.get("loan_date","") or ""),
                status        = status,
            ))
        # Más recientes primero
        result.sort(key=lambda r: r.date_time, reverse=True)
        return result

    def _compute_stats(self) -> BecarioDashboardStats:
        today  = datetime.now().strftime("%Y-%m-%d")
        loans  = self._load_loans()
        active  = [l for l in loans if l.status in (LoanStatus.ACTIVE, LoanStatus.OVERDUE)]
        daily   = [l for l in loans if l.date_time.startswith(today)]
        overdue = [l for l in loans if l.status == LoanStatus.OVERDUE]
        counts: Dict[str,int] = {}
        for l in loans:
            counts[l.material_name] = counts.get(l.material_name, 0) + 1
        top = max(counts, key=counts.get) if counts else "—"
        return BecarioDashboardStats(
            active_loans            = len(active),
            daily_loans             = len(daily),
            most_requested_material = top,
            overdue_loans           = len(overdue),
        )

    def get_dashboard_stats(self) -> List[Tuple[str, str, str]]:
        s = self._compute_stats()
        return [
            ("Préstamos Activos",  str(s.active_loans),  "stat_blue"),
            ("Préstamos del Día",  str(s.daily_loans),   "stat_green"),
            ("Materiales en Uso",  str(s.active_loans),  "stat_purple"),
            ("Préstamos Vencidos", str(s.overdue_loans), "stat_red"),
        ]

    def get_recent_loans(self, limit: Optional[int] = None) -> List[LoanRecord]:
        loans = self._load_loans()
        return loans[:limit] if limit else loans

    def get_table_headers(self) -> List[str]:
        return list(self._table_headers)

    def get_loan_by_id(self, loan_id: str) -> Optional[LoanRecord]:
        for l in self._load_loans():
            if l.loan_id == loan_id:
                return l
        return None

    def search_loans(self, search_term: str) -> List[LoanRecord]:
        q = search_term.lower()
        return [l for l in self._load_loans()
                if q in l.student_name.lower()
                or q in l.material_name.lower()
                or q in l.loan_id.lower()]

    def get_active_loans_count(self) -> int:
        return self._compute_stats().active_loans

    def get_overdue_loans_count(self) -> int:
        return self._compute_stats().overdue_loans

    def get_statistics_summary(self) -> Dict:
        loans   = self._load_loans()
        total   = len(loans)
        active  = sum(1 for l in loans if l.status == LoanStatus.ACTIVE)
        returned= sum(1 for l in loans if l.status == LoanStatus.RETURNED)
        overdue = sum(1 for l in loans if l.status == LoanStatus.OVERDUE)
        return {
            "total_loans":         total,
            "active_percentage":   (active   / total * 100) if total else 0,
            "returned_percentage": (returned / total * 100) if total else 0,
            "overdue_percentage":  (overdue  / total * 100) if total else 0,
            "today_loans":         self._compute_stats().daily_loans,
        }

    def refresh_data(self) -> None:
        pass   # datos siempre frescos desde dm

_backend_instance = None

def get_becario_backend() -> BecarioDashboardBackend:
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = BecarioDashboardBackend()
    return _backend_instance
