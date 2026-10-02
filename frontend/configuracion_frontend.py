from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QMessageBox, QGridLayout,
    QComboBox, QCheckBox, QFileDialog
)
from components import SectionHeader
from styles import COLORS

from backend.configuracion_backend import (
    get_config_backend, BackupFrequency
)

class ConfiguracionPage(QScrollArea):

    settings_saved = Signal()
    backup_created = Signal(str)

    def __init__(self):
        super().__init__()
        self.backend = get_config_backend()
        self._setup_ui()
        self._load_configurations()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background:{COLORS['background']};")
        container = QWidget()
        container.setStyleSheet(f"background:{COLORS['background']};")
        self.setWidget(container)
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 28, 32, 28)
        self.main_layout.setSpacing(24)
        self.max_width = 700

        self.main_layout.addWidget(SectionHeader("Configuración del Sistema", "Archivos de datos, respaldos y parámetros del sistema"))
        self._create_files_card()
        self._create_backup_card()
        self._create_system_info_card()
        self._add_action_buttons()
        self.main_layout.addStretch()

    # ── Tarjeta de archivos xlsx ──────────────────────────────────────────────
    def _create_files_card(self):
        card = self._card()
        card.layout().addWidget(self._card_header("Archivos de Datos (.xlsx)"))

        body = QVBoxLayout()
        body.setContentsMargins(20, 16, 20, 20)
        body.setSpacing(14)

        desc = QLabel(
            "Selecciona los archivos Excel que el sistema usará como base de datos. "
            "Al cambiar una ruta y guardar, los datos se recargan automáticamente."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{COLORS['muted_fg']};font-size:13px;border:none;")
        body.addWidget(desc)

        self._file_inputs = {}
        for key, label, default in [
            ("personas",   "Personas (usuarios y estudiantes)", "personas.xlsx"),
            ("materiales", "Materiales (inventario)",           "materiales.xlsx"),
            ("prestamos",  "Préstamos (historial)",             "prestamos.xlsx"),
            ("bajas",      "Bajas de materiales",               "bajas.xlsx"),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight:600;border:none;")
            body.addWidget(lbl)

            row = QHBoxLayout()
            inp = QLineEdit()
            inp.setFixedHeight(40)
            inp.setPlaceholderText(default)
            inp.setStyleSheet(
                f"QLineEdit{{background:white;border:1px solid {COLORS['border']};"
                f"border-radius:6px;padding:6px 10px;font-size:13px;}}"
                f"QLineEdit:focus{{border:1.5px solid {COLORS['primary']};}}"
            )
            row.addWidget(inp)

            browse_btn = QPushButton("Examinar…")
            browse_btn.setFixedHeight(40)
            browse_btn.setStyleSheet(
                f"QPushButton{{background:{COLORS['muted']};border:1px solid {COLORS['border']};"
                f"border-radius:6px;padding:6px 14px;font-size:13px;}}"
                f"QPushButton:hover{{background:#e2e8f0;}}"
            )
            # captura key en closure
            browse_btn.clicked.connect(lambda _=False, i=inp: self._browse_xlsx(i))
            row.addWidget(browse_btn)
            body.addLayout(row)
            self._file_inputs[key] = inp

        card.layout().addLayout(body)
        self.main_layout.addWidget(card, alignment=Qt.AlignHCenter)

    # ── Tarjeta de respaldos ──────────────────────────────────────────────────
    def _create_backup_card(self):
        card = self._card()
        card.layout().addWidget(self._card_header("Respaldos"))

        body = QVBoxLayout()
        body.setContentsMargins(20, 16, 20, 20)
        body.setSpacing(12)

        toggle_row = QHBoxLayout()
        labels = QVBoxLayout()
        labels.addWidget(self._bold_label("Respaldos Automáticos"))
        sub = QLabel("Copia los 4 archivos xlsx en la carpeta de respaldo")
        sub.setStyleSheet(f"color:{COLORS['muted_fg']};font-size:12px;border:none;")
        labels.addWidget(sub)
        toggle_row.addLayout(labels)
        toggle_row.addStretch()
        self.auto_backup_check = QCheckBox()
        toggle_row.addWidget(self.auto_backup_check)
        body.addLayout(toggle_row)

        body.addWidget(self._bold_label("Frecuencia"))
        self.frequency_combo = QComboBox()
        self.frequency_combo.setFixedHeight(40)
        self.frequency_combo.setStyleSheet(
            f"QComboBox{{background:white;border:1px solid {COLORS['border']};border-radius:6px;padding:6px 10px;}}"
        )
        self.frequency_combo.addItems(self.backend.get_available_frequencies())
        body.addWidget(self.frequency_combo)

        body.addWidget(self._bold_label("Carpeta de respaldo"))
        backup_row = QHBoxLayout()
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setFixedHeight(40)
        self.backup_path_input.setStyleSheet(
            f"QLineEdit{{background:white;border:1px solid {COLORS['border']};border-radius:6px;padding:6px 10px;}}"
        )
        backup_row.addWidget(self.backup_path_input)
        bb = QPushButton("Examinar…")
        bb.setFixedHeight(40)
        bb.setStyleSheet(
            f"QPushButton{{background:{COLORS['muted']};border:1px solid {COLORS['border']};border-radius:6px;padding:6px 14px;}}"
            f"QPushButton:hover{{background:#e2e8f0;}}"
        )
        bb.clicked.connect(lambda: self._browse_folder(self.backup_path_input))
        backup_row.addWidget(bb)
        body.addLayout(backup_row)

        manual_btn = QPushButton("Crear Respaldo Manual Ahora")
        manual_btn.setFixedHeight(40)
        manual_btn.setStyleSheet(
            f"QPushButton{{background:{COLORS['muted']};border:1px solid {COLORS['border']};border-radius:6px;padding:6px 16px;}}"
            f"QPushButton:hover{{background:#e2e8f0;}}"
        )
        manual_btn.clicked.connect(self._create_manual_backup)
        body.addWidget(manual_btn)

        card.layout().addLayout(body)
        self.main_layout.addWidget(card, alignment=Qt.AlignHCenter)

    # ── Tarjeta de info del sistema ───────────────────────────────────────────
    def _create_system_info_card(self):
        card = self._card()
        card.layout().addWidget(self._card_header("Información del Sistema"))

        info_grid = QGridLayout()
        info_grid.setContentsMargins(20, 16, 20, 20)
        info_grid.setSpacing(12)

        self.info_labels = {}
        for i, (label, value) in enumerate(self.backend.get_system_info().get_info_items()):
            lw = QLabel(label)
            lw.setStyleSheet(f"color:{COLORS['muted_fg']};font-size:13px;border:none;")
            info_grid.addWidget(lw, i // 2, (i % 2) * 2)
            vw = QLabel(value)
            vw.setStyleSheet("font-weight:600;border:none;")
            info_grid.addWidget(vw, i // 2, (i % 2) * 2 + 1)
            self.info_labels[label] = vw

        card.layout().addLayout(info_grid)
        self.main_layout.addWidget(card, alignment=Qt.AlignHCenter)

    # ── Botones finales ───────────────────────────────────────────────────────
    def _add_action_buttons(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        reset_btn = self._action_btn("Restablecer", COLORS['muted'], COLORS['foreground'], border=True)
        reset_btn.clicked.connect(self._reset_configurations)

        save_btn = self._action_btn("Guardar Configuración", COLORS['primary'], "white")
        save_btn.clicked.connect(self._save_configurations)

        export_btn = self._action_btn("Exportar Config", COLORS.get('stat_green','#16a34a'), "white")
        export_btn.clicked.connect(self._export_configuration)

        import_btn = self._action_btn("Importar Config", COLORS.get('stat_purple','#7c3aed'), "white")
        import_btn.clicked.connect(self._import_configuration)

        row.addStretch()
        for btn in [import_btn, export_btn, reset_btn, save_btn]:
            row.addWidget(btn)

        w = QWidget()
        w.setFixedWidth(self.max_width)
        w.setStyleSheet("background:transparent;")
        QHBoxLayout(w).addLayout(row)
        self.main_layout.addWidget(w, alignment=Qt.AlignHCenter)

    # ── Carga y guardado ──────────────────────────────────────────────────────
    def _load_configurations(self):
        fc = self.backend.get_file_config()
        self._file_inputs["personas"].setText(fc.personas_path)
        self._file_inputs["materiales"].setText(fc.materiales_path)
        self._file_inputs["prestamos"].setText(fc.prestamos_path)
        self._file_inputs["bajas"].setText(fc.bajas_path)

        bc = self.backend.get_backup_config()
        self.auto_backup_check.setChecked(bc.auto_backup)
        idx = self.frequency_combo.findText(bc.frequency.value)
        if idx >= 0:
            self.frequency_combo.setCurrentIndex(idx)
        self.backup_path_input.setText(bc.backup_path)
        self._refresh_system_info()

    def _refresh_system_info(self):
        for label, value in self.backend.get_system_info().get_info_items():
            if label in self.info_labels:
                self.info_labels[label].setText(value)

    def _save_configurations(self):
        ok, msg = self.backend.update_file_config(
            personas   = self._file_inputs["personas"].text(),
            materiales = self._file_inputs["materiales"].text(),
            prestamos  = self._file_inputs["prestamos"].text(),
            bajas      = self._file_inputs["bajas"].text(),
        )
        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return

        freq = BackupFrequency(self.frequency_combo.currentText())
        self.backend.update_backup_config(
            auto_backup  = self.auto_backup_check.isChecked(),
            frequency    = freq,
            backup_path  = self.backup_path_input.text(),
        )

        self._refresh_system_info()
        QMessageBox.information(self, "Guardado", msg)
        self.settings_saved.emit()

    def _reset_configurations(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Restablecer configuración a valores por defecto?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.backend.reset_to_defaults()
            self._load_configurations()

    def _create_manual_backup(self):
        success, msg = self.backend.create_manual_backup()
        if success:
            QMessageBox.information(self, "Respaldo", msg)
            self.backup_created.emit(msg)
            self._refresh_system_info()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _export_configuration(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Config", "config_labmanager.json", "JSON (*.json)")
        if path:
            ok, msg = self.backend.export_configuration(path)
            (QMessageBox.information if ok else QMessageBox.critical)(self, "Exportar", msg)

    def _import_configuration(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar Config", "", "JSON (*.json)")
        if path:
            reply = QMessageBox.question(self, "Confirmar", "Esto sobrescribirá la configuración actual. ¿Continuar?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                ok, msg = self.backend.import_configuration(path)
                if ok:
                    self._load_configurations()
                (QMessageBox.information if ok else QMessageBox.critical)(self, "Importar", msg)

    # ── Helpers de UI ─────────────────────────────────────────────────────────
    def _browse_xlsx(self, inp: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", inp.text() or "",
            "Excel (*.xlsx *.xls);;CSV (*.csv);;Todos (*.*)"
        )
        if path:
            inp.setText(path)

    def _browse_folder(self, inp: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", inp.text() or "")
        if folder:
            inp.setText(folder)

    def _card(self) -> QFrame:
        card = QFrame()
        card.setFixedWidth(self.max_width)
        card.setStyleSheet(
            f"QFrame{{background:white;border:1px solid {COLORS['border']};border-radius:8px;}}"
        )
        card.setLayout(QVBoxLayout())
        card.layout().setContentsMargins(0, 0, 0, 0)
        return card

    def _card_header(self, title: str) -> QLabel:
        h = QLabel(f"  {title}")
        h.setFixedHeight(52)
        h.setStyleSheet(
            f"font-size:16px;font-weight:700;"
            f"border-bottom:1px solid {COLORS['border']};padding-left:14px;border-top:none;border-left:none;border-right:none;"
        )
        return h

    def _bold_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight:600;border:none;")
        return lbl

    def _action_btn(self, text: str, bg: str, fg: str, border: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        border_css = f"border:1px solid {COLORS['border']};" if border else "border:none;"
        btn.setStyleSheet(
            f"QPushButton{{background:{bg};color:{fg};{border_css}border-radius:6px;padding:6px 18px;font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{opacity:0.9;}}"
        )
        return btn

    def refresh_page(self):
        self._load_configurations()
