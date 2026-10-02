import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QStackedWidget, QLineEdit, QMessageBox,
    QCheckBox, QDialog
)
from components import SectionHeader, StepIndicator, ConfirmDialog
from styles import COLORS
from PySide6.QtGui import QPixmap, QPainter, QBrush

from backend.registrar_devolucion_backend import (
    get_devolucion_backend, DevolucionStep
)

class RegistrarDevolucionPage(QScrollArea):
    """
    Página para Registrar Devolución de Materiales.
    Pasos: Estudiante → Seleccionar préstamos → Firma → Confirmar
    """

    devolution_completed = Signal(object)
    process_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.backend = get_devolucion_backend()

        self.steps = ["Estudiante", "Préstamos", "Firma", "Confirmar"]
        self.current_step = 0

        self.step_widget = None
        self.stack = None
        self.current_student = None
        self.selected_loans = []

        # checkbox widgets keyed by step rebuild
        self._loan_checkboxes = []

        self._setup_ui()
        self._build_steps()

  

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background: {COLORS['background']};")

        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['background']};")
        self.setWidget(container)

        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 28, 32, 28)
        self.main_layout.setSpacing(20)

        header = SectionHeader(
            "Registrar Devolución",
            "Sigue los pasos para registrar una devolución"
        )
        self.main_layout.addWidget(header)

    def _create_logo(self, icon) -> QLabel:
                print(f"🎨 COLORS['primary'] = {COLORS['primary']!r}  (tipo: {type(COLORS['primary']).__name__})")
                size = 72
                logo = QLabel()
                logo.setFixedSize(size, size)
                logo.setAlignment(Qt.AlignCenter)
        
                # Sube de frontend/ a la raíz del proyecto y entra a assets/
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                icon_path = os.path.join(base_dir, "assets", icon)
        
                print(f"🔍 Buscando icono en: {icon_path}")
                print(f"🔍 ¿Existe?: {os.path.exists(icon_path)}")
        
                pixmap = QPixmap(icon_path)
        
                if pixmap.isNull():
                    logo.setText("L")
                    logo.setStyleSheet(f"""
                        background: {COLORS['primary']};
                        color: white;
                        border-radius: {size // 2}px;
                        font-size: 30px;
                        font-weight: bold;
                    """)
                    return logo
        
                pixmap = pixmap.scaled(
                    size, size,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
        
                rounded = QPixmap(size, size)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(pixmap))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(0, 0, size, size)
                painter.end()
        
                logo.setPixmap(rounded)
                logo.setStyleSheet("background: transparent; border: none;")
                return logo
        

    def _build_steps(self):
        self.step_widget = StepIndicator(self.steps, 0)
        self.main_layout.addWidget(self.step_widget, alignment=Qt.AlignHCenter)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self._build_step_0()   # Escanear estudiante
        self._build_step_1()   # Seleccionar préstamos (checkboxes)
        self._build_step_2()   # Firma digital
        self._build_step_3()   # Confirmar

        self.main_layout.addStretch()

  

    def _build_step_0(self):
        w = self._create_scan_card(
            icon="credencial.png",
            title="Escanear Credencial",
            description="Ingresa la matrícula del estudiante para ver sus préstamos activos",
            placeholder="Matrícula del estudiante",
            button_text="Buscar Estudiante"
        )
        inp = w.findChild(QLineEdit)
        btn = w.findChild(QPushButton, "action_btn")
        if inp:
            inp.returnPressed.connect(lambda: self._search_student(inp.text()))
        if btn:
            btn.clicked.connect(lambda: self._search_student(inp.text() if inp else ""))
        self.stack.addWidget(w)

  

    def _build_step_1(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.setSpacing(0)

        self.step1_card = QFrame()
        self.step1_card.setFixedWidth(640)
        self.step1_card.setStyleSheet(
            f"QFrame {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        c = QVBoxLayout(self.step1_card)
        c.setContentsMargins(28, 24, 28, 24)
        c.setSpacing(14)

        # Header
        self.step1_header = QLabel("Selecciona los materiales a devolver")
        self.step1_header.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {COLORS['foreground']}; background: transparent; border: none;"
        )
        c.addWidget(self.step1_header)

        # Select all checkbox
        self._select_all_cb = QCheckBox("Seleccionar todos")
        self._select_all_cb.setStyleSheet(f"""
            QCheckBox {{ font-size: 13px; color: {COLORS['muted_fg']}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 17px; height: 17px; border: 2px solid {COLORS['border']};
                border-radius: 4px; background: white; }}
            QCheckBox::indicator:checked {{ background: {COLORS['primary']}; border-color: {COLORS['primary']}; }}
        """)
        self._select_all_cb.toggled.connect(self._toggle_all)
        c.addWidget(self._select_all_cb)

      
        scan_row = QHBoxLayout()
        scan_row.setSpacing(8)
        scan_lbl = QLabel("Escanear material:")
        scan_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['muted_fg']}; background: transparent; border: none;")
        scan_row.addWidget(scan_lbl)
        self._scan_input = QLineEdit()
        self._scan_input.setPlaceholderText("Código del material — selecciona automáticamente")
        self._scan_input.setFixedHeight(38)
        self._scan_input.setStyleSheet(f"""
            QLineEdit {{
                background: white; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; padding: 6px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        self._scan_input.returnPressed.connect(self._scan_and_select)
        scan_row.addWidget(self._scan_input, 1)
        scan_btn = QPushButton("Agregar")
        scan_btn.setFixedHeight(38)
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary_light']}; color: {COLORS['primary']};
                border: 1.5px solid {COLORS['primary']}; border-radius: 6px;
                font-size: 13px; font-weight: 600; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; color: white; }}
        """)
        scan_btn.clicked.connect(self._scan_and_select)
        scan_row.addWidget(scan_btn)
        c.addLayout(scan_row)

        # Scrollable loans list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(300)
        scroll.setStyleSheet("background: transparent;")
        self._loans_inner = QWidget()
        self._loans_inner.setStyleSheet("background: transparent;")
        self.loans_layout = QVBoxLayout(self._loans_inner)
        self.loans_layout.setSpacing(8)
        self.loans_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._loans_inner)
        c.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = self._make_button("Cancelar", primary=False)
        cancel_btn.clicked.connect(self._reset_process)
        self._continuar_btn = self._make_button("Continuar — Firma Digital", primary=True)
        self._continuar_btn.clicked.connect(self._advance_from_loans)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._continuar_btn)
        c.addLayout(btn_row)

        layout.addWidget(self.step1_card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

    def _scan_and_select(self):
        """Scan a material code and auto-check matching loan checkboxes."""
        code = self._scan_input.text().strip().upper()
        if not code:
            return
        matched = False
        for cb in self._loan_checkboxes:
            loan = cb.property("loan_obj")
            if loan and loan.material_code.upper() == code:
                cb.setChecked(True)
                matched = True
        self._scan_input.clear()
        if not matched:
            QMessageBox.warning(
                self, "No encontrado",
                f"No hay préstamo activo con código '{code}' para este estudiante."
            )

    def _toggle_all(self, checked: bool):
        for cb in self._loan_checkboxes:
            cb.setChecked(checked)

    def _advance_from_loans(self):
        selected = [cb.property("loan_obj") for cb in self._loan_checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Sin selección", "Selecciona al menos un préstamo.")
            return
        self.selected_loans = selected
        # Clear password field for re-entry
        if hasattr(self, 'password_input'):
            self.password_input.clear()
        self._go_to(2)

  

    def _build_step_2(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet(
            f"QFrame {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(16)

        title = QLabel("Firma Digital del Estudiante")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['foreground']}; border: none;")
        cl.addWidget(title)

        info = QLabel("El estudiante debe ingresar su contraseña para autorizar la devolución.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS['muted_fg']}; background: transparent; border: none;")
        cl.addWidget(info)

        # Show selected materials summary
        self.firma_summary_label = QLabel()
        self.firma_summary_label.setWordWrap(True)
        self.firma_summary_label.setStyleSheet(
            f"background: {COLORS['muted']}; border-radius: 6px; padding: 10px 14px; border: none;"
            f"font-size: 13px; color: {COLORS['foreground']};"
        )
        cl.addWidget(self.firma_summary_label)

        pass_lbl = QLabel("Contraseña del Estudiante")
        pass_lbl.setStyleSheet(f"font-weight: 600; color: {COLORS['foreground']}; background: transparent; border: none;")
        cl.addWidget(pass_lbl)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("El estudiante ingresa su contraseña")
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self._verify_signature)
        cl.addWidget(self.password_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        back_btn = self._make_button("Atrás", primary=False)
        back_btn.clicked.connect(lambda: self._go_to(1))
        verify_btn = self._make_button("Verificar y Continuar", primary=True)
        verify_btn.clicked.connect(self._verify_signature)
        btn_row.addWidget(back_btn)
        btn_row.addStretch()
        btn_row.addWidget(verify_btn)
        cl.addLayout(btn_row)

        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

  

    def _build_step_3(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet(
            f"QFrame {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(16)

        title = QLabel("Resumen de Devolución")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['foreground']}; border: none;")
        cl.addWidget(title)

        # Student info row
        self.confirm_student_lbl = QLabel()
        self.confirm_student_lbl.setStyleSheet(
            f"background: {COLORS['muted']}; border-radius: 6px; padding: 10px 14px; font-size: 13px; border: none;"
        )
        cl.addWidget(self.confirm_student_lbl)

        # Loans list
        list_lbl = QLabel("Materiales a devolver:")
        list_lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {COLORS['muted_fg']}; background: transparent; border: none;")
        cl.addWidget(list_lbl)

        self.confirm_loans_frame = QFrame()
        self.confirm_loans_frame.setStyleSheet(
            f"QFrame {{ background: {COLORS['green_bg']}; border-radius: 6px; }}"
        )
        self.confirm_loans_layout = QVBoxLayout(self.confirm_loans_frame)
        self.confirm_loans_layout.setContentsMargins(14, 10, 14, 10)
        self.confirm_loans_layout.setSpacing(6)
        cl.addWidget(self.confirm_loans_frame)

        # Fine warning
        self.fine_lbl = QLabel()
        self.fine_lbl.setStyleSheet(
            f"color: {COLORS['destructive']}; font-weight: 600; background: transparent; border: none;"
        )
        self.fine_lbl.hide()
        cl.addWidget(self.fine_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = self._make_button("Cancelar", primary=False)
        cancel_btn.clicked.connect(self._reset_process)
        confirm_btn = self._make_button("Confirmar Devolución", primary=True)
        confirm_btn.clicked.connect(self._confirm_devolution)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        cl.addLayout(btn_row)

        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

  

    def _search_student(self, student_id: str):
        success, message, student = self.backend.get_student_by_id(student_id)
        if not success:
            QMessageBox.warning(self, "Estudiante no encontrado", message)
            return
        self.current_student = student
        self._load_active_loans(student.student_id)
        self._go_to(1)

    def _load_active_loans(self, student_id: str):
        # Clear previous
        self._loan_checkboxes = []
        while self.loans_layout.count():
            item = self.loans_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(False)
        self._select_all_cb.blockSignals(False)

        self.step1_header.setText(
            f"{self.current_student.name}  ({student_id}) — selecciona los materiales a devolver"
        )

        loans = self.backend.get_active_loans(student_id)

        if not loans:
            lbl = QLabel("Este estudiante no tiene préstamos activos.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {COLORS['muted_fg']}; padding: 20px; background: transparent; border: none;")
            self.loans_layout.addWidget(lbl)
            return

        for loan in loans:
            frame = QFrame()
            bg = COLORS.get("red_bg", "#fee2e2") if loan.is_overdue else COLORS["muted"]
            frame.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                }}
            """)
            row = QHBoxLayout(frame)
            row.setContentsMargins(14, 10, 14, 10)
            row.setSpacing(12)

            cb = QCheckBox()
            cb.setProperty("loan_obj", loan)
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 18px; height: 18px;
                    border: 2px solid {COLORS['border']};
                    border-radius: 4px; background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {COLORS['primary']};
                    border-color: {COLORS['primary']};
                }}
            """)
            row.addWidget(cb)
            self._loan_checkboxes.append(cb)

            info_col = QVBoxLayout()
            name_lbl = QLabel(f"{loan.material_name}  ({loan.material_code})  ×{loan.quantity}")
            name_lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; background: transparent; border: none;")
            info_col.addWidget(name_lbl)

            detail = f"Prestado: {loan.loan_date}"
            if loan.is_overdue:
                detail += f"  •  VENCIDO ({loan.days_overdue} días)"
            detail_lbl = QLabel(detail)
            detail_lbl.setStyleSheet(
                f"color: {COLORS['destructive'] if loan.is_overdue else COLORS['muted_fg']}; border: none;"
                f"font-size: 12px; background: transparent;"
            )
            info_col.addWidget(detail_lbl)

            row.addLayout(info_col)
            row.addStretch()
            self.loans_layout.addWidget(frame)

        self.loans_layout.addStretch()

    def _verify_signature(self):
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Contraseña requerida", "Ingresa la contraseña del estudiante.")
            return
        success, message = self.backend.verify_student_password(
            self.current_student.student_id, password
        )
        if success:
            self._update_confirm_screen()
            self._go_to(3)
        else:
            QMessageBox.warning(self, "Firma no verificada", message)

    def _update_confirm_screen(self):
        """Populate step 3 with selected loans info."""
        self.confirm_student_lbl.setText(
            f"Estudiante: {self.current_student.name}  |  Matrícula: {self.current_student.student_id}"
        )
        # Clear loans list
        while self.confirm_loans_layout.count():
            item = self.confirm_loans_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_overdue = False
        for loan in self.selected_loans:
            lbl = QLabel(f"• {loan.material_name}  ({loan.material_code})  ×{loan.quantity}")
            lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['green_fg']}; background: transparent; border: none;")
            self.confirm_loans_layout.addWidget(lbl)
            if loan.is_overdue:
                has_overdue = True

        if has_overdue:
            self.fine_lbl.setText("[!]  Uno o más préstamos están vencidos. Se aplicarán multas.")
            self.fine_lbl.show()
        else:
            self.fine_lbl.hide()

        # Update firma summary label
        lines = [f"• {l.material_name} ×{l.quantity}" for l in self.selected_loans]
        self.firma_summary_label.setText(
            f"Devolviendo {len(self.selected_loans)} material(es):\n" + "\n".join(lines)
        )

    def _confirm_devolution(self):
        dialog = ConfirmDialog(
            self.window(),
            "Confirmar Devolución",
            f"¿Confirmar la devolución de {len(self.selected_loans)} material(es)?\n"
            "Esta acción no se puede deshacer.",
            "Registrar Devolución"
        )
        if dialog.exec() != QDialog.Accepted:
            return

        becario_name = "Becario"
        errors = []
        last_devolution = None

        for loan in self.selected_loans:
            success, message, devolution = self.backend.register_devolution(
                loan, self.current_student, becario_name
            )
            if success:
                last_devolution = devolution
            else:
                errors.append(f"{loan.material_name}: {message}")

        if errors:
            QMessageBox.warning(
                self, "Devoluciones con errores",
                "Algunos materiales no pudieron registrarse:\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self, "Éxito",
                f"{len(self.selected_loans)} material(es) devuelto(s) correctamente."
            )

        if last_devolution:
            self.devolution_completed.emit(last_devolution)
        self._reset_process()

    def _reset_process(self):
        self.backend.reset_process()
        self.current_step = 0
        self.current_student = None
        self.selected_loans = []
        self._loan_checkboxes = []
        self.stack.setCurrentIndex(0)
        self._update_step_indicator()

    def _go_to(self, step: int):
        self.current_step = step
        self.stack.setCurrentIndex(step)
        self._update_step_indicator()

    def _update_step_indicator(self):
        idx = self.main_layout.indexOf(self.step_widget)
        self.main_layout.removeWidget(self.step_widget)
        self.step_widget.deleteLater()
        self.step_widget = StepIndicator(self.steps, self.current_step)
        self.main_layout.insertWidget(idx, self.step_widget, alignment=Qt.AlignHCenter)

  

    def _create_scan_card(self, icon: str, title: str, description: str,
                              placeholder: str, button_text: str) -> QWidget:
            """Crea una tarjeta de escaneo genérica"""
            w = QWidget()
            w.setStyleSheet(f"background: {COLORS['background']};")
            layout = QVBoxLayout(w)
            layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
    
            card = QFrame()
            card.setFixedWidth(640)
            card.setStyleSheet(f"QFrame {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(40, 36, 40, 36)
            card_layout.setSpacing(16)
            card_layout.setAlignment(Qt.AlignHCenter)
    
            # Icono
            # ✅ Construye el logo aquí, a partir del nombre del archivo
            logo = self._create_logo(icon)
            card_layout.addWidget(logo, alignment=Qt.AlignHCenter)
    
    
            # Título
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 20px; font-weight: 700; border: none;")
            card_layout.addWidget(title_label)
    
            # Descripción
            desc_label = QLabel(description)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {COLORS['muted_fg']}; border: none;")
            card_layout.addWidget(desc_label)
    
            # Campo de entrada
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            input_field.setFixedHeight(48)
            input_field.setAlignment(Qt.AlignCenter)
            input_field.setStyleSheet(self._input_style())
            card_layout.addWidget(input_field)
    
            # Botón de acción
            action_btn = QPushButton(button_text)
            action_btn.setObjectName("action_btn")
            action_btn.setFixedHeight(48)
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.setStyleSheet(self._primary_btn_style())
            card_layout.addWidget(action_btn)
    
            layout.addWidget(card, alignment=Qt.AlignHCenter)
            return w

    def _make_button(self, text, primary=True):
        btn = QPushButton(text)
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._primary_btn_style() if primary else self._secondary_btn_style())
        return btn

    def _primary_btn_style(self):
        return f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white; border: none;
                border-radius: 6px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """

    def _secondary_btn_style(self):
        return f"""
            QPushButton {{
                background: {COLORS['muted']}; color: {COLORS['foreground']};
                border: 1px solid {COLORS['border']}; border-radius: 6px; font-size: 14px;
            }}
            QPushButton:hover {{ background: #e2e8f0; }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                background: white; border: 2px solid {COLORS['border']};
                border-radius: 6px; padding: 8px; font-size: 16px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """
