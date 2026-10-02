import os
import csv
from backend import data_manager as dm
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from io import StringIO, BytesIO

class ExportType(Enum):
    ALL = "all"
    DATE_RANGE = "date"
    BY_STUDENT = "student"
    BY_MATERIAL = "material"

class ExportFormat(Enum):
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"

@dataclass
class LoanHistoryRecord:
    """Data class."""

    loan_id: str
    student_name: str
    student_id: str
    material_code: str
    material_name: str
    loan_date: str
    return_date: Optional[str]
    status: str
    days_borrowed: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_list(self) -> List[Any]:
        return [
            self.loan_id,
            self.student_name,
            self.student_id,
            self.material_code,
            self.material_name,
            self.loan_date,
            self.return_date or "",
            self.status,
            str(self.days_borrowed)
        ]

@dataclass
class ExportOptions:
    """Data class."""

    export_type: ExportType = ExportType.ALL
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    student_name: Optional[str] = None
    material_name: Optional[str] = None    # búsqueda por nombre
    material_code: Optional[str] = None    # búsqueda por código
    format: ExportFormat = ExportFormat.EXCEL

class ExportarHistorialBackend:


    def __init__(self):
        self.export_options = ExportOptions()

    def _load_history(self) -> 'List[LoanHistoryRecord]':
        """Lee el historial de préstamos desde data_manager."""
        from datetime import datetime as _dt
        records = []
        for p in dm.get_all_prestamos():
            try:
                loan_date_str = str(p.get('loan_date', '') or '')
                return_date   = str(p.get('return_date', '') or '') or None
                # Calcular días
                try:
                    ld = _dt.strptime(loan_date_str[:10], '%Y-%m-%d')
                    if return_date:
                        rd = _dt.strptime(return_date[:10], '%Y-%m-%d')
                        days = (rd - ld).days
                    else:
                        days = (_dt.now() - ld).days
                except Exception:
                    days = 0
                records.append(LoanHistoryRecord(
                    loan_id       = str(p.get('loan_id', '')),
                    student_name  = str(p.get('student_name', '')),
                    student_id    = str(p.get('student_id', '')),
                    material_code = str(p.get('material_code', '')),
                    material_name = str(p.get('material_name', '')),
                    loan_date     = loan_date_str,
                    return_date   = return_date,
                    status        = str(p.get('status', 'Activo')),
                    days_borrowed = max(0, days),
                ))
            except Exception as e:
                print(f"[ExportarHistorial] Error cargando préstamo: {e}")
        return records

    def get_all_history(self) -> List[LoanHistoryRecord]:
        return self._load_history()

    def get_filtered_history(self, options: Optional[ExportOptions] = None) -> List[LoanHistoryRecord]:

        if options is None:
            options = self.export_options

        filtered = self._load_history()

        # Filtrar por tipo de exportación
        if options.export_type == ExportType.DATE_RANGE:
            filtered = self._filter_by_date_range(filtered, options.start_date, options.end_date)
        elif options.export_type == ExportType.BY_STUDENT and options.student_name:
            filtered = self._filter_by_student(filtered, options.student_name)
        elif options.export_type == ExportType.BY_MATERIAL:
            query = options.material_code or options.material_name or ""
            if query:
                filtered = self._filter_by_material(filtered, query)

        return filtered

    def _filter_by_date_range(self, records: List[LoanHistoryRecord],
                               start_date: Optional[str],
                               end_date: Optional[str]) -> List[LoanHistoryRecord]:
        if not start_date and not end_date:
            return records

        filtered = []
        for record in records:
            loan_date_obj = datetime.strptime(record.loan_date.split()[0], "%Y-%m-%d")

            if start_date:
                start_obj = datetime.strptime(start_date, "%Y-%m-%d")
                if loan_date_obj < start_obj:
                    continue

            if end_date:
                end_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if loan_date_obj > end_obj:
                    continue

            filtered.append(record)

        return filtered

    def _filter_by_student(self, records: List[LoanHistoryRecord], student_name: str) -> List[LoanHistoryRecord]:
        student_lower = student_name.lower()
        return [r for r in records if student_lower in r.student_name.lower()]

    def _filter_by_material(self, records: List[LoanHistoryRecord], material_query: str) -> List[LoanHistoryRecord]:
        """Filtra por código de material (exacto, sin mayúsculas) o por nombre (parcial)."""
        q = material_query.strip().upper()
        # Primero intentar coincidencia exacta de código
        exact = [r for r in records if r.material_code.upper() == q]
        if exact:
            return exact
        # Luego búsqueda parcial en código
        by_code = [r for r in records if q in r.material_code.upper()]
        if by_code:
            return by_code
        # Fallback: búsqueda parcial en nombre
        q_lower = material_query.strip().lower()
        return [r for r in records if q_lower in r.material_name.lower()]

    def get_table_headers(self) -> List[str]:

        return [
            "ID Préstamo", "Estudiante", "ID Estudiante",
            "Código Material", "Material", "Fecha Préstamo",
            "Fecha Devolución", "Estado", "Días en Préstamo"
        ]

    def export_to_excel(self, records: List[LoanHistoryRecord], file_path: str) -> Tuple[bool, str]:

        try:
            # Intentar usar pandas si está disponible
            try:
                import pandas as pd
                df = self._create_dataframe(records)
                df.to_excel(file_path, index=False, engine='openpyxl')
                return True, f"Archivo Excel guardado en: {file_path}"
            except ImportError:
                # Fallback a CSV si pandas no está disponible
                return self.export_to_csv(records, file_path.replace('.xlsx', '.csv'))
        except Exception as e:
            return False, f"Error al exportar a Excel: {str(e)}"

    def export_to_csv(self, records: List[LoanHistoryRecord], file_path: str) -> Tuple[bool, str]:

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # Escribir encabezados
                writer.writerow(self.get_table_headers())

                # Escribir datos
                for record in records:
                    writer.writerow(record.to_list())

            return True, f"Archivo CSV guardado en: {file_path}"
        except Exception as e:
            return False, f"Error al exportar a CSV: {str(e)}"

    def export_to_json(self, records: List[LoanHistoryRecord], file_path: str) -> Tuple[bool, str]:

        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'total_records': len(records),
                'records': [record.to_dict() for record in records]
            }

            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)

            return True, f"Archivo JSON guardado en: {file_path}"
        except Exception as e:
            return False, f"Error al exportar a JSON: {str(e)}"

    def export_to_pdf(self, records: List[LoanHistoryRecord], file_path: str) -> Tuple[bool, str]:

        try:
            # Verificar si reportlab está disponible
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import landscape, letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
            except ImportError:
                return False, "ReportLab no está instalado. Instálalo con: pip install reportlab"

            doc = SimpleDocTemplate(file_path, pagesize=landscape(letter))
            elements = []

            # Título
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=1,  # Centrado
                spaceAfter=30
            )
            title = Paragraph(f"Reporte de Historial de Préstamos", title_style)
            elements.append(title)

            # Fecha de exportación
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=2  # Derecha
            )
            date_text = Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
            elements.append(date_text)
            elements.append(Spacer(1, 0.2 * inch))

            # Datos de la tabla
            headers = self.get_table_headers()
            data = [headers]
            for record in records[:100]:  # Limitar a 100 registros para PDF
                data.append(record.to_list())

            # Crear tabla
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))

            elements.append(table)
            doc.build(elements)

            return True, f"Archivo PDF guardado en: {file_path}"
        except Exception as e:
            return False, f"Error al exportar a PDF: {str(e)}"

    def _create_dataframe(self, records: List[LoanHistoryRecord]):
        try:
            import pandas as pd
            data = [record.to_dict() for record in records]
            return pd.DataFrame(data)
        except ImportError:
            raise ImportError("pandas no está instalado")

    def get_students_list(self) -> List[str]:

        students = sorted(set(r.student_name for r in self._load_history()))
        return students

    def get_materials_list(self) -> List[str]:

        materials = sorted(set(r.material_name for r in self._load_history()))
        return materials

    def get_statistics(self, records: List[LoanHistoryRecord]) -> Dict[str, Any]:

        if not records:
            return {
                'total_loans': 0,
                'active_loans': 0,
                'returned_loans': 0,
                'overdue_loans': 0,
                'avg_days_borrowed': 0,
                'unique_students': 0,
                'unique_materials': 0
            }

        total = len(records)
        active = sum(1 for r in records if r.status == "Activo")
        returned = sum(1 for r in records if r.status == "Devuelto")
        overdue = sum(1 for r in records if r.status == "Vencido")
        avg_days = sum(r.days_borrowed for r in records) / total
        unique_students = len(set(r.student_name for r in records))
        unique_materials = len(set(r.material_name for r in records))

        return {
            'total_loans': total,
            'active_loans': active,
            'returned_loans': returned,
            'overdue_loans': overdue,
            'avg_days_borrowed': round(avg_days, 1),
            'unique_students': unique_students,
            'unique_materials': unique_materials
        }

    def preview_export(self, options: ExportOptions) -> Tuple[List[LoanHistoryRecord], Dict[str, Any]]:

        records = self.get_filtered_history(options)
        stats = self.get_statistics(records)
        return records, stats

    def perform_export(self, options: ExportOptions, file_path: str) -> Tuple[bool, str]:

        # Obtener datos filtrados
        records = self.get_filtered_history(options)

        if not records:
            return False, "No hay datos que coincidan con los filtros seleccionados"

        # Exportar según formato
        if options.format == ExportFormat.CSV:
            return self.export_to_csv(records, file_path)
        elif options.format == ExportFormat.JSON:
            return self.export_to_json(records, file_path)
        elif options.format == ExportFormat.PDF:
            return self.export_to_pdf(records, file_path)
        else:  # Excel por defecto
            return self.export_to_excel(records, file_path)

    def get_available_formats(self) -> List[Tuple[str, str]]:

        formats = [
            (ExportFormat.EXCEL.value, " Excel (.xlsx)"),
            (ExportFormat.CSV.value, "📄 CSV (.csv)"),
            (ExportFormat.JSON.value, "🔧 JSON (.json)"),
            (ExportFormat.PDF.value, "📑 PDF (.pdf)"),
        ]
        return formats

    def validate_date_range(self, start_date: str, end_date: str) -> Tuple[bool, str]:

        if not start_date or not end_date:
            return False, "Debe seleccionar ambas fechas"

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            if start > end:
                return False, "La fecha inicial no puede ser mayor que la final"

            if end > datetime.now():
                return False, "La fecha final no puede ser futura"

            return True, "Rango válido"
        except ValueError:
            return False, "Formato de fecha inválido"

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_export_backend() -> ExportarHistorialBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = ExportarHistorialBackend()
    return _backend_instance