from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QDateEdit, QMessageBox, QFileDialog,
    QTabWidget, QGridLayout, QProgressDialog, QHeaderView
)
from datetime import datetime, timedelta
from components import SectionHeader, LabTable, SearchBar
from styles import COLORS

# Importar el backend
from backend.historial_prestamos_backend import (
    get_historial_backend, FilterCriteria, LoanStatus
)

class HistorialPrestamosPage(QWidget):
    """
    Página de Historial de Préstamos

    Permite consultar el registro completo de préstamos con filtros
    avanzados y opciones de exportación.
    """

    # Señales para comunicación
    loan_selected = Signal(str)  # Emitida cuando se selecciona un préstamo
    export_completed = Signal(str)  # Emitida cuando se completa exportación

    def __init__(self):
        """Inicializa la página de historial de préstamos"""
        super().__init__()

        # Inicializar backend
        self.backend = get_historial_backend()

        # Referencias a widgets
        self.search_bar = None
        self.status_combo = None
        self.date_from = None
        self.date_to = None
        self.history_table = None
        self.footer_label = None

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_history()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Botón de exportar
        export_btn = self._create_export_button()

        # Agregar encabezado con botón
        header = SectionHeader(
            "Historial de Préstamos",
            "Consulta el registro completo de préstamos",
            export_btn
        )
        main_layout.addWidget(header)

        # Crear pestañas
        self.tab_widget = QTabWidget()

        # Pestaña de historial
        history_tab = self._create_history_tab()
        self.tab_widget.addTab(history_tab, "  Historial")

        main_layout.addWidget(self.tab_widget, 1)

    def _create_export_button(self) -> QPushButton:
        """Crea el botón de exportar"""
        btn = QPushButton("⬇  Exportar")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS.get('primary_hover', '#3b82f6')};
            }}
        """)
        btn.clicked.connect(self._export_data)
        return btn

    def _create_history_tab(self) -> QWidget:
        """Crea la pestaña de historial con filtros y tabla"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Tarjeta de filtros
        filter_card = self._create_filter_card()
        layout.addWidget(filter_card)

        # Tabla de historial
        self.history_table = self._create_history_table()

        # Footer
        self.footer_label = QLabel()
        self.footer_label.setStyleSheet(f"color: {COLORS['muted_fg']}; padding: 8px 16px; border: none;")

        # Contenedor de la tabla
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self.history_table)
        table_layout.addWidget(self.footer_label)

        layout.addWidget(table_container, 1)

        return tab

    def _create_filter_card(self) -> QFrame:
        """Crea la tarjeta de filtros"""
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        filters_layout = QHBoxLayout(filter_card)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(12)

        # Barra de búsqueda
        self.search_bar = SearchBar("Buscar por ID, estudiante o material...")
        self.search_bar.textChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.search_bar, 2)

        # Combo de estado
        self.status_combo = QComboBox()
        status_options = self.backend.get_status_options()
        self.status_combo.addItems(status_options)
        self.status_combo.setFixedHeight(44)
        self.status_combo.setMinimumWidth(180)
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.status_combo, 1)

        # Fecha desde
        self.date_from = QDateEdit()
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedHeight(44)
        self.date_from.setMinimumWidth(130)
        self.date_from.setStyleSheet(self._date_style())
        self.date_from.dateChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.date_from)

        # Fecha hasta
        self.date_to = QDateEdit()
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedHeight(44)
        self.date_to.setMinimumWidth(130)
        self.date_to.setStyleSheet(self._date_style())
        self.date_to.dateChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.date_to)

        # Botón limpiar filtros
        clear_btn = QPushButton("Limpiar")
        clear_btn.setFixedHeight(44)
        clear_btn.setStyleSheet(self._clear_style())
        clear_btn.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_btn)

        return filter_card

    def _create_history_table(self) -> LabTable:
        """Crea la tabla de historial de préstamos"""
        headers = self.backend.get_table_headers()
        table = LabTable(headers)

        # Custom column widths: fecha columns wider, cantidad smaller
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        # Set after show: ID, Estudiante, Becario, Material, Cantidad, Fecha Préstamo, Fecha Devolución, Estado
        table.setColumnWidth(0, 90)   # ID
        table.setColumnWidth(1, 160)  # Estudiante
        table.setColumnWidth(2, 140)  # Becario
        table.setColumnWidth(3, 160)  # Material
        table.setColumnWidth(4, 70)   # Cantidad (más pequeña)
        table.setColumnWidth(5, 175)  # Fecha Préstamo (más grande)
        table.setColumnWidth(6, 175)  # Fecha Devolución (más grande)

        # Conectar señal de clic
        table.clicked.connect(self._on_table_click)

        return table

    def _create_stats_tab(self) -> QWidget:
        """Crea la pestaña de estadísticas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Frame principal
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(20)

        # Título
        title = QLabel("Estadísticas de Préstamos")
        title.setStyleSheet("font-size: 16px; font-weight: 700; border: none;")
        stats_layout.addWidget(title)

        # Grid de estadísticas principales
        main_grid = QGridLayout()
        main_grid.setSpacing(15)

        self.stats_labels = {}
        stats_items = [
            ("Total Préstamos:", "total"),
            ("Préstamos Activos:", "active"),
            ("Devueltos:", "returned"),
            ("Vencidos:", "overdue"),
            ("Total Unidades Prestadas:", "total_quantity"),
            ("Tasa de Actividad:", "active_percentage"),
        ]

        for i, (label, key) in enumerate(stats_items):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['muted_fg']};")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("font-weight: 600; font-size: 14px; border: none;")
            main_grid.addWidget(lbl, i, 0)
            main_grid.addWidget(value_lbl, i, 1)
            self.stats_labels[key] = value_lbl

        stats_layout.addLayout(main_grid)

        # Sección de Top Materiales
        top_label = QLabel("[MAT] Materiales más prestados")
        top_label.setStyleSheet("font-weight: 600; margin-top: 10px; border: none;")
        stats_layout.addWidget(top_label)

        self.top_materials_list = QLabel()
        self.top_materials_list.setStyleSheet(f"color: {COLORS['muted_fg']}; padding: 10px; border: none;")
        stats_layout.addWidget(self.top_materials_list)

        # Sección de Top Estudiantes
        students_label = QLabel(" Estudiantes más activos")
        students_label.setStyleSheet("font-weight: 600; margin-top: 10px; border: none;")
        stats_layout.addWidget(students_label)

        self.top_students_list = QLabel()
        self.top_students_list.setStyleSheet(f"color: {COLORS['muted_fg']}; padding: 10px; border: none;")
        stats_layout.addWidget(self.top_students_list)

        # Sección de Top Becarios
        becarios_label = QLabel(" Becarios más activos")
        becarios_label.setStyleSheet("font-weight: 600; margin-top: 10px; border: none;")
        stats_layout.addWidget(becarios_label)

        self.top_becarios_list = QLabel()
        self.top_becarios_list.setStyleSheet(f"color: {COLORS['muted_fg']}; padding: 10px; border: none;")
        stats_layout.addWidget(self.top_becarios_list)

        layout.addWidget(stats_frame)

        # Botón refrescar
        refresh_btn = QPushButton(" Actualizar Estadísticas")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
        """)
        refresh_btn.clicked.connect(self._load_statistics)
        layout.addWidget(refresh_btn)

        # Cargar estadísticas
        self._load_statistics()

        return tab

    def _create_overdue_tab(self) -> QWidget:
        """Crea la pestaña de préstamos vencidos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabla de vencidos
        headers = ["ID", "Estudiante", "Material", "Fecha Préstamo", "Fecha Límite", "Días Retraso", "Acciones"]
        self.overdue_table = LabTable(headers)

        # Contenedor
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.overdue_table)

        layout.addWidget(container)

        # Botón refrescar
        refresh_btn = QPushButton(" Refrescar")
        refresh_btn.setFixedHeight(35)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 5px 15px;
            }}
        """)
        refresh_btn.clicked.connect(self._load_overdue_loans)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        # Cargar vencidos
        self._load_overdue_loans()

        return tab

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """

    def _date_style(self) -> str:
        return f"""
            QDateEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """

    def _clear_style(self) -> str:
        return f"""
            QPushButton {{
                background: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: #e2e8f0;
            }}
        """

    def _get_current_filters(self) -> FilterCriteria:
        """Obtiene los filtros actuales de la UI"""
        return FilterCriteria(
            search_text=self.search_bar.text(),
            status=self.status_combo.currentText(),
            start_date=self.date_from.date().toString("yyyy-MM-dd"),
            end_date=self.date_to.date().toString("yyyy-MM-dd")
        )

    def _on_filter_changed(self):
        """Manejador de cambios en los filtros"""
        self._load_history()

    def _clear_filters(self):
        """Limpia todos los filtros"""
        self.search_bar.clear()
        self.status_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())

    def _load_history(self):
        """Carga el historial de préstamos en la tabla"""
        filters = self._get_current_filters()
        loans = self.backend.get_filtered_loans(filters)
        all_loans = self.backend.get_all_loans()

        # Configurar la tabla
        self.history_table.setRowCount(len(loans))

        for i, loan in enumerate(loans):
            # ID
            self.history_table.add_item(i, 0, loan.loan_id, mono=True)

            # Estudiante
            self.history_table.add_item(i, 1, loan.student_name)

            # Becario
            self.history_table.add_item(i, 2, loan.becario_name)

            # Material
            self.history_table.add_item(i, 3, loan.material_name)

            # Cantidad
            self.history_table.add_item(i, 4, str(loan.quantity))

            # Fecha Préstamo
            self.history_table.add_item(i, 5, loan.get_formatted_loan_date())

            # Fecha Devolución
            self.history_table.add_item(i, 6, loan.get_formatted_return_date())

            # Estado (con badge)
            status_text = loan.get_status_display()
            self.history_table.set_badge_item(i, 7, status_text)

        # Actualizar footer
        showing_count = len(loans)
        total_count = len(all_loans)
        self.footer_label.setText(
            f"Mostrando <b>{showing_count}</b> de <b>{total_count}</b> registros"
        )

    def _load_statistics(self):
        """Carga las estadísticas en la pestaña correspondiente"""
        stats = self.backend.get_statistics()

        # Actualizar valores principales
        self.stats_labels['total'].setText(str(stats['total']))
        self.stats_labels['active'].setText(str(stats['active']))
        self.stats_labels['returned'].setText(str(stats['returned']))
        self.stats_labels['overdue'].setText(str(stats['overdue']))
        self.stats_labels['total_quantity'].setText(str(stats['total_quantity']))
        self.stats_labels['active_percentage'].setText(f"{stats['active_percentage']}%")

        # Top materiales
        top_materials_text = ""
        for material, count in stats['top_materials']:
            top_materials_text += f"• {material}: {count} préstamos<br>"
        self.top_materials_list.setText(top_materials_text or "No hay datos")

        # Top estudiantes
        top_students_text = ""
        for student, count in stats['top_students']:
            top_students_text += f"• {student}: {count} préstamos<br>"
        self.top_students_list.setText(top_students_text or "No hay datos")

        # Top becarios
        top_becarios_text = ""
        for becario, count in stats['top_becarios']:
            top_becarios_text += f"• {becario}: {count} préstamos<br>"
        self.top_becarios_list.setText(top_becarios_text or "No hay datos")

    def _load_overdue_loans(self):
        """Carga los préstamos vencidos en la tabla"""
        overdue_loans = self.backend.get_overdue_loans()

        self.overdue_table.setRowCount(len(overdue_loans))

        for i, loan in enumerate(overdue_loans):
            # ID
            self.overdue_table.add_item(i, 0, loan.loan_id, mono=True)

            # Estudiante
            self.overdue_table.add_item(i, 1, loan.student_name)

            # Material
            self.overdue_table.add_item(i, 2, loan.material_name)

            # Fecha Préstamo
            self.overdue_table.add_item(i, 3, loan.get_formatted_loan_date())

            # Fecha Límite
            self.overdue_table.add_item(i, 4, loan.due_date)

            # Días Retraso
            days_text = f"[!] {loan.days_overdue} días"
            self.overdue_table.add_item(i, 5, days_text)

            # Acciones
            actions = [("Marcar Devolución", lambda l=loan: self._mark_returned(l), False)]
            self.overdue_table.add_actions(i, 6, actions)

    def _on_table_click(self, index):
        """Manejador de clic en la tabla"""
        if index.isValid():
            row = index.row()
            loan_id_item = self.history_table.item(row, 0)
            if loan_id_item:
                self.loan_selected.emit(loan_id_item.text())

    def _mark_returned(self, loan):
        """Marca un préstamo como devuelto"""
        reply = QMessageBox.question(
            self,
            "Confirmar Devolución",
            f"¿Confirmas la devolución del material '{loan.material_name}' "
            f"para el estudiante {loan.student_name}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.backend.return_loan(loan.loan_id)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_history()
                self._load_statistics()
                self._load_overdue_loans()
            else:
                QMessageBox.critical(self, "Error", message)

    def _export_data(self):
        """Exporta los datos del historial"""
        # Obtener datos a exportar
        filters = self._get_current_filters()
        loans = self.backend.get_filtered_loans(filters)

        if not loans:
            QMessageBox.warning(self, "Exportar", "No hay datos para exportar con los filtros actuales")
            return

        # Diálogo para elegir formato
        export_dialog = QMessageBox(self)
        export_dialog.setWindowTitle("Exportar Historial")
        export_dialog.setText("Selecciona el formato de exportación:")
        csv_btn = export_dialog.addButton("CSV", QMessageBox.ActionRole)
        json_btn = export_dialog.addButton("JSON", QMessageBox.ActionRole)
        cancel_btn = export_dialog.addButton("Cancelar", QMessageBox.RejectRole)

        export_dialog.exec()

        format_type = None
        if export_dialog.clickedButton() == csv_btn:
            format_type = "csv"
            file_filter = "CSV Files (*.csv)"
            extension = "csv"
        elif export_dialog.clickedButton() == json_btn:
            format_type = "json"
            file_filter = "JSON Files (*.json)"
            extension = "json"
        else:
            return

        # Guardar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Historial",
            f"historial_prestamos_{timestamp}.{extension}",
            file_filter
        )

        if file_path:
            progress = QProgressDialog("Exportando datos...", "Cancelar", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            try:
                export_data = self.backend.export_loans(loans, format_type)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_data)

                progress.close()

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Se exportaron {len(loans)} registros a:\n{file_path}"
                )
                self.export_completed.emit(file_path)

            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")

    def refresh_history(self):
        """Refresca todo el historial"""
        self.backend.refresh_data()
        self._load_history()
        self._load_statistics()
        self._load_overdue_loans()

    def filter_by_status(self, status: str):
        """Filtra por estado específico"""
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def filter_by_date_range(self, start_date: QDate, end_date: QDate):
        """Filtra por rango de fechas"""
        self.date_from.setDate(start_date)
        self.date_to.setDate(end_date)
    def refresh_page(self):
        if hasattr(self.backend, 'reload'):
            self.backend.reload()
        elif hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()
        self._load_history()
