from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDialog, QMessageBox, QComboBox,
    QFormLayout, QTextEdit, QFileDialog, QHeaderView
)
from components import SectionHeader, LabTable, SearchBar, make_button
from styles import COLORS

# Importar el backend
from backend.gestion_estudiantes_backend import (
    get_students_backend, Student, StudentStatus
)

class GestionEstudiantesPage(QWidget):
    """
    Página de Gestión de Estudiantes

    Permite administrar los estudiantes registrados, realizar operaciones
    CRUD y ver su historial de préstamos.
    """

    # Señales para comunicación
    student_added = Signal(object)   # Emitida cuando se agrega un estudiante
    student_updated = Signal(object) # Emitida cuando se actualiza un estudiante
    student_deleted = Signal(str)    # Emitida cuando se elimina un estudiante

    def __init__(self):
        """Inicializa la página de gestión de estudiantes"""
        super().__init__()

        self._role = "becario"  # Se actualiza tras login

        # Inicializar backend
        self.backend = get_students_backend()

        # Referencias a widgets
        self.search_bar = None
        self.students_table = None

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_students()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Botón de agregar estudiante
        add_btn = self._create_add_button()

        # Agregar encabezado con botón
        header = SectionHeader(
            "Gestión de Estudiantes",
            "Administra los estudiantes registrados",
            add_btn
        )
        main_layout.addWidget(header)

        # Barra de búsqueda
        self.search_bar = SearchBar("Buscar por nombre o matrícula...")
        self.search_bar.textChanged.connect(self._on_search)
        main_layout.addWidget(self.search_bar)

        # Tabla de estudiantes
        self.students_table = self._create_students_table()

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
        table_layout.addWidget(self.students_table)

        main_layout.addWidget(table_container, 1)

    def _create_add_button(self) -> QPushButton:
        """Crea el botón de agregar estudiante"""
        btn = QPushButton("＋  Registrar Estudiante")
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
        btn.clicked.connect(self._show_add_dialog)
        return btn

    def _create_students_table(self) -> LabTable:
        """Crea la tabla de estudiantes con sus columnas"""
        headers = self.backend.get_table_headers()
        table = LabTable(headers)

        # Matrícula, Nombre, Carrera, Préstamos Activos, Estado, Acciones
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 110)   # Matrícula
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        table.setColumnWidth(2, 160)   # Carrera
        table.setColumnWidth(3, 100)   # Préstamos Activos (pequeña)
        table.setColumnWidth(4, 115)   # Estado
        table.setColumnWidth(5, 160)   # Acciones (iconos)

        # Conectar señal de clic para acciones
        table.clicked.connect(self._on_table_click)

        return table

    def _load_students(self, students: list = None):
        """
        Carga los estudiantes en la tabla

        Args:
            students (list, optional): Lista de estudiantes a mostrar
        """
        if students is None:
            students = self.backend.get_all_students()

        self.students_table.setRowCount(len(students))

        for i, student in enumerate(students):
            # Matrícula (monoespaciado)
            self.students_table.add_item(i, 0, student.student_id, mono=True)

            # Nombre
            self.students_table.add_item(i, 1, student.name)

            # Carrera
            self.students_table.add_item(i, 2, student.career)

            # Préstamos activos
            self.students_table.add_item(i, 3, str(student.active_loans))

            # Estado (con badge)
            status_text = student.get_status_display()
            self.students_table.set_badge_item(i, 4, status_text)

            # Acciones (botones)
            actions = self._get_student_actions(student)
            self.students_table.add_actions(i, 5, actions)

    def set_role(self, role: str):
        """Actualiza el rol y recarga la tabla para aplicar permisos."""
        self._role = role
        self._load_students()

    def _get_student_actions(self, student: Student) -> list:
        """
        Obtiene las acciones disponibles para un estudiante

        Args:
            student (Student): Estudiante

        Returns:
            list: Lista de acciones (texto, callback, is_warning)
        """
        # Use s=student default arg to capture by value, not reference
        actions = [
            ("Ver Historial", lambda s=student: self._show_loan_history(s.student_id), False),
        ]

        if self._role == "admin":
            if student.is_active():
                actions.append(("Desactivar", lambda s=student: self._toggle_status(s), False))
            else:
                actions.append(("Activar", lambda s=student: self._toggle_status(s), False))

        actions.append(("Editar", lambda s=student: self._show_edit_dialog(s), False))
        if self._role == "admin":
            actions.append(("Eliminar", lambda s=student: self._delete_student(s), True))

        return actions

    def _on_search(self, text: str):
        """Manejador de búsqueda de estudiantes"""
        results = self.backend.search_students(text)
        self._load_students(results)

    def _on_table_click(self, index):
        """Manejador de clic en la tabla"""
        # Los botones de acción manejarán sus propios eventos
        pass

    def _show_add_dialog(self):
        """Muestra el diálogo para agregar un nuevo estudiante"""
        dialog = StudentDialog(self, self.backend)
        if dialog.exec() == QDialog.Accepted:
            student_data = dialog.get_student_data()
            success, message, student = self.backend.add_student(student_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_students()
                self.student_added.emit(student)
            else:
                QMessageBox.critical(self, "Error", message)

    def _show_edit_dialog(self, student: Student):
        """Muestra el diálogo para editar un estudiante"""
        dialog = StudentDialog(self, self.backend, student)
        if dialog.exec() == QDialog.Accepted:
            update_data = dialog.get_update_data()
            success, message = self.backend.update_student(student.student_id, update_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_students()
                self.student_updated.emit(student)
            else:
                QMessageBox.critical(self, "Error", message)

    def _toggle_status(self, student: Student):
        """Cambia el estado de un estudiante"""
        success, message = self.backend.toggle_student_status(student.student_id)

        if success:
            QMessageBox.information(self, "Éxito", message)
            self._load_students()
        else:
            QMessageBox.warning(self, "Advertencia", message)

    def _delete_student(self, student: Student):
        """Elimina un estudiante del sistema"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar al estudiante {student.name}?\n\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.backend.delete_student(student.student_id)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_students()
                self.student_deleted.emit(student.student_id)
            else:
                QMessageBox.critical(self, "Error", message)

    def _show_loan_history(self, student_id: str):
        """Muestra el historial de préstamos de un estudiante"""
        student = self.backend.get_student_by_id(student_id)
        if not student:
            return

        history = self.backend.get_student_loan_history(student_id)

        # Crear diálogo de historial
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historial de Préstamos - {student.name}")
        dialog.setMinimumSize(700, 500)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Información del estudiante
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {COLORS['muted']}; border-radius: 8px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)

        info_text = QLabel(
            f"<b>Matrícula:</b> {student.student_id}<br>"
            f"<b>Nombre:</b> {student.name}<br>"
            f"<b>Carrera:</b> {student.career}<br>"
            f"<b>Préstamos activos:</b> {student.active_loans}"
        )
        info_layout.addWidget(info_text)
        layout.addWidget(info_frame)

        # Tabla de historial
        headers = ["ID Préstamo", "Material", "Fecha Préstamo", "Fecha Devolución", "Estado"]
        history_table = LabTable(headers)
        history_table.setRowCount(len(history))

        for i, loan in enumerate(history):
            history_table.add_item(i, 0, loan.loan_id, mono=True)
            history_table.add_item(i, 1, loan.material_name)
            history_table.add_item(i, 2, loan.loan_date.split()[0] if loan.loan_date else "")
            history_table.add_item(i, 3, loan.return_date.split()[0] if loan.return_date else "-")
            history_table.set_badge_item(i, 4, loan.status)

        layout.addWidget(history_table)

        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def refresh_students(self):
        """Refresca la lista de estudiantes"""
        self._load_students()

    def export_students(self):
        """Exporta la lista de estudiantes"""
        # Diálogo para elegir formato
        export_dialog = QMessageBox(self)
        export_dialog.setWindowTitle("Exportar Estudiantes")
        export_dialog.setText("Selecciona el formato de exportación:")
        csv_btn = export_dialog.addButton("CSV", QMessageBox.ActionRole)
        json_btn = export_dialog.addButton("JSON", QMessageBox.ActionRole)
        cancel_btn = export_dialog.addButton("Cancelar", QMessageBox.RejectRole)

        export_dialog.exec()

        format_type = None
        if export_dialog.clickedButton() == csv_btn:
            format_type = "csv"
            file_filter = "CSV Files (*.csv)"
        elif export_dialog.clickedButton() == json_btn:
            format_type = "json"
            file_filter = "JSON Files (*.json)"
        else:
            return

        # Guardar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Estudiantes",
            f"estudiantes_laboratorio.{format_type}",
            file_filter
        )

        if file_path:
            try:
                export_data = self.backend.export_students(format_type)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_data)

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Estudiantes exportados a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar: {str(e)}"
                )

class StudentDialog(QDialog):
    """
    Diálogo para registrar o editar un estudiante
    """

    def __init__(self, parent, backend, student: Student = None):
        """
        Inicializa el diálogo

        Args:
            parent: Widget padre
            backend: Instancia del backend
            student (Student, optional): Estudiante a editar
        """
        super().__init__(parent)
        self.backend = backend
        self.student = student
        self.is_edit = student is not None

        self.setWindowTitle("Editar Estudiante" if self.is_edit else "Registrar Estudiante")
        self.setFixedWidth(500)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: white; }")

        self._setup_ui()

        if self.is_edit:
            self._load_student_data()

    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Título
        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size: 18px; font-weight: 700; border: none;")
        layout.addWidget(title)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Matrícula
        self.matricula_input = QLineEdit()
        self.matricula_input.setPlaceholderText("Ej: 2024005")
        self.matricula_input.setFixedHeight(42)
        self.matricula_input.setStyleSheet(self._input_style())
        if not self.is_edit:
            form_layout.addRow("Matrícula *:", self.matricula_input)
        else:
            mat_label = QLabel(self.student.student_id)
            mat_label.setStyleSheet("font-weight: 600; padding: 8px; border: none;")
            form_layout.addRow("Matrícula:", mat_label)

        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre y apellidos")
        self.name_input.setFixedHeight(42)
        self.name_input.setStyleSheet(self._input_style())
        form_layout.addRow("Nombre Completo *:", self.name_input)

        # Carrera
        self.career_combo = QComboBox()
        self.career_combo.addItems(self.backend.get_careers())
        self.career_combo.setFixedHeight(42)
        self.career_combo.setStyleSheet(self._combo_style())
        form_layout.addRow("Carrera *:", self.career_combo)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@ejemplo.com")
        self.email_input.setFixedHeight(42)
        self.email_input.setStyleSheet(self._input_style())
        form_layout.addRow("Email:", self.email_input)

        # Contraseña (solo para nuevo o si se quiere cambiar)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña inicial")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(42)
        self.password_input.setStyleSheet(self._input_style())
        form_layout.addRow("Contraseña *:" if not self.is_edit else "Nueva Contraseña:", self.password_input)

        if self.is_edit:
            pass_label = QLabel("Dejar en blanco para mantener la actual")
            pass_label.setStyleSheet(f"color: {COLORS['muted_fg']}; font-size: 11px; border: none;")
            form_layout.addRow("", pass_label)

        # Notas
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales (opcional)")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet(self._textarea_style())
        form_layout.addRow("Notas:", self.notes_input)

        layout.addLayout(form_layout)

        layout.addSpacing(10)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(self._cancel_style())
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Guardar Estudiante")
        save_btn.setStyleSheet(self._save_style())
        save_btn.clicked.connect(self._on_save)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def _input_style(self) -> str:
        """Estilo para campos de texto"""
        return f"""
            QLineEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """

    def _combo_style(self) -> str:
        """Estilo para combo box"""
        return f"""
            QComboBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QComboBox:focus {{
                border-color: {COLORS['primary']};
            }}
        """

    def _textarea_style(self) -> str:
        """Estilo para área de texto"""
        return f"""
            QTextEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """

    def _cancel_style(self) -> str:
        """Estilo para botón cancelar"""
        return f"""
            QPushButton {{
                background: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: #e2e8f0;
            }}
        """

    def _save_style(self) -> str:
        """Estilo para botón guardar"""
        return f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS.get('primary_hover', '#3b82f6')};
            }}
        """

    def _load_student_data(self):
        """Carga los datos del estudiante en el formulario"""
        if not self.student:
            return

        self.name_input.setText(self.student.name)

        index = self.career_combo.findText(self.student.career)
        if index >= 0:
            self.career_combo.setCurrentIndex(index)

        if self.student.email:
            self.email_input.setText(self.student.email)

        if self.student.notes:
            self.notes_input.setText(self.student.notes)

    def get_student_data(self) -> dict:
        """
        Obtiene los datos del estudiante del formulario

        Returns:
            dict: Datos del estudiante
        """
        return {
            'student_id': self.matricula_input.text().strip(),
            'name': self.name_input.text().strip(),
            'career': self.career_combo.currentText(),
            'email': self.email_input.text().strip(),
            'password': self.password_input.text(),
            'notes': self.notes_input.toPlainText().strip()
        }

    def get_update_data(self) -> dict:
        """
        Obtiene los datos para actualizar

        Returns:
            dict: Datos a actualizar
        """
        data = {
            'name': self.name_input.text().strip(),
            'career': self.career_combo.currentText(),
            'email': self.email_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }

        # Solo incluir contraseña si se proporcionó una nueva
        password = self.password_input.text()
        if password:
            data['password'] = password

        return data

    def _on_save(self):
        """Manejador del botón guardar"""
        if not self.is_edit:
            # Validar campos requeridos para nuevo estudiante
            if not self.matricula_input.text().strip():
                QMessageBox.warning(self, "Validación", "La matrícula es requerida")
                return
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Validación", "El nombre es requerido")
                return
            if not self.password_input.text():
                QMessageBox.warning(self, "Validación", "La contraseña es requerida")
                return

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre es requerido")
            return

        self.accept()
    def refresh_page(self):
        if hasattr(self.backend, 'reload'):
            self.backend.reload()
        elif hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()
        self._load_students()
