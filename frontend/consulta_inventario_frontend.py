from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QMessageBox, QFileDialog
)
from components import SectionHeader, CardWidget, LabTable, SearchBar
from styles import COLORS

# Importar el backend
from backend.consulta_inventario_backend import (
    get_inventory_backend, FilterCriteria, MaterialCategory,
    MaterialLocation, MaterialStatus
)

class ConsultaInventarioPage(QWidget):
    """
    Página de Consulta de Inventario

    Permite visualizar y filtrar el inventario de materiales del laboratorio.
    Separa completamente la presentación de la lógica de negocio.
    """

    # Señales para comunicación
    inventory_filtered = Signal(int)  # Emitida cuando se filtran resultados (número de resultados)
    material_selected = Signal(str)   # Emitida cuando se selecciona un material (código)

    def __init__(self):
        """Inicializa la página de consulta de inventario"""
        super().__init__()

        # Inicializar backend
        self.backend = get_inventory_backend()

        # Referencias a widgets
        self.search_bar = None
        self.category_combo = None
        self.location_combo = None
        self.status_combo = None
        self.inventory_table = None
        self.footer_label = None

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_inventory()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Agregar encabezado
        self._add_header(main_layout)

        # Agregar filtros
        self._add_filters_card(main_layout)

        # Agregar tabla de inventario
        self._add_inventory_table(main_layout)

        main_layout.addStretch()

    def _add_header(self, layout: QVBoxLayout):
        """Agrega el encabezado de la página"""
        header = SectionHeader(
            "Consulta de Inventario",
            "Visualiza el estado del inventario de materiales"
        )
        layout.addWidget(header)

    def _add_filters_card(self, layout: QVBoxLayout):
        """Agrega la tarjeta de filtros"""
        # Contenedor de filtros
        filters_card = QFrame()
        filters_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        # Layout horizontal para filtros
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(12)

        # Barra de búsqueda
        self.search_bar = SearchBar("Buscar por nombre o código...")
        self.search_bar.textChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.search_bar, 2)

        # Combo de categoría
        self.category_combo = self._create_filter_combo()
        categories = self.backend.get_categories()
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.category_combo, 1)

        # Combo de estado
        self.status_combo = self._create_filter_combo()
        statuses = self.backend.get_statuses()
        self.status_combo.addItems(statuses)
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.status_combo, 1)

        # Botón para limpiar filtros
        clear_btn = QPushButton("Limpiar Filtros")
        clear_btn.setFixedHeight(44)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: #e2e8f0;
            }}
        """)
        clear_btn.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_btn)

        layout.addWidget(filters_card)

    def _add_inventory_table(self, layout: QVBoxLayout):
        """Agrega la tabla de inventario con su contenedor"""
        # Crear tabla
        headers = self.backend.get_table_headers()
        self.inventory_table = LabTable(headers)

        # Crear footer
        self.footer_label = QLabel()
        self.footer_label.setStyleSheet(
            f"color: {COLORS['muted_fg']}; font-size: 13px; padding: 8px 16px; border: none;"
        )

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
        table_layout.addWidget(self.inventory_table)
        table_layout.addWidget(self.footer_label)

        # Conectar señal de selección
        self.inventory_table.clicked.connect(self._on_material_selected)

        layout.addWidget(table_container, 1)

    def _create_filter_combo(self) -> QComboBox:
        """Crea un combo box estilizado para filtros"""
        combo = QComboBox()
        combo.setFixedHeight(44)
        combo.setMinimumWidth(160)
        combo.setStyleSheet(f"""
            QComboBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        return combo

    def _get_current_filters(self) -> FilterCriteria:
        """
        Obtiene los filtros actuales de la UI

        Returns:
            FilterCriteria: Criterios de filtrado actuales
        """
        return FilterCriteria(
            search_text=self.search_bar.text(),
            category=self.category_combo.currentText(),
            location="",
            status=self.status_combo.currentText()
        )

    def _on_filter_changed(self):
        """Manejador de cambios en los filtros"""
        filters = self._get_current_filters()
        self._load_inventory(filters)

    def _clear_filters(self):
        """Limpia todos los filtros"""
        self.search_bar.clear()
        self.category_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)

    def _load_inventory(self, filters: Optional[FilterCriteria] = None):
        """
        Carga el inventario en la tabla aplicando filtros

        Args:
            filters (Optional[FilterCriteria]): Filtros a aplicar
        """
        # Obtener materiales filtrados
        if filters is None:
            materials = self.backend.get_all_materials()
            total_count = len(materials)
        else:
            materials = self.backend.get_filtered_materials(filters)
            total_count = len(self.backend.get_all_materials())

        # Configurar la tabla
        self.inventory_table.setRowCount(len(materials))

        for i, material in enumerate(materials):
            # Código (monoespaciado)
            self.inventory_table.add_item(i, 0, material.code, mono=True)

            # Nombre
            self.inventory_table.add_item(i, 1, material.name)

            # Categoría
            self.inventory_table.add_item(i, 2, material.category)

            # Existencias (cantidad disponible)
            self.inventory_table.add_item(i, 3, str(material.available_quantity))

            # Prestados
            self.inventory_table.add_item(i, 4, str(material.borrowed_quantity))

            # Estado (con badge de color)
            self.inventory_table.set_badge_item(i, 5, material.status)

        # Actualizar footer
        showing_count = len(materials)
        self.footer_label.setText(
            f"Mostrando <b>{showing_count}</b> de <b>{total_count}</b> materiales"
        )

        # Emitir señal con número de resultados
        self.inventory_filtered.emit(showing_count)

    def _on_material_selected(self, index):
        """
        Manejador de selección de material en la tabla

        Args:
            index: Índice del elemento seleccionado
        """
        if index.isValid():
            row = index.row()
            # Obtener código del material de la primera columna
            code_item = self.inventory_table.item(row, 0)
            if code_item:
                material_code = code_item.text()
                self.material_selected.emit(material_code)

                # Opcional: mostrar detalles del material
                self._show_material_details(material_code)

    def _show_material_details(self, material_code: str):
        """
        Muestra detalles de un material en un diálogo

        Args:
            material_code (str): Código del material
        """
        material = self.backend.get_material_by_code(material_code)
        if not material:
            return

        # Crear mensaje con detalles
        details = f"""
        <b>Detalles del Material</b><br><br>
        <b>Código:</b> {material.code}<br>
        <b>Nombre:</b> {material.name}<br>
        <b>Categoría:</b> {material.category}<br>
        <b>Ubicación:</b> —<br>
        <b>Existencias:</b> {material.available_quantity}<br>
        <b>Prestados:</b> {material.borrowed_quantity}<br>
        <b>Total:</b> {material.total_quantity}<br>
        <b>Estado:</b> {material.status}<br>
        <b>Disponibilidad:</b> {material.availability_percentage:.1f}%<br>
        """

        QMessageBox.information(self, "Detalles del Material", details)

    def refresh_inventory(self):
        """Método público para refrescar el inventario"""
        self.backend.refresh_data()
        self._load_inventory(self._get_current_filters())

    def refresh_page(self):
        """Alias para que main.py pueda refrescar la página."""
        if hasattr(self.backend, 'reload'):
            self.backend.reload()
        elif hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()
        self._load_inventory(self._get_current_filters())

    def export_inventory(self):
        """Exporta el inventario a archivo"""
        # Diálogo para elegir formato
        export_dialog = QMessageBox(self)
        export_dialog.setWindowTitle("Exportar Inventario")
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
            "Exportar Inventario",
            f"inventario_laboratorio.{format_type}",
            file_filter
        )

        if file_path:
            try:
                export_data = self.backend.export_inventory(format_type)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_data)

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Inventario exportado a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar: {str(e)}"
                )

    def get_low_stock_materials(self):
        """Obtiene y muestra materiales con bajo stock"""
        low_stock = self.backend.get_low_stock_materials()

        if not low_stock:
            QMessageBox.information(
                self,
                "Bajo Stock",
                "No hay materiales con bajo stock en este momento."
            )
            return

        # Mostrar lista de materiales con bajo stock
        message = "<b>Materiales con Bajo Stock:</b><br><br>"
        for material in low_stock:
            message += f"• {material.name} ({material.code}): {material.available_quantity} unidades disponibles<br>"

        QMessageBox.warning(self, "Alerta de Bajo Stock", message)

    def search_material(self, search_text: str):
        """
        Busca materiales por texto

        Args:
            search_text (str): Texto a buscar
        """
        self.search_bar.setText(search_text)

    def filter_by_category(self, category: str):
        """
        Filtra materiales por categoría

        Args:
            category (str): Categoría a filtrar
        """
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    def filter_by_status(self, status: str):
        """
        Filtra materiales por estado

        Args:
            status (str): Estado a filtrar
        """
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)