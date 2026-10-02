from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDialog, QMessageBox, QComboBox,
    QFormLayout, QTextEdit, QFileDialog, QTabWidget, QHeaderView
)
from components import SectionHeader, LabTable, SearchBar
from styles import COLORS

# Importar el backend
from backend.gestion_usuarios_backend import (
    get_users_backend, SystemUser, UserRole, UserStatus
)

class GestionUsuariosPage(QWidget):
    """
    Página de Gestión de Usuarios

    Permite administrar los usuarios del sistema (administradores y becarios),
    realizar operaciones CRUD y gestionar contraseñas.
    """

    # Señales para comunicación
    user_created = Signal(object)   # Emitida cuando se crea un usuario
    user_updated = Signal(object)   # Emitida cuando se actualiza un usuario
    user_deleted = Signal(str)      # Emitida cuando se elimina un usuario

    def __init__(self):
        """Inicializa la página de gestión de usuarios"""
        super().__init__()

        # Inicializar backend
        self.backend = get_users_backend()

        # Referencias a widgets
        self.search_bar = None
        self.users_table = None
        self.tab_widget = None

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_users()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Botón de crear usuario
        add_btn = self._create_add_button()

        # Agregar encabezado con botón
        header = SectionHeader(
            "Gestión de Usuarios",
            "Administra becarios y administradores del sistema",
            add_btn
        )
        main_layout.addWidget(header)

        # Crear pestañas
        self.tab_widget = QTabWidget()

        # Pestaña de usuarios
        users_tab = self._create_users_tab()
        self.tab_widget.addTab(users_tab, "  Usuarios")

        # Pestaña de estadísticas
        stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(stats_tab, "  Estadísticas")

        main_layout.addWidget(self.tab_widget, 1)

    def _create_add_button(self) -> QPushButton:
        """Crea el botón de crear usuario"""
        btn = QPushButton("＋  Crear Usuario")
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
        btn.clicked.connect(self._show_create_dialog)
        return btn

    def _create_users_tab(self) -> QWidget:
        """Crea la pestaña de lista de usuarios"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Barra de búsqueda
        self.search_bar = SearchBar("Buscar por nombre o matrícula...")
        self.search_bar.textChanged.connect(self._on_search)
        layout.addWidget(self.search_bar)

        # Tabla de usuarios
        self.users_table = self._create_users_table()

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
        table_layout.addWidget(self.users_table)

        layout.addWidget(table_container)

        return tab

    def _create_users_table(self) -> LabTable:
        """Crea la tabla de usuarios con sus columnas"""
        headers = self.backend.get_table_headers()
        table = LabTable(headers)

        # Matrícula, Nombre, Rol, Estado, Acciones
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 110)   # Matrícula
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        table.setColumnWidth(2, 110)   # Rol
        table.setColumnWidth(3, 115)   # Estado
        table.setColumnWidth(4, 160)   # Acciones (iconos)

        # Conectar señal de clic
        table.clicked.connect(self._on_table_click)

        return table

    def _create_audit_tab(self) -> QWidget:
        """Crea la pestaña de auditoría"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabla de auditoría
        headers = ["Fecha/Hora", "Usuario", "Evento", "Detalles"]
        self.audit_table = LabTable(headers)

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
        container_layout.addWidget(self.audit_table)

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
        refresh_btn.clicked.connect(self._load_audit_log)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        # Cargar auditoría
        self._load_audit_log()

        return tab

    def _create_stats_tab(self) -> QWidget:
        """Crea la pestaña de estadísticas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Frame para estadísticas
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
        stats_layout.setSpacing(15)

        # Título
        title = QLabel("Estadísticas del Sistema")
        title.setStyleSheet("font-size: 16px; font-weight: 700; border: none;")
        stats_layout.addWidget(title)

        # Grid de estadísticas
        grid = QGridLayout()
        grid.setSpacing(15)

        # Labels para estadísticas (se actualizarán dinámicamente)
        self.stats_labels = {}
        stats_items = [
            ("Total Usuarios:", "total"),
            ("Usuarios Activos:", "active"),
            ("Usuarios Inactivos:", "inactive"),
            ("Administradores:", "admins"),
            ("Becarios:", "becarios"),
            ("Activos Recientemente:", "active_recently"),
            ("Promedio Intentos Fallidos:", "avg_failed_attempts"),
            ("Tasa de Actividad:", "active_percentage")
        ]

        for i, (label, key) in enumerate(stats_items):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['muted_fg']}; border: none;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("font-weight: 600; border: none;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(value_lbl, i, 1)
            self.stats_labels[key] = value_lbl

        stats_layout.addLayout(grid)
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

    def _load_users(self, users: list = None):
        """
        Carga los usuarios en la tabla

        Args:
            users (list, optional): Lista de usuarios a mostrar
        """
        if users is None:
            users = self.backend.get_all_users()

        self.users_table.setRowCount(len(users))

        for i, user in enumerate(users):
            # Matrícula (monoespaciado)
            self.users_table.add_item(i, 0, user.username, mono=True)

            # Nombre
            self.users_table.add_item(i, 1, user.full_name)

            # Rol (con badge)
            role_text = user.get_role_display()
            self.users_table.set_badge_item(i, 2, role_text)

            # Estado (con badge)
            status_text = user.get_status_display()
            status_color = self._get_status_color(user.status)
            self.users_table.set_badge_item(i, 3, status_text)

            # Acciones
            actions = self._get_user_actions(user)
            self.users_table.add_actions(i, 4, actions)

    def _get_user_actions(self, user: SystemUser) -> list:
        """
        Obtiene las acciones disponibles para un usuario

        Args:
            user (SystemUser): Usuario

        Returns:
            list: Lista de acciones
        """
        actions = [
            ("Editar", lambda u=user: self._show_edit_dialog(u), False),
            ("Reset PW", lambda u=user: self._reset_password(u), False),
        ]

        if user.is_active():
            actions.append(("Desactivar", lambda u=user: self._toggle_status(u), True))
        else:
            actions.append(("Activar", lambda u=user: self._toggle_status(u), False))

        return actions

    def _get_status_color(self, status: UserStatus) -> str:
        """Obtiene el color para el badge de estado"""
        colors = {
            UserStatus.ACTIVE: COLORS.get('stat_green', '#10b981'),
            UserStatus.INACTIVE: COLORS.get('stat_red', '#ef4444'),
            UserStatus.SUSPENDED: COLORS.get('stat_orange', '#f59e0b'),
            UserStatus.LOCKED: COLORS.get('stat_red_dark', '#dc2626')
        }
        return colors.get(status, COLORS.get('muted_fg', '#64748b'))

    def _on_search(self, text: str):
        """Manejador de búsqueda de usuarios"""
        results = self.backend.search_users(text)
        self._load_users(results)

    def _on_table_click(self, index):
        """Manejador de clic en la tabla"""
        pass

    def _show_create_dialog(self):
        """Muestra el diálogo para crear un nuevo usuario"""
        dialog = UserDialog(self, self.backend)
        if dialog.exec() == QDialog.Accepted:
            user_data = dialog.get_user_data()
            success, message, user = self.backend.create_user(user_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_users()
                self.user_created.emit(user)

                # Mostrar contraseña generada si aplica
                if 'generated_password' in user_data:
                    QMessageBox.information(
                        self,
                        "Contraseña Generada",
                        f"La contraseña para el usuario {user.username} es:\n\n"
                        f"{user_data['generated_password']}\n\n"
                        f"Por favor, compártela con el usuario."
                    )
            else:
                QMessageBox.critical(self, "Error", message)

    def _show_edit_dialog(self, user: SystemUser):
        """Muestra el diálogo para editar un usuario"""
        dialog = UserDialog(self, self.backend, user)
        if dialog.exec() == QDialog.Accepted:
            update_data = dialog.get_update_data()
            success, message = self.backend.update_user(user.username, update_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_users()
                self.user_updated.emit(user)
            else:
                QMessageBox.critical(self, "Error", message)

    def _reset_password(self, user: SystemUser):
        """Resetea la contraseña de un usuario"""
        # Confirmar acción
        reply = QMessageBox.question(
            self,
            "Confirmar Reset de Contraseña",
            f"¿Estás seguro de que deseas restablecer la contraseña de {user.full_name}?\n\n"
            f"Se generará una nueva contraseña aleatoria.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message, new_password = self.backend.reset_password(user.username)

            if success:
                QMessageBox.information(
                    self,
                    "Contraseña Restablecida",
                    f"La nueva contraseña para {user.username} es:\n\n"
                    f"{new_password}\n\n"
                    f"Por favor, compártela con el usuario."
                )
                self._load_users()
            else:
                QMessageBox.critical(self, "Error", message)

    def _toggle_status(self, user: SystemUser):
        """Cambia el estado de un usuario"""
        success, message = self.backend.toggle_user_status(user.username)

        if success:
            QMessageBox.information(self, "Éxito", message)
            self._load_users()
        else:
            QMessageBox.warning(self, "Advertencia", message)

    def _load_audit_log(self):
        """Carga el registro de auditoría"""
        audit_log = self.backend.get_audit_log(limit=100)

        self.audit_table.setRowCount(len(audit_log))

        for i, event in enumerate(audit_log):
            self.audit_table.add_item(i, 0, event['timestamp'])
            self.audit_table.add_item(i, 1, event['username'])
            self.audit_table.set_badge_item(i, 2, event['event'])
            self.audit_table.add_item(i, 3, event['details'])

    def _load_statistics(self):
        """Carga las estadísticas del sistema"""
        stats = self.backend.get_statistics()

        # Actualizar labels
        self.stats_labels['total'].setText(str(stats['total']))
        self.stats_labels['active'].setText(str(stats['active']))
        self.stats_labels['inactive'].setText(str(stats['inactive']))
        self.stats_labels['admins'].setText(str(stats['admins']))
        self.stats_labels['becarios'].setText(str(stats['becarios']))
        self.stats_labels['active_recently'].setText(str(stats['active_recently']))
        self.stats_labels['avg_failed_attempts'].setText(str(stats['avg_failed_attempts']))
        self.stats_labels['active_percentage'].setText(f"{stats['active_percentage']}%")

    def refresh_users(self):
        """Refresca la lista de usuarios"""
        self.backend.refresh_data()
        self._load_users()

    def export_users(self):
        """Exporta la lista de usuarios"""
        # Diálogo para elegir formato
        export_dialog = QMessageBox(self)
        export_dialog.setWindowTitle("Exportar Usuarios")
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
            "Exportar Usuarios",
            f"usuarios_sistema.{format_type}",
            file_filter
        )

        if file_path:
            try:
                export_data = self.backend.export_users(format_type)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_data)

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Usuarios exportados a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar: {str(e)}"
                )

class UserDialog(QDialog):
    """
    Diálogo para crear o editar un usuario
    """

    def __init__(self, parent, backend, user: SystemUser = None):
        """
        Inicializa el diálogo

        Args:
            parent: Widget padre
            backend: Instancia del backend
            user (SystemUser, optional): Usuario a editar
        """
        super().__init__(parent)
        self.backend = backend
        self.user = user
        self.is_edit = user is not None
        self.generated_password = None

        self.setWindowTitle("Editar Usuario" if self.is_edit else "Crear Usuario")
        self.setFixedWidth(500)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: white; }")

        self._setup_ui()

        if self.is_edit:
            self._load_user_data()

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

        # Usuario / Matrícula
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("bec003")
        self.username_input.setFixedHeight(42)
        self.username_input.setStyleSheet(self._input_style())
        if not self.is_edit:
            form_layout.addRow("Usuario *:", self.username_input)
        else:
            user_label = QLabel(self.user.username)
            user_label.setStyleSheet("font-weight: 600; padding: 8px; border: none;")
            form_layout.addRow("Usuario:", user_label)

        # Nombre Completo
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre y apellidos")
        self.name_input.setFixedHeight(42)
        self.name_input.setStyleSheet(self._input_style())
        form_layout.addRow("Nombre Completo *:", self.name_input)

        # Rol
        self.role_combo = QComboBox()
        self.role_combo.addItems(self.backend.get_roles())
        self.role_combo.setFixedHeight(42)
        self.role_combo.setStyleSheet(self._combo_style())
        form_layout.addRow("Rol *:", self.role_combo)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@laboratorio.edu")
        self.email_input.setFixedHeight(42)
        self.email_input.setStyleSheet(self._input_style())
        form_layout.addRow("Email:", self.email_input)

        # Contraseña (solo para nuevo)
        if not self.is_edit:
            self.password_input = QLineEdit()
            self.password_input.setPlaceholderText("Contraseña inicial")
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setFixedHeight(42)
            self.password_input.setStyleSheet(self._input_style())
            form_layout.addRow("Contraseña *:", self.password_input)

            # Checkbox para generar contraseña aleatoria
            self.generate_check = QCheckBox("Generar contraseña aleatoria")
            self.generate_check.toggled.connect(self._on_generate_toggle)
            form_layout.addRow("", self.generate_check)

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

        save_btn = QPushButton("Guardar Usuario" if self.is_edit else "Crear Usuario")
        save_btn.setStyleSheet(self._save_style())
        save_btn.clicked.connect(self._on_save)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def _input_style(self) -> str:
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

    def _on_generate_toggle(self, checked: bool):
        """Manejador del checkbox de generar contraseña"""
        self.password_input.setEnabled(not checked)
        if checked:
            self.generated_password = SystemUser.generate_random_password()
            self.password_input.setText(self.generated_password)
        else:
            self.password_input.clear()
            self.generated_password = None

    def _load_user_data(self):
        """Carga los datos del usuario en el formulario"""
        if not self.user:
            return

        self.name_input.setText(self.user.full_name)

        index = self.role_combo.findText(self.user.role.value)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        if self.user.email:
            self.email_input.setText(self.user.email)

        if self.user.notes:
            self.notes_input.setText(self.user.notes)

    def get_user_data(self) -> dict:
        """Obtiene los datos del usuario del formulario"""
        data = {
            'username': self.username_input.text().strip().lower(),
            'full_name': self.name_input.text().strip(),
            'role': self.role_combo.currentText(),
            'email': self.email_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }

        if hasattr(self, 'generate_check') and self.generate_check.isChecked():
            data['password'] = self.generated_password
            data['generated_password'] = self.generated_password
        else:
            data['password'] = self.password_input.text() if hasattr(self, 'password_input') else ""

        return data

    def get_update_data(self) -> dict:
        """Obtiene los datos para actualizar"""
        data = {
            'full_name': self.name_input.text().strip(),
            'role': self.role_combo.currentText(),
            'email': self.email_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }

        # Incluir contraseña si se proporcionó una nueva
        if hasattr(self, 'password_input') and self.password_input.text():
            data['password'] = self.password_input.text()

        return data

    def _on_save(self):
        """Manejador del botón guardar"""
        if not self.is_edit:
            if not self.username_input.text().strip():
                QMessageBox.warning(self, "Validación", "El nombre de usuario es requerido")
                return

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre completo es requerido")
            return

        if not self.is_edit and not hasattr(self, 'generate_check'):
            if not self.password_input.text():
                QMessageBox.warning(self, "Validación", "La contraseña es requerida")
                return

        self.accept()
    def refresh_page(self):
        if hasattr(self.backend, 'reload'):
            self.backend.reload()
        elif hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()
        self._load_users()
