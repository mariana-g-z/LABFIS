from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDialog, QMessageBox, QComboBox,
    QSpinBox, QTextEdit, QFormLayout, QFileDialog, QGridLayout, QHeaderView
)
from components import SectionHeader, LabTable, SearchBar
from styles import COLORS

# Importar el backend
from backend.gestion_materiales_backend import (
    get_materials_backend, Material, MaterialStatus
)

class GestionMaterialesPage(QWidget):
    """
    Página de Gestión de Materiales

    Permite administrar el catálogo de materiales del laboratorio,
    realizar operaciones CRUD y ver su historial de préstamos.
    """

    # Señales para comunicación
    material_added = Signal(object)   # Emitida cuando se agrega un material
    material_updated = Signal(object) # Emitida cuando se actualiza un material
    material_deleted = Signal(str)    # Emitida cuando se elimina un material

    def __init__(self):
        """Inicializa la página de gestión de materiales"""
        super().__init__()

        # Inicializar backend
        self.backend = get_materials_backend()

        # Referencias a widgets
        self.search_bar = None
        self.materials_table = None

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_materials()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Botón de agregar material
        add_btn = self._create_add_button()

        # Agregar encabezado con botón
        header = SectionHeader(
            "Gestión de Materiales",
            "Administra el catálogo de materiales del laboratorio",
            add_btn
        )
        main_layout.addWidget(header)

        # Barra de búsqueda
        self.search_bar = SearchBar("Buscar por nombre o código...")
        self.search_bar.textChanged.connect(self._on_search)
        main_layout.addWidget(self.search_bar)

        # Tabla de materiales
        self.materials_table = self._create_materials_table()

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
        table_layout.addWidget(self.materials_table)

        main_layout.addWidget(table_container, 1)

    def _create_add_button(self) -> QPushButton:
        """Crea el botón de agregar material"""
        btn = QPushButton("＋  Agregar Material")
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

    def _create_materials_table(self) -> LabTable:
        """Crea la tabla de materiales con sus columnas"""
        headers = self.backend.get_table_headers()
        table = LabTable(headers)

        # Código, Nombre, Categoría, Tipo Control, Existencias, Estado, Acciones
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 100)   # Código
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        table.setColumnWidth(2, 130)   # Categoría
        table.setColumnWidth(3, 120)   # Tipo Control
        table.setColumnWidth(4, 80)    # Existencias (pequeña)
        table.setColumnWidth(5, 115)   # Estado
        table.setColumnWidth(6, 160)   # Acciones (iconos)

        # Conectar señal de clic
        table.clicked.connect(self._on_table_click)

        return table

    def _load_materials(self, materials: list = None):
        """
        Carga los materiales en la tabla

        Args:
            materials (list, optional): Lista de materiales a mostrar
        """
        if materials is None:
            materials = self.backend.get_all_materials()

        self.materials_table.setRowCount(len(materials))

        for i, material in enumerate(materials):
            # Código (monoespaciado)
            self.materials_table.add_item(i, 0, material.code, mono=True)

            # Nombre
            self.materials_table.add_item(i, 1, material.name)

            # Categoría
            self.materials_table.add_item(i, 2, material.category)

            # Tipo Control
            self.materials_table.add_item(i, 3, material.control_type)

            # Existencias
            stock_text = str(material.stock)
            if material.is_low_stock() and material.stock > 0:
                stock_text = f"[!] {material.stock}"
            elif material.stock == 0:
                stock_text = f"[x] {material.stock}"
            self.materials_table.add_item(i, 4, stock_text)

            # Estado (con badge)
            status_text = material.get_status_display()
            self.materials_table.set_badge_item(i, 5, status_text)

            # Acciones (botones)
            actions = self._get_material_actions(material)
            self.materials_table.add_actions(i, 6, actions)

    def _get_material_actions(self, material: Material) -> list:
        actions = [
            ("Ver Historial", lambda m=material: self._show_loan_history(m.code), False),
        ]
        if material.is_active():
            if material.stock == 0:
                actions.append(("Reabastecer", lambda m=material: self._restock_material(m), False))
            actions.append(("Editar", lambda m=material: self._show_edit_dialog(m), False))
            actions.append(("Dar de Baja", lambda m=material: self._toggle_status(m), True))
        else:
            actions.append(("Reactivar", lambda m=material: self._toggle_status(m), False))
        actions.append(("Eliminar", lambda m=material: self._delete_material(m), True))
        return actions

    def _restock_material(self, material: Material):
        dialog = RestockDialog(self, material)
        if dialog.exec() == QDialog.Accepted:
            quantity = dialog.get_quantity()
            # ✅ Calcular nuevo stock sin usar update_stock (que valida max_stock=100)
            new_stock = material.stock + quantity
            success, message = self.backend.update_material(
                material.code, {'stock': new_stock}
            )
            if success:
                QMessageBox.information(
                    self, "Éxito",
                    f"Se agregaron {quantity} unidades. Stock actual: {new_stock}"
                )
                self._load_materials()
            else:
                QMessageBox.critical(self, "Error", message)

    def _toggle_status(self, material: Material):
        # ✅ Recargar del backend por si el objeto está desactualizado
        fresh = self.backend.get_material_by_code(material.code)
        if not fresh:
            QMessageBox.warning(self, "Error", "El material ya no existe.")
            self._load_materials()
            return
        success, message = self.backend.toggle_material_status(fresh.code)
        if success:
            QMessageBox.information(self, "Éxito", message)
            self._load_materials()
        else:
            QMessageBox.warning(self, "Advertencia", message)

    def _on_search(self, text: str):
        """Manejador de búsqueda de materiales"""
        results = self.backend.search_materials(text)
        self._load_materials(results)

    def _on_table_click(self, index):
        """Manejador de clic en la tabla"""
        pass

    def _show_add_dialog(self):
        """Muestra el diálogo para agregar un nuevo material"""
        dialog = MaterialDialog(self, self.backend)
        if dialog.exec() == QDialog.Accepted:
            material_data = dialog.get_material_data()
            success, message, material = self.backend.add_material(material_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_materials()
                self.material_added.emit(material)
            else:
                QMessageBox.critical(self, "Error", message)

    def _show_edit_dialog(self, material: Material):
        """Muestra el diálogo para editar un material"""
        dialog = MaterialDialog(self, self.backend, material)
        if dialog.exec() == QDialog.Accepted:
            update_data = dialog.get_update_data()
            success, message = self.backend.update_material(material.code, update_data)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_materials()
                self.material_updated.emit(material)
            else:
                QMessageBox.critical(self, "Error", message)

    def _toggle_status(self, material: Material):
        """Cambia el estado de un material"""
        success, message = self.backend.toggle_material_status(material.code)

        if success:
            QMessageBox.information(self, "Éxito", message)
            self._load_materials()
        else:
            QMessageBox.warning(self, "Advertencia", message)

    def _restock_material(self, material: Material):
        """Reabastece un material"""
        dialog = RestockDialog(self, material)
        if dialog.exec() == QDialog.Accepted:
            quantity = dialog.get_quantity()
            success, message = material.update_stock(quantity)

            if success:
                self.backend.update_material(material.code, {'stock': material.stock})
                QMessageBox.information(self, "Éxito", f"Se agregaron {quantity} unidades. Stock actual: {material.stock}")
                self._load_materials()
            else:
                QMessageBox.critical(self, "Error", message)

    def _delete_material(self, material: Material):
        """Elimina un material del catálogo"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar el material {material.name}?\n\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.backend.delete_material(material.code)

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_materials()
                self.material_deleted.emit(material.code)
            else:
                QMessageBox.critical(self, "Error", message)

    def _show_loan_history(self, material_code: str):
        """Muestra el historial de préstamos de un material"""
        material = self.backend.get_material_by_code(material_code)
        if not material:
            return

        history = self.backend.get_material_loan_history(material_code)

        # Crear diálogo de historial
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historial de Préstamos - {material.name}")
        dialog.setMinimumSize(800, 500)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Información del material
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {COLORS['muted']}; border-radius: 8px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)

        active_loans = self.backend.get_active_loans_count(material_code)
        info_text = QLabel(
            f"<b>Código:</b> {material.code}<br>"
            f"<b>Nombre:</b> {material.name}<br>"
            f"<b>Categoría:</b> {material.category}<br>"
            f"<b>Stock actual:</b> {material.stock}<br>"
            f"<b>Préstamos activos:</b> {active_loans}"
        )
        info_layout.addWidget(info_text)
        layout.addWidget(info_frame)

        # Tabla de historial
        headers = ["ID Préstamo", "Estudiante", "Fecha Préstamo", "Fecha Devolución", "Cantidad", "Estado"]
        history_table = LabTable(headers)
        history_table.setRowCount(len(history))

        for i, loan in enumerate(history):
            history_table.add_item(i, 0, loan.loan_id, mono=True)
            history_table.add_item(i, 1, loan.student_name)
            history_table.add_item(i, 2, loan.loan_date.split()[0] if loan.loan_date else "")
            history_table.add_item(i, 3, loan.return_date.split()[0] if loan.return_date else "-")
            history_table.add_item(i, 4, str(loan.quantity))
            history_table.set_badge_item(i, 5, loan.status)

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

    def refresh_materials(self):
        """Refresca la lista de materiales"""
        self.backend.refresh_data()
        self._load_materials()

    def export_materials(self):
        """Exporta la lista de materiales"""
        # Diálogo para elegir formato
        export_dialog = QMessageBox(self)
        export_dialog.setWindowTitle("Exportar Materiales")
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
            "Exportar Materiales",
            f"materiales_laboratorio.{format_type}",
            file_filter
        )

        if file_path:
            try:
                export_data = self.backend.export_materials(format_type)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_data)

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Materiales exportados a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar: {str(e)}"
                )

    def show_low_stock_alert(self):
        """Muestra alerta de materiales con bajo stock"""
        low_stock = self.backend.get_low_stock_materials()

        if not low_stock:
            QMessageBox.information(
                self,
                "Stock Normal",
                "No hay materiales con bajo stock en este momento."
            )
            return

        message = "<b>Materiales con Bajo Stock:</b><br><br>"
        for material in low_stock:
            message += f"• {material.name} ({material.code}): {material.stock} unidades (mínimo: {material.min_stock})<br>"

        QMessageBox.warning(self, "Alerta de Bajo Stock", message)

class MaterialDialog(QDialog):
    """
    Diálogo para registrar o editar un material
    """

    def __init__(self, parent, backend, material: Material = None):
        """
        Inicializa el diálogo

        Args:
            parent: Widget padre
            backend: Instancia del backend
            material (Material, optional): Material a editar
        """
        super().__init__(parent)
        self.backend = backend
        self.material = material
        self.is_edit = material is not None

        self.setWindowTitle("Editar Material" if self.is_edit else "Alta de Material")
        self.setMinimumWidth(600)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: white; }")

        self._setup_ui()

        if self.is_edit:
            self._load_material_data()

    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Título
        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size: 18px; font-weight: 700; border: none;")
        layout.addWidget(title)

        # Formulario en grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # Campos del formulario
        row = 0

        # Código
        lbl_code = QLabel("Código *")
        lbl_code.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_code, row, 0)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Ej: MUL-002")
        self.code_input.setFixedHeight(42)
        self.code_input.setStyleSheet(self._input_style())
        if not self.is_edit:
            grid.addWidget(self.code_input, row, 1)
        else:
            code_label = QLabel(self.material.code)
            code_label.setStyleSheet("font-weight: 600; padding: 8px; border: none;")
            grid.addWidget(code_label, row, 1)

        # Nombre
        lbl_name = QLabel("Nombre *")
        lbl_name.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_name, row, 2)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del material")
        self.name_input.setFixedHeight(42)
        self.name_input.setStyleSheet(self._input_style())
        grid.addWidget(self.name_input, row, 3)

        row += 1

        # Categoría
        lbl_category = QLabel("Categoría *")
        lbl_category.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_category, row, 0)

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.backend.get_categories())
        self.category_combo.setFixedHeight(42)
        self.category_combo.setStyleSheet(self._combo_style())
        grid.addWidget(self.category_combo, row, 1)

        # Tipo Control
        lbl_control = QLabel("Tipo Control *")
        lbl_control.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_control, row, 2)

        self.control_combo = QComboBox()
        self.control_combo.addItems(self.backend.get_control_types())
        self.control_combo.setFixedHeight(42)
        self.control_combo.setStyleSheet(self._combo_style())
        grid.addWidget(self.control_combo, row, 3)

        row += 1

        # Stock
        lbl_stock = QLabel("Stock Inicial *")
        lbl_stock.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_stock, row, 2)

        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999)
        self.stock_spin.setFixedHeight(42)
        self.stock_spin.setStyleSheet(self._spin_style())
        grid.addWidget(self.stock_spin, row, 3)

        row += 1

        # Stock Mínimo
        lbl_min = QLabel("Stock Mínimo")
        lbl_min.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_min, row, 0)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 100)
        self.min_stock_spin.setValue(5)
        self.min_stock_spin.setFixedHeight(42)
        self.min_stock_spin.setStyleSheet(self._spin_style())
        grid.addWidget(self.min_stock_spin, row, 1)

        # Stock Máximo
        lbl_max = QLabel("Stock Máximo")
        lbl_max.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        grid.addWidget(lbl_max, row, 2)

        self.max_stock_spin = QSpinBox()
        self.max_stock_spin.setRange(1, 1000)
        self.max_stock_spin.setValue(100)
        self.max_stock_spin.setFixedHeight(42)
        self.max_stock_spin.setStyleSheet(self._spin_style())
        grid.addWidget(self.max_stock_spin, row, 3)

        layout.addLayout(grid)

        # Descripción
        desc_label = QLabel("Descripción")
        desc_label.setStyleSheet("font-weight: 600; font-size: 13px; border: none;")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descripción detallada del material...")
        self.description_input.setFixedHeight(80)
        self.description_input.setStyleSheet(self._textarea_style())
        layout.addWidget(self.description_input)

        layout.addSpacing(10)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(self._cancel_style())
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Guardar Material")
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

    def _spin_style(self) -> str:
        return f"""
            QSpinBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QSpinBox:focus {{
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

    def _load_material_data(self):
        """Carga los datos del material en el formulario"""
        if not self.material:
            return

        self.name_input.setText(self.material.name)

        index = self.category_combo.findText(self.material.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        index = self.control_combo.findText(self.material.control_type)
        if index >= 0:
            self.control_combo.setCurrentIndex(index)

        self.location_input.setText(self.material.location)
        self.stock_spin.setValue(self.material.stock)
        self.min_stock_spin.setValue(self.material.min_stock)
        self.max_stock_spin.setValue(self.material.max_stock)

        if self.material.description:
            self.description_input.setText(self.material.description)

    def get_material_data(self) -> dict:
        """Obtiene los datos del material del formulario"""
        return {
            'code': self.code_input.text().strip().upper(),
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'control_type': self.control_combo.currentText(),
            'stock': self.stock_spin.value(),
            'description': self.description_input.toPlainText().strip(),
            'min_stock': self.min_stock_spin.value(),
            'max_stock': self.max_stock_spin.value()
        }

    def get_update_data(self) -> dict:
        """Obtiene los datos para actualizar"""
        return {
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'control_type': self.control_combo.currentText(),
            'stock': self.stock_spin.value(),
            'description': self.description_input.toPlainText().strip(),
            'min_stock': self.min_stock_spin.value(),
            'max_stock': self.max_stock_spin.value()
        }

    def _on_save(self):
        """Manejador del botón guardar"""
        if not self.is_edit:
            if not self.code_input.text().strip():
                QMessageBox.warning(self, "Validación", "El código es requerido")
                return

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre es requerido")
            return

        self.accept()

class RestockDialog(QDialog):
    """Diálogo para reabastecer un material"""

    def __init__(self, parent, material: Material):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle(f"Reabastecer - {material.name}")
        self.setFixedWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Información actual
        info = QLabel(f"Stock actual: <b>{material.stock}</b> unidades")
        layout.addWidget(info)

        # Cantidad a agregar
        lbl = QLabel("Cantidad a agregar:")
        lbl.setStyleSheet("font-weight: 600; border: none;")
        layout.addWidget(lbl)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(10)
        layout.addWidget(self.quantity_spin)

        # Botones
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        add_btn = QPushButton("Agregar")
        add_btn.setStyleSheet(f"background: {COLORS['primary']}; color: white;")
        add_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(add_btn)
        layout.addLayout(buttons)

    def get_quantity(self) -> int:
        return self.quantity_spin.value()
    def refresh_page(self):
        if hasattr(self.backend, 'reload'):
            self.backend.reload()
        self._load_materials()
