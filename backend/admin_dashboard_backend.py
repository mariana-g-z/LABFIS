from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from backend import data_manager as dm

class TransactionType(Enum):
    LOAN   = "Préstamo"
    RETURN = "Devolución"

@dataclass
class ActivityLog:
    student_name:     str
    material_name:    str
    transaction_type: TransactionType
    time:             str
    date:             date = field(default_factory=date.today)

@dataclass
class MaterialStats:
    name:       str
    loan_count: int
    percentage: float

@dataclass
class DashboardStats:
    active_loans:         int
    total_students:       int
    available_materials:  int
    daily_loans:          int
    most_requested_material: str
    overdue_loans:        int

class AdminDashboardBackend:

    def __init__(self):
        dm.register_reload_callback(self.refresh_data)

    def _compute_stats(self) -> DashboardStats:
        today = datetime.now().strftime("%Y-%m-%d")
        prestamos = dm.get_all_prestamos()

        active  = [p for p in prestamos if str(p.get("status","")) == "Activo"]
        daily   = [p for p in active    if str(p.get("loan_date","")).startswith(today)]
        overdue = []
        for p in active:
            due = str(p.get("due_date",""))
            if due and due[:10] < today:
                overdue.append(p)

        materiales  = dm.get_all_materiales()
        estudiantes = dm.get_estudiantes()
        avail       = sum(1 for m in materiales
                         if str(m.get("status","")).lower() == "activo"
                         and int(m.get("stock", 0) or 0) > 0)

        # Material más prestado
        counts: Dict[str,int] = {}
        for p in prestamos:
            n = str(p.get("material_name",""))
            counts[n] = counts.get(n, 0) + 1
        top = max(counts, key=counts.get) if counts else "—"

        return DashboardStats(
            active_loans            = len(active),
            total_students          = len(estudiantes),
            available_materials     = avail,
            daily_loans             = len(daily),
            most_requested_material = top,
            overdue_loans           = len(overdue),
        )

    def get_dashboard_stats(self) -> List[Tuple[str, str, str]]:
        s = self._compute_stats()
        return [
            ("Préstamos Activos",      str(s.active_loans),         "stat_blue"),
            ("Total Estudiantes",      str(s.total_students),        "stat_green"),
            ("Materiales Disponibles", str(s.available_materials),   "stat_purple"),
            ("Préstamos del Día",      str(s.daily_loans),           "stat_orange"),
            ("Materiales en Uso",      str(s.active_loans),          "stat_indigo"),
            ("Préstamos Vencidos",     str(s.overdue_loans),         "stat_red"),
        ]

    def get_recent_activity(self) -> List[ActivityLog]:
        result = []
        prestamos = sorted(
            dm.get_all_prestamos(),
            key=lambda p: str(p.get("loan_date","") or ""),
            reverse=True
        )[:10]
        for p in prestamos:
            t_type = (TransactionType.RETURN
                      if str(p.get("status","")) == "Devuelto"
                      else TransactionType.LOAN)
            loan_date = str(p.get("loan_date","") or "")
            time_str  = loan_date[11:16] if len(loan_date) > 10 else ""
            result.append(ActivityLog(
                student_name     = str(p.get("student_name","")),
                material_name    = str(p.get("material_name","")),
                transaction_type = t_type,
                time             = time_str,
            ))
        return result

    def get_top_materials(self) -> List[MaterialStats]:
        counts: Dict[str,int] = {}
        for p in dm.get_all_prestamos():
            n = str(p.get("material_name",""))
            counts[n] = counts.get(n, 0) + 1
        if not counts:
            return []
        top5 = sorted(counts.items(), key=lambda x: -x[1])[:5]
        max_c = top5[0][1] if top5 else 1
        return [MaterialStats(name=n, loan_count=c,
                              percentage=round(c/max_c*100, 1))
                for n, c in top5]

    def get_material_percentage_width(self, percentage: float,
                                      max_width: int = 220) -> int:
        return int((percentage / 100) * max_width)

    def refresh_data(self) -> None:
        pass   # datos siempre frescos desde dm

_backend_instance = None

def get_admin_backend() -> AdminDashboardBackend:
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = AdminDashboardBackend()
    return _backend_instance
