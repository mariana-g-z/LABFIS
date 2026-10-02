from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QRadioButton, QDateEdit, QComboBox,
    QMessageBox, QFileDialog, QProgressDialog, QGroupBox,
    QLineEdit, QTextEdit, QButtonGroup
)
from datetime import datetime, date
from components import SectionHeader, CardWidget, LabTable, make_button
from styles import COLORS

# Importar el backend
from backend.exportar_historial_backend import (
    get_export_backend, ExportType, ExportFormat, ExportOptions
)

class ExportarHistorialPage(QScrollArea):
    """
    Página de Exportar Historial

    Permite exportar el historial de préstamos a diferentes formatos
    con múltiples opciones de filtrado.
    """

    # Señales para comunicación
    export_completed = Signal(str)  # Emitida cuando se completa exportación (ruta del archivo)
    export_failed = Signal(str)      # Emitida cuando falla exportación

    def __init__(self):
        """Inicializa la página de exportación"""
        super().__init__()

        # Inicializar backend
        self.backend = get_export_backend()

        # Referencias a widgets
        self.radio_buttons = {}
        self._radio_group = QButtonGroup(self)   # enforces mutual exclusivity
        self._radio_group.setExclusive(True)
        self.date_from = None
        self.date_to = None
        self.student_combo = None
        self.material_combo = None
        self.material_input = None
        self.format_combo = None
        self.preview_text = None

        # Configurar la interfaz
        self._setup_ui()

        # Configurar visibilidad de filtros
        self._update_filters_visibility()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Widget contenedor principal
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['background']};")
        self.setWidget(container)

        # Layout principal
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        # Encabezado
        self._add_header(main_layout)

      
        two_col = QHBoxLayout()
        two_col.setSpacing(20)
        two_col.setAlignment(Qt.AlignTop)

        # Columna izquierda: opciones
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        left_col.setAlignment(Qt.AlignTop)
        self._add_options_card(left_col)
        left_col.addStretch()

        left_widget = QWidget()
        left_widget.setMinimumWidth(360)
        left_widget.setMaximumWidth(460)
        left_widget.setLayout(left_col)
        two_col.addWidget(left_widget)

        # Columna derecha: previsualización
        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        right_col.setAlignment(Qt.AlignTop)
        self._add_preview_section(right_col)
        right_col.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        two_col.addWidget(right_widget, 1)

        main_layout.addLayout(two_col)
        main_layout.addStretch()

    def _add_header(self, layout: QVBoxLayout):
        """Agrega el encabezado de la página"""
        header = SectionHeader(
            "Exportar Historial",
            "Exporta el historial de préstamos a Excel con diferentes filtros"
        )
        layout.addWidget(header)

    def _add_options_card(self, layout: QVBoxLayout):
        """Agrega la tarjeta principal de opciones"""
        # Tarjeta contenedora
        card = QFrame()
        card.setMaximumWidth(800)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        # Layout de la tarjeta
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(20)

        # Título
        title = QLabel("Opciones de Exportación")
        title.setStyleSheet("font-size: 18px; font-weight: 700; border: none;")
        card_layout.addWidget(title)

        # Opciones de exportación (radio buttons)
        self._add_export_options(card_layout)

        # Filtros específicos
        self._add_filter_sections(card_layout)

        # Formato de exportación
        self._add_format_selection(card_layout)

        # Botón de exportación
        self._add_export_button(card_layout)

        # Apply initial highlight to the default selected option
        self._on_export_type_changed()

        layout.addWidget(card, alignment=Qt.AlignLeft)

    def _add_export_options(self, layout: QVBoxLayout):
        """Agrega las opciones de tipo de exportación como radio-cards."""
        options = [
            (ExportType.ALL,        "Todo el historial",     "Exportar todos los préstamos registrados"),
            (ExportType.DATE_RANGE, "Por rango de fechas",   "Filtrar por período específico"),
            (ExportType.BY_STUDENT, "Por estudiante",        "Exportar préstamos de un estudiante"),
            (ExportType.BY_MATERIAL,"Por material",          "Exportar préstamos de un material"),
        ]

        self._option_frames = {}  # export_type.value -> QFrame

        for export_type, label, desc in options:
            opt_frame = QFrame()
            opt_frame.setCursor(Qt.PointingHandCursor)
            opt_frame.setStyleSheet(self._option_frame_style(selected=False))

            opt_layout = QHBoxLayout(opt_frame)
            opt_layout.setContentsMargins(14, 12, 14, 12)
            opt_layout.setSpacing(12)

            radio = QRadioButton()
            radio.setProperty("export_type", export_type.value)
            if export_type == ExportType.ALL:
                radio.setChecked(True)
            radio.setStyleSheet(f"""
                QRadioButton::indicator {{
                    width: 17px; height: 17px;
                    border: 2px solid {COLORS['border']};
                    border-radius: 9px; background: white;
                }}
                QRadioButton::indicator:checked {{
                    background: {COLORS['primary']};
                    border-color: {COLORS['primary']};
                }}
            """)
            radio.toggled.connect(self._on_export_type_changed)
            opt_layout.addWidget(radio)
            self.radio_buttons[export_type.value] = radio
            self._radio_group.addButton(radio)   # group enforces exclusivity
            self._option_frames[export_type.value] = opt_frame

            # Make clicking anywhere on the frame toggle the radio
            radio_ref = radio
            opt_frame.mousePressEvent = lambda e, r=radio_ref: r.setChecked(True)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            title_lbl = QLabel(label)
            title_lbl.setStyleSheet("font-weight: 600; background: transparent; border: none;")
            text_col.addWidget(title_lbl)
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['muted_fg']}; font-size: 12px; background: transparent; border: none;")
            text_col.addWidget(desc_lbl)
            opt_layout.addLayout(text_col)
            opt_layout.addStretch()

            layout.addWidget(opt_frame)

    def _add_filter_sections(self, layout: QVBoxLayout):
        """Agrega las secciones de filtros específicos"""
        # Sección de rango de fechas
        self.date_frame = QFrame()
        self.date_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['muted']};
                border-radius: 6px;
            }}
        """)
        date_layout = QHBoxLayout(self.date_frame)
        date_layout.setContentsMargins(14, 10, 14, 10)
        date_layout.setSpacing(12)

        # Fecha desde
        self.date_from = QDateEdit()
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(date.today().replace(day=1))  # Primer día del mes
        self.date_from.setFixedHeight(40)
        self.date_from.setStyleSheet(f"""
            QDateEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
        """)
        date_layout.addWidget(QLabel("Desde:"))
        date_layout.addWidget(self.date_from)

        # Fecha hasta
        self.date_to = QDateEdit()
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(date.today())
        self.date_to.setFixedHeight(40)
        self.date_to.setStyleSheet(f"""
            QDateEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
        """)
        date_layout.addWidget(QLabel("Hasta:"))
        date_layout.addWidget(self.date_to)

        layout.addWidget(self.date_frame)

        # Sección de estudiante
        self.student_frame = QFrame()
        student_layout = QHBoxLayout(self.student_frame)
        student_layout.setContentsMargins(14, 10, 14, 10)

        self.student_combo = QComboBox()
        self.student_combo.setEditable(True)
        self.student_combo.addItems(self.backend.get_students_list())
        self.student_combo.setPlaceholderText("Seleccione o escriba el nombre del estudiante...")
        self.student_combo.setMinimumHeight(40)
        self.student_combo.setStyleSheet(f"""
            QComboBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
        """)
        student_layout.addWidget(QLabel("Estudiante:"))
        student_layout.addWidget(self.student_combo)

        layout.addWidget(self.student_frame)

        # Sección de material
        self.material_frame = QFrame()
        material_layout = QVBoxLayout(self.material_frame)
        material_layout.setContentsMargins(14, 10, 14, 10)
        material_layout.setSpacing(4)

        hint = QLabel("Ingresa el código (ej. MUL-001) o parte del nombre:")
        hint.setStyleSheet(f"color:{COLORS['muted_fg']};font-size:12px;border:none;")
        material_layout.addWidget(hint)

        self.material_input = QLineEdit()
        self.material_input.setPlaceholderText("Código o nombre del material…")
        self.material_input.setMinimumHeight(40)
        self.material_input.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 1.5px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        material_layout.addWidget(self.material_input)

        layout.addWidget(self.material_frame)

    def _add_format_selection(self, layout: QVBoxLayout):
        """Agrega la selección de formato de exportación"""
        format_group = QGroupBox("Formato de Exportación")
        format_group.setStyleSheet("""
            QGroupBox { font-weight: 600; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

        format_layout = QHBoxLayout()

        self.format_combo = QComboBox()
        formats = self.backend.get_available_formats()
        for value, label in formats:
            self.format_combo.addItem(label, value)
        self.format_combo.setFixedHeight(40)
        self.format_combo.setMinimumWidth(200)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

    def _add_export_button(self, layout: QVBoxLayout):
        """Agrega el botón de exportación"""
        export_btn = QPushButton("⬇  Exportar")
        export_btn.setFixedHeight(48)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS.get('primary_hover', '#3b82f6')};
            }}
        """)
        export_btn.clicked.connect(self._on_export_clicked)
        layout.addWidget(export_btn)

    def _add_preview_section(self, layout: QVBoxLayout):
        """Agrega el área de previsualización"""
        preview_card = CardWidget("Previsualización del Reporte")
        preview_layout, _ = preview_card.body_layout()

        # Texto de previsualización
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-family: monospace;
                font-size: 12px;
            }}
        """)
        preview_layout.addWidget(self.preview_text)

        # Botón de actualizar previsualización
        refresh_btn = make_button(" Actualizar Previsualización")
        refresh_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(refresh_btn)

        layout.addWidget(preview_card)

    def _option_frame_style(self, selected: bool) -> str:
        if selected:
            return f"""
                QFrame {{
                    background: {COLORS['primary_light']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 6px;
                }}
            """
        return f"""
            QFrame {{
                background: {COLORS['muted']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
            }}
        """

    def _on_export_type_changed(self):
        """Manejador de cambio en el tipo de exportación"""
        # Refresh card highlight styles
        if hasattr(self, '_option_frames'):
            for val, frame in self._option_frames.items():
                radio = self.radio_buttons.get(val)
                selected = radio is not None and radio.isChecked()
                frame.setStyleSheet(self._option_frame_style(selected=selected))
        self._update_filters_visibility()
        # Only update preview if it has been created already
        if hasattr(self, 'preview_text') and self.preview_text is not None:
            self._update_preview()

    def _update_filters_visibility(self):
        """Actualiza la visibilidad de los filtros según la selección"""
        # Obtener tipo seleccionado
        selected_type = self._get_selected_export_type()

        # Ocultar todos primero
        self.date_frame.setVisible(False)
        self.student_frame.setVisible(False)
        self.material_frame.setVisible(False)

        # Mostrar según selección
        if selected_type == ExportType.DATE_RANGE:
            self.date_frame.setVisible(True)
        if selected_type == ExportType.BY_STUDENT:
            self.student_frame.setVisible(True)
        elif selected_type == ExportType.BY_MATERIAL:
            self.material_frame.setVisible(True)

    def _get_selected_export_type(self) -> ExportType:
        """Obtiene el tipo de exportación seleccionado"""
        for radio in self.radio_buttons.values():
            if radio.isChecked():
                export_type_value = radio.property("export_type")
                return ExportType(export_type_value)
        return ExportType.ALL

    def _get_current_options(self) -> ExportOptions:
        """
        Obtiene las opciones de exportación actuales

        Returns:
            ExportOptions: Opciones configuradas
        """
        export_type = self._get_selected_export_type()

        options = ExportOptions(export_type=export_type)

        if export_type == ExportType.DATE_RANGE:
            options.start_date = self.date_from.date().toString("yyyy-MM-dd")
            options.end_date = self.date_to.date().toString("yyyy-MM-dd")
        elif export_type == ExportType.BY_STUDENT:
            options.student_name = self.student_combo.currentText()
        elif export_type == ExportType.BY_MATERIAL:
            options.material_code = self.material_input.text().strip()

        # Formato seleccionado
        format_value = self.format_combo.currentData()
        options.format = ExportFormat(format_value)

        return options

    def _update_preview(self):
        """Actualiza la previsualización del reporte"""
        options = self._get_current_options()
        records, stats = self.backend.preview_export(options)

        # Crear texto de previsualización
        preview = f"""
        ========== RESUMEN DEL REPORTE ==========

        Tipo de exportación: {options.export_type.value.replace('_', ' ').title()}

        Estadísticas:
        • Total de préstamos: {stats['total_loans']}
        • Préstamos activos: {stats['active_loans']}
        • Préstamos devueltos: {stats['returned_loans']}
        • Préstamos vencidos: {stats['overdue_loans']}
        • Promedio días prestado: {stats['avg_days_borrowed']}
        • Estudiantes únicos: {stats['unique_students']}
        • Materiales únicos: {stats['unique_materials']}

        ========== ÚLTIMOS PRÉSTAMOS ==========

        """

        # Mostrar últimos 10 registros
        for record in records[:10]:
            preview += f" {record.loan_id} | {record.student_name} | {record.material_name} | {record.loan_date} | {record.status}\n"

        if len(records) > 10:
            preview += f"\n... y {len(records) - 10} registros más.\n"

        self.preview_text.setText(preview)

    def _on_export_clicked(self):
        """Manejador del botón de exportación"""
        options = self._get_current_options()

        # Validar filtros según tipo
        if not self._validate_options(options):
            return

        # Solicitar ubicación de guardado
        file_extension = self._get_file_extension(options.format)
        file_filter = self._get_file_filter(options.format)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Exportación",
            f"historial_prestamos_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}",
            file_filter
        )

        if not file_path:
            return

        # Crear diálogo de progreso
        progress = QProgressDialog("Exportando datos...", "Cancelar", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            # Realizar exportación
            success, message = self.backend.perform_export(options, file_path)

            progress.close()

            if success:
                QMessageBox.information(self, "Exportación Exitosa", message)
                self.export_completed.emit(file_path)
            else:
                QMessageBox.critical(self, "Error de Exportación", message)
                self.export_failed.emit(message)
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Error durante la exportación: {str(e)}")
            self.export_failed.emit(str(e))

    def _validate_options(self, options: ExportOptions) -> bool:
        """
        Valida las opciones seleccionadas

        Args:
            options (ExportOptions): Opciones a validar

        Returns:
            bool: True si son válidas
        """
        if options.export_type == ExportType.DATE_RANGE:
            is_valid, message = self.backend.validate_date_range(
                options.start_date, options.end_date
            )
            if not is_valid:
                QMessageBox.warning(self, "Validación", message)
                return False

        elif options.export_type == ExportType.BY_STUDENT:
            if not options.student_name or options.student_name.strip() == "":
                QMessageBox.warning(self, "Validación", "Debe seleccionar o escribir un estudiante")
                return False

        elif options.export_type == ExportType.BY_MATERIAL:
            if not (options.material_code or options.material_name) or (options.material_code or '').strip() == "":
                QMessageBox.warning(self, "Validación", "Debe seleccionar o escribir un material")
                return False

        return True

    def _get_file_extension(self, format_type: ExportFormat) -> str:
        """Obtiene la extensión de archivo según el formato"""
        extensions = {
            ExportFormat.EXCEL: ".xlsx",
            ExportFormat.CSV: ".csv",
            ExportFormat.JSON: ".json",
            ExportFormat.PDF: ".pdf"
        }
        return extensions.get(format_type, ".xlsx")

    def _get_file_filter(self, format_type: ExportFormat) -> str:
        """Obtiene el filtro de archivo según el formato"""
        filters = {
            ExportFormat.EXCEL: "Excel Files (*.xlsx)",
            ExportFormat.CSV: "CSV Files (*.csv)",
            ExportFormat.JSON: "JSON Files (*.json)",
            ExportFormat.PDF: "PDF Files (*.pdf)"
        }
        return filters.get(format_type, "All Files (*.*)")

    def refresh_preview(self):
        """Refresca la previsualización (método público)"""
        self._update_preview()

