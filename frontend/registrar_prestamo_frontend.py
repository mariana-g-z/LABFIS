from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QStackedWidget, QLineEdit, QSpinBox,
    QDialog, QMessageBox
)
from components import SectionHeader, StepIndicator, InfoRow
from styles import COLORS

from backend.registrar_prestamo_backend import (
    get_prestamo_backend, PrestamoStep, MaterialInfo
)

class RegistrarPrestamoPage(QScrollArea):

    loan_completed = Signal(object)
    process_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.backend = get_prestamo_backend()
        self.steps = ["Estudiante", "Identificar", "Material", "Detalles", "Firma", "Confirmar"]
        self.current_step = 0
        self.step_widget = None
        self.stack = None
        self.current_student = None
        self.current_material = None
        self.current_quantity = 1
        self.materials_list = []   # [(MaterialInfo, qty), ...]
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
        header = SectionHeader("Registrar Préstamo", "Sigue los pasos para registrar un nuevo préstamo")
        self.main_layout.addWidget(header)

    def _build_steps(self):
        self.step_widget = StepIndicator(self.steps, 0)
        self.main_layout.addWidget(self.step_widget, alignment=Qt.AlignHCenter)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        self._build_step_0()
        self._build_step_1()
        self._build_step_2()
        self._build_step_3()
        self._build_step_4()
        self._build_step_5()
        self.main_layout.addStretch()

    # ── Paso 0: Buscar estudiante ─────────────────────────────────────────────
    def _build_step_0(self):
        w = self._create_scan_card(
            icon="[ID]", title="Escanear Credencial del Estudiante",
            description="Pasa la credencial o ingresa la matrícula manualmente",
            placeholder="Matrícula del estudiante", button_text="Buscar Estudiante"
        )
        input_field = w.findChild(QLineEdit)
        search_btn = w.findChild(QPushButton, "action_btn")
        if input_field:
            input_field.returnPressed.connect(lambda: self._search_student(input_field.text()))
        if search_btn:
            search_btn.clicked.connect(lambda _=False: self._search_student(input_field.text() if input_field else ""))
        self.stack.addWidget(w)

    # ── Paso 1: Info estudiante ───────────────────────────────────────────────
    def _build_step_1(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(12)

        self.step1_header = QLabel("✓ Estudiante Encontrado")
        self.step1_header.setStyleSheet(
            f"font-size:18px;font-weight:700;color:{COLORS.get('green_fg','#14532d')};"
            f"background:{COLORS.get('green_bg','#dcfce7')};padding:10px 14px;border-radius:6px;border:none;"
        )
        card_layout.addWidget(self.step1_header)

        self.student_info_container = QVBoxLayout()
        card_layout.addLayout(self.student_info_container)

        cancel_btn = self._make_button("Cancelar", primary=False)
        continue_btn = self._make_button("Continuar — Agregar Material", primary=True)
        cancel_btn.clicked.connect(self._reset_process)
        continue_btn.clicked.connect(self._next_step)

        btn_w = QWidget()
        bl = QHBoxLayout(btn_w)
        bl.setSpacing(12)
        bl.addWidget(cancel_btn)
        bl.addWidget(continue_btn)
        card_layout.addWidget(btn_w)
        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

    # ── Paso 2: Buscar material ───────────────────────────────────────────────
    def _build_step_2(self):
        w = self._create_scan_card(
            icon="[MAT]", title="Escanear Material",
            description="Ingresa el código del material",
            placeholder="Código del material (ej. MUL-001)", button_text="Buscar Material"
        )
        input_field = w.findChild(QLineEdit)
        search_btn = w.findChild(QPushButton, "action_btn")
        if input_field:
            input_field.returnPressed.connect(lambda: self._search_material(input_field.text()))
        if search_btn:
            search_btn.clicked.connect(lambda _=False: self._search_material(input_field.text() if input_field else ""))
        self.stack.addWidget(w)

    # ── Paso 3: Info material + cantidad ─────────────────────────────────────
    def _build_step_3(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(12)

        self.step3_header = QLabel("✓ Material Encontrado")
        self.step3_header.setStyleSheet(
            f"font-size:18px;font-weight:700;color:{COLORS.get('green_fg','#14532d')};"
            f"background:{COLORS.get('green_bg','#dcfce7')};padding:10px 14px;border-radius:6px;border:none;"
        )
        card_layout.addWidget(self.step3_header)

        self.material_info_container = QVBoxLayout()
        card_layout.addLayout(self.material_info_container)

        qty_layout = QHBoxLayout()
        qty_label = QLabel("Cantidad:")
        qty_label.setStyleSheet(f"font-weight:600;color:{COLORS['foreground']};background:transparent;border:none;")
        qty_layout.addWidget(qty_label)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedWidth(100)
        self.qty_spin.setFixedHeight(40)
        self.qty_spin.setStyleSheet(
            f"QSpinBox{{background:white;border:1px solid {COLORS['border']};border-radius:6px;padding:6px 10px;font-size:16px;}}"
        )
        self.qty_spin.valueChanged.connect(self._on_quantity_changed)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addStretch()
        card_layout.addLayout(qty_layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{COLORS['border']};max-height:1px;border:none;")
        card_layout.addWidget(sep)

        list_lbl = QLabel("Materiales en esta solicitud:")
        list_lbl.setStyleSheet(f"font-weight:600;font-size:13px;color:{COLORS['muted_fg']};background:transparent;border:none;")
        card_layout.addWidget(list_lbl)

        self.materials_list_frame = QFrame()
        self.materials_list_frame.setStyleSheet(f"background:{COLORS['muted']};border-radius:6px;")
        self.materials_list_layout = QVBoxLayout(self.materials_list_frame)
        self.materials_list_layout.setContentsMargins(12, 8, 12, 8)
        self.materials_list_layout.setSpacing(4)
        card_layout.addWidget(self.materials_list_frame)

        btn_w = QWidget()
        btn_layout = QHBoxLayout(btn_w)
        btn_layout.setSpacing(10)

        cancel_btn = self._make_button("Cancelar", primary=False)
        cancel_btn.clicked.connect(self._reset_process)

        add_more_btn = self._make_button("+ Agregar otro material", primary=False)
        add_more_btn.setStyleSheet(
            f"QPushButton{{background:{COLORS['primary_light']};color:{COLORS['primary']};"
            f"border:1.5px solid {COLORS['primary']};border-radius:6px;font-size:14px;font-weight:600;padding:8px 16px;}}"
            f"QPushButton:hover{{background:{COLORS['primary']};color:white;}}"
        )
        add_more_btn.clicked.connect(self._add_current_and_scan_more)

        continue_btn = self._make_button("Continuar — Firma Digital", primary=True)
        continue_btn.clicked.connect(self._add_current_and_continue)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(add_more_btn)
        btn_layout.addWidget(continue_btn)
        card_layout.addWidget(btn_w)
        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

    # ── Paso 4: Firma digital ─────────────────────────────────────────────────
    def _build_step_4(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(15)

        header = QLabel("Firma Digital del Estudiante")
        header.setStyleSheet(f"font-size:18px;font-weight:700;color:{COLORS['foreground']};border:none;")
        card_layout.addWidget(header)

        info = QLabel("El estudiante debe ingresar su contraseña para autorizar el préstamo.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{COLORS['muted_fg']};background:transparent;border:none;")
        card_layout.addWidget(info)

        pass_label = QLabel("Contraseña del Estudiante")
        pass_label.setStyleSheet(f"font-weight:600;color:{COLORS['foreground']};background:transparent;border:none;")
        card_layout.addWidget(pass_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("El estudiante ingresa su contraseña")
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self._verify_signature)
        card_layout.addWidget(self.password_input)

        cancel_btn = self._make_button("Cancelar", primary=False)
        verify_btn = self._make_button("Verificar y Continuar", primary=True)
        cancel_btn.clicked.connect(self._reset_process)
        verify_btn.clicked.connect(self._verify_signature)

        btn_w = QWidget()
        bl = QHBoxLayout(btn_w)
        bl.setSpacing(12)
        bl.addWidget(cancel_btn)
        bl.addWidget(verify_btn)
        card_layout.addWidget(btn_w)
        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

    # ── Paso 5: Confirmar ─────────────────────────────────────────────────────
    def _build_step_5(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(12)

        header = QLabel("Resumen del Préstamo")
        header.setStyleSheet("font-size:18px;font-weight:700;border:none;")
        card_layout.addWidget(header)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"QFrame{{background:{COLORS['muted']};border-radius:6px;}}")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(16, 14, 16, 14)

        self.summary_widgets = {}
        summary_fields = [
            ("Estudiante",   "student_name"),
            ("Matrícula",    "student_id"),
            ("Carrera",      "student_career"),
            ("Material(es)", "material_display"),
            ("Cantidad",     "quantity"),
            ("Becario",      "becario_name"),
            ("Fecha/Hora",   "loan_date"),
            ("Fecha Límite", "due_date"),
        ]
        for label, key in summary_fields:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 5, 0, 5)
            lw = QLabel(label)
            lw.setStyleSheet(f"color:{COLORS['muted_fg']};min-width:110px;border:none;")
            vw = QLabel("-")
            vw.setStyleSheet("font-weight:600;border:none;")
            vw.setWordWrap(True)
            row_layout.addWidget(lw)
            row_layout.addWidget(vw, 1)
            summary_layout.addWidget(row)
            self.summary_widgets[key] = vw

        self.remaining_loans_widget = QLabel()
        self.remaining_loans_widget.setStyleSheet(
            f"color:{COLORS.get('green_fg','#14532d')};margin-top:10px;border:none;"
        )
        summary_layout.addWidget(self.remaining_loans_widget)
        card_layout.addWidget(summary_frame)

        btn_layout = QHBoxLayout()
        cancel_btn = self._make_button("Cancelar", primary=False)
        cancel_btn.clicked.connect(self._reset_process)
        confirm_btn = self._make_button("✓  Confirmar Préstamo", primary=True)
        confirm_btn.clicked.connect(self._confirm_loan)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        card_layout.addLayout(btn_layout)
        layout.addWidget(card, alignment=Qt.AlignHCenter)
        self.stack.addWidget(w)

    # ── Lógica ────────────────────────────────────────────────────────────────
    def _search_student(self, student_id: str):
        success, message, student = self.backend.get_student_by_id(student_id)
        if success:
            self.current_student = student
            self._update_student_info(student)
            self.current_step = 1
            self.stack.setCurrentIndex(1)
            self._update_step_indicator()
        else:
            QMessageBox.warning(self, "Estudiante no encontrado", message)

    def _update_student_info(self, student):
        while self.student_info_container.count():
            item = self.student_info_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, value in [
            ("Nombre",           student.name),
            ("Matrícula",        student.student_id),
            ("Carrera",          student.career),
            ("Préstamos Activos", f"{student.active_loans} / {student.max_loans}"),
        ]:
            self.student_info_container.addWidget(InfoRow(label, value))
        if student.remaining_loans <= 2:
            w = QLabel(f"⚠ Préstamos restantes: {student.remaining_loans}")
            w.setStyleSheet(f"color:{COLORS.get('destructive','#dc2626')};margin-top:8px;border:none;")
            self.student_info_container.addWidget(w)

    def _search_material(self, material_code: str):
        success, message, material = self.backend.get_material_by_code(material_code)
        if success:
            self.current_material = material
            self._update_material_info(material)
            self.current_step = 3
            self.stack.setCurrentIndex(3)
            self._update_step_indicator()
        else:
            QMessageBox.warning(self, "Material no encontrado", message)

    def _update_material_info(self, material: MaterialInfo):
        while self.material_info_container.count():
            item = self.material_info_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, value in [
            ("Nombre",      material.name),
            ("Código",      material.code),
            ("Categoría",   material.category),
            ("Disponibles", str(material.available_stock)),
            ("Tipo",        material.control_type),
        ]:
            self.material_info_container.addWidget(InfoRow(label, value))
        self.qty_spin.setRange(1, material.available_stock)
        self.qty_spin.setValue(1)
        self._refresh_materials_list_ui()

    def _on_quantity_changed(self, value: int):
        self.current_quantity = value

    def _add_current_and_scan_more(self):
        if self.current_material:
            self.materials_list.append((self.current_material, self.current_quantity))
            self.current_material = None
            self.current_quantity = 1
            step2_widget = self.stack.widget(2)
            if step2_widget:
                inp = step2_widget.findChild(QLineEdit)
                if inp:
                    inp.clear()
            self.current_step = 2
            self.stack.setCurrentIndex(2)
            self._update_step_indicator()

    def _add_current_and_continue(self):
        if self.current_material:
            self.materials_list.append((self.current_material, self.current_quantity))
            self.current_material = None
            self.current_quantity = 1
        if not self.materials_list:
            QMessageBox.warning(self, "Sin materiales", "Agrega al menos un material.")
            return
        self._next_step()

    def _refresh_materials_list_ui(self):
        while self.materials_list_layout.count():
            item = self.materials_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.materials_list:
            empty = QLabel("(ninguno aún)")
            empty.setStyleSheet(f"color:{COLORS['muted_fg']};font-size:12px;background:transparent;border:none;")
            self.materials_list_layout.addWidget(empty)
        else:
            for mat, qty in self.materials_list:
                row = QLabel(f"• {mat.name}  ×{qty}")
                row.setStyleSheet(f"color:{COLORS['foreground']};font-size:13px;background:transparent;border:none;")
                self.materials_list_layout.addWidget(row)

    def _verify_signature(self):
        if not self.current_student:
            QMessageBox.warning(self, "Error", "No hay estudiante seleccionado")
            return
        password = self.password_input.text()
        success, message = self.backend.verify_student_password(self.current_student.student_id, password)
        if success:
            self._update_summary()
            self.current_step = 5
            self.stack.setCurrentIndex(5)
            self._update_step_indicator()
        else:
            QMessageBox.warning(self, "Firma No Verificada", message)

    def _update_summary(self):
        if not self.current_student or not self.materials_list:
            return
        becario_name = self._get_becario_name()
        summary = self.backend.get_loan_summary(self.current_student, self.materials_list, becario_name)
        self.summary_widgets["student_name"].setText(summary["student_name"])
        self.summary_widgets["student_id"].setText(summary["student_id"])
        self.summary_widgets["student_career"].setText(summary["student_career"])
        self.summary_widgets["material_display"].setText(summary["material_display"])
        self.summary_widgets["quantity"].setText(str(summary["quantity"]))
        self.summary_widgets["becario_name"].setText(summary["becario_name"])
        self.summary_widgets["loan_date"].setText(summary["loan_date"])
        self.summary_widgets["due_date"].setText(summary["due_date"])
        self.remaining_loans_widget.setText(
            f"Préstamos restantes después de este: {summary['remaining_loans']}"
        )

    def _confirm_loan(self):
        from components import ConfirmDialog
        dialog = ConfirmDialog(
            self.window(), "Confirmar Préstamo",
            "¿Deseas registrar este préstamo?\n\nEl estudiante ha autorizado con su firma digital.\nEsta acción no se puede deshacer.",
            "✓  Registrar Préstamo"
        )
        if dialog.exec() == QDialog.Accepted:
            becario_name = self._get_becario_name()
            success, message, loans = self.backend.register_loan(
                self.current_student, self.materials_list, becario_name
            )
            if success:
                QMessageBox.information(self, "Préstamo Registrado", message)
                self.loan_completed.emit(loans)
                self._reset_process()
            else:
                QMessageBox.critical(self, "Error al Registrar", message)

    def _get_becario_name(self) -> str:
        """Obtiene el nombre del usuario actualmente logueado."""
        try:
            from backend.login_backend import get_auth_backend
            auth = get_auth_backend()
            sessions = auth.get_all_active_sessions()
            if sessions:
                return sessions[0].full_name
        except Exception:
            pass
        return "Becario"

    def _next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_indicator()

    def _reset_process(self):
        self.backend.reset_process()
        self.current_step = 0
        self.current_student = None
        self.current_material = None
        self.current_quantity = 1
        self.materials_list = []
        self.password_input.clear() if hasattr(self, 'password_input') else None
        self.stack.setCurrentIndex(0)
        self._update_step_indicator()

    def _update_step_indicator(self):
        idx = self.main_layout.indexOf(self.step_widget)
        self.main_layout.removeWidget(self.step_widget)
        self.step_widget.deleteLater()
        self.step_widget = StepIndicator(self.steps, self.current_step)
        self.main_layout.insertWidget(idx, self.step_widget, alignment=Qt.AlignHCenter)

    # ── Helpers de UI ─────────────────────────────────────────────────────────
    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet(
            f"QFrame{{background:white;border:1px solid {COLORS['border']};border-radius:8px;}}"
        )
        return card

    def _create_scan_card(self, icon, title, description, placeholder, button_text) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{COLORS['background']};")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        card = self._make_card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 36, 40, 36)
        cl.setSpacing(16)
        cl.setAlignment(Qt.AlignHCenter)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(72, 72)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"background:{COLORS.get('blue_bg','#dbeafe')};color:{COLORS['primary']};"
            f"border-radius:36px;font-size:28px;border:none;"
        )
        cl.addWidget(icon_label, alignment=Qt.AlignHCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size:20px;font-weight:700;border:none;")
        cl.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color:{COLORS['muted_fg']};border:none;")
        cl.addWidget(desc_label)

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(48)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setStyleSheet(self._input_style())
        cl.addWidget(input_field)

        action_btn = QPushButton(button_text)
        action_btn.setObjectName("action_btn")
        action_btn.setFixedHeight(48)
        action_btn.setCursor(Qt.PointingHandCursor)
        action_btn.setStyleSheet(self._primary_btn_style())
        cl.addWidget(action_btn)

        layout.addWidget(card, alignment=Qt.AlignHCenter)
        return w

    def _make_button(self, text: str, primary: bool = True) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._primary_btn_style() if primary else self._secondary_btn_style())
        return btn

    def _primary_btn_style(self) -> str:
        return (
            f"QPushButton{{background:{COLORS['primary']};color:white;border:none;"
            f"border-radius:6px;font-size:14px;font-weight:600;}}"
            f"QPushButton:hover{{background:{COLORS['primary_hover']};}}"
        )

    def _secondary_btn_style(self) -> str:
        return (
            f"QPushButton{{background:{COLORS['muted']};color:{COLORS['foreground']};"
            f"border:1px solid {COLORS['border']};border-radius:6px;font-size:14px;}}"
            f"QPushButton:hover{{background:#e2e8f0;}}"
        )

    def _input_style(self) -> str:
        return (
            f"QLineEdit{{background:white;border:2px solid {COLORS['border']};"
            f"border-radius:6px;padding:8px 14px;font-size:16px;}}"
            f"QLineEdit:focus{{border:2px solid {COLORS['primary']};}}"
        )
