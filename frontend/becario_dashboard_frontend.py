from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from components import StatCard, SectionHeader, CardWidget, LabTable, status_badge
from styles import COLORS

# Importar el backend
from backend.becario_dashboard_backend import get_becario_backend, LoanStatus

class BecarioDashboard(QScrollArea):
    """
    Vista principal del Dashboard del Becario

    Muestra estadísticas clave, préstamos recientes y permite gestionar
    las operaciones básicas del laboratorio.
    """

    # Señales para comunicación con otros componentes
    loan_returned = Signal(str)  # Emitida cuando se devuelve un préstamo
    loan_created = Signal(object)  # Emitida cuando se crea un préstamo

    def __init__(self):
        """Inicializa el dashboard y configura la interfaz"""
        super().__init__()

        # Inicializar backend
        self.backend = get_becario_backend()

        # Referencias a widgets dinámicos
        self.recent_loans_table = None
        self.stats_cards = []

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_data()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background: {COLORS['background']};")
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['background']};")
        self.setWidget(container)
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 28, 32, 28)
        self.main_layout.setSpacing(24)
        self._add_header()
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(16)
        self.main_layout.addLayout(self.stats_layout)
        self._add_recent_loans_section()
        # No addStretch — table expands to fill

    def _add_header(self):
        """Agrega el encabezado del dashboard"""
        header = SectionHeader(
            "Dashboard — Becario",
            "Resumen de actividad del laboratorio"
        )
        self.main_layout.addWidget(header)

    def _add_recent_loans_section(self):
        """Agrega la sección de préstamos recientes con tabla"""
        # Crear tarjeta contenedora
        card = CardWidget("Préstamos Recientes")
        headers = self.backend.get_table_headers()
        self.recent_loans_table = LabTable(headers)
        self.recent_loans_table.setMinimumHeight(300)
        self.recent_loans_table.setSizePolicy(
            self.recent_loans_table.sizePolicy().horizontalPolicy(),
            __import__('PySide6.QtWidgets', fromlist=['QSizePolicy']).QSizePolicy.Expanding
        )
        card.add_widget(self.recent_loans_table)
        self.main_layout.addWidget(card, 1)  # stretch=1 fills remaining space

    def _add_action_buttons(self):
        """Agrega botones de acción adicionales"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # Botón para refrescar datos
        refresh_btn = QPushButton(" Refrescar Datos")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_dashboard)
        button_layout.addWidget(refresh_btn)

        # Botón para exportar reporte (ejemplo)
        export_btn = QPushButton(" Exportar Reporte")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['stat_green']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['stat_green_dark']};
            }}
        """)
        export_btn.clicked.connect(self._export_report)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()
        self.main_layout.addLayout(button_layout)

    def _load_data(self):
        """Carga y muestra todos los datos en la interfaz"""
        # Cargar estadísticas
        self._load_stats()

        # Cargar tabla de préstamos
        self._load_loans_table()

    def _load_stats(self):
        """Carga las tarjetas de estadísticas"""
        # Limpiar estadísticas existentes
        self._clear_stats()

        # Obtener datos del backend
        stats_data = self.backend.get_dashboard_stats()

        # Crear nuevas tarjetas
        for label, value, color_key in stats_data:
            color = COLORS.get(color_key, COLORS['primary'])
            stat_card = StatCard(label, value, color)
            self.stats_layout.addWidget(stat_card)
            self.stats_cards.append(stat_card)

    def _load_loans_table(self):
        """Carga los datos de préstamos en la tabla"""
        if not self.recent_loans_table:
            return

        # Obtener préstamos del backend
        loans = self.backend.get_recent_loans()

        # Configurar filas de la tabla
        self.recent_loans_table.setRowCount(len(loans))

        for i, loan in enumerate(loans):
            # Agregar ID (monoespaciado)
            self.recent_loans_table.add_item(i, 0, loan.loan_id, mono=True)

            # Agregar nombre del estudiante
            self.recent_loans_table.add_item(i, 1, loan.student_name)

            # Agregar nombre del material
            self.recent_loans_table.add_item(i, 2, loan.material_name)

            # Agregar fecha/hora formateada
            formatted_date = loan.get_formatted_date()
            self.recent_loans_table.add_item(i, 3, formatted_date)

            # Agregar badge de estado
            status_text = loan.status.value
            self.recent_loans_table.set_badge_item(i, 4, status_text)

    def _clear_stats(self):
        """Limpia las tarjetas de estadísticas existentes"""
        for card in self.stats_cards:
            card.deleteLater()
        self.stats_cards.clear()

        # Limpiar el layout
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh_dashboard(self):
        """
        Refresca todos los datos del dashboard
        Método público que puede ser llamado para actualizar la vista
        """
        try:
            # Refrescar datos del backend
            self.backend.refresh_data()

            # Recargar interfaz
            self._load_data()

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "Actualizado",
                "Los datos del dashboard han sido actualizados correctamente."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al actualizar los datos: {str(e)}"
            )

    def return_loan_by_id(self, loan_id: str) -> bool:
        """
        Marca un préstamo como devuelto

        Args:
            loan_id (str): ID del préstamo a devolver

        Returns:
            bool: True si se devolvió exitosamente
        """
        success, message = self.backend.return_loan(loan_id)

        if success:
            # Actualizar la interfaz
            self.refresh_dashboard()

            # Emitir señal
            self.loan_returned.emit(loan_id)

            # Mostrar mensaje
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)

        return success

    def search_loans(self, search_term: str):
        """
        Busca préstamos por término de búsqueda

        Args:
            search_term (str): Término a buscar
        """
        if not search_term:
            # Si no hay término, mostrar todos
            self._load_loans_table()
            return

        # Buscar en el backend
        results = self.backend.search_loans(search_term)

        # Actualizar tabla con resultados
        if self.recent_loans_table:
            self.recent_loans_table.setRowCount(len(results))

            for i, loan in enumerate(results):
                self.recent_loans_table.add_item(i, 0, loan.loan_id, mono=True)
                self.recent_loans_table.add_item(i, 1, loan.student_name)
                self.recent_loans_table.add_item(i, 2, loan.material_name)

                formatted_date = loan.get_formatted_date()
                self.recent_loans_table.add_item(i, 3, formatted_date)

                status_text = loan.status.value
                self.recent_loans_table.set_badge_item(i, 4, status_text)

    def _export_report(self):
        """Exporta un reporte de préstamos (ejemplo)"""
        stats_summary = self.backend.get_statistics_summary()
        loans = self.backend.get_recent_loans(limit=50)

        # Crear contenido del reporte
        report_content = f"""
        REPORTE DE PRÉSTAMOS - LABORATORIO
        ===================================
        Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        ESTADÍSTICAS:
        - Total préstamos: {stats_summary['total_loans']}
        - Préstamos activos: {self.backend.get_active_loans_count()}
        - Préstamos vencidos: {self.backend.get_overdue_loans_count()}
        - Préstamos hoy: {stats_summary['today_loans']}

        MATERIAL MÁS SOLICITADO: {self.backend.get_dashboard_stats()[2][1]}

        PRÉSTAMOS RECIENTES:
        {self._format_loans_for_report(loans)}
        """

        # Mostrar diálogo con el reporte (simulación)
        QMessageBox.information(
            self,
            "Reporte Generado",
            "El reporte ha sido generado. En producción se guardaría en un archivo."
        )

        # En producción, aquí se guardaría el archivo
        print(report_content)

    def _format_loans_for_report(self, loans) -> str:
        """Formatea los préstamos para el reporte"""
        if not loans:
            return "No hay préstamos registrados."

        lines = []
        for loan in loans[:10]:  # Mostrar solo últimos 10
            lines.append(
                f"  {loan.loan_id}: {loan.student_name} - {loan.material_name} "
                f"({loan.status.value}) - {loan.get_formatted_date()}"
            )

        return "\n".join(lines)


    def refresh_page(self):
        if hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()
        self._clear_stats()
        self._load_stats()
        self._load_loans_table()
