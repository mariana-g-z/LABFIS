from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout
)
from components import (
    StatCard, SectionHeader, CardWidget, status_badge
)
from styles import COLORS

# Importar el backend
from backend.admin_dashboard_backend import get_admin_backend, TransactionType

class AdminDashboard(QScrollArea):
    """
    Vista principal del Dashboard Administrativo

    Muestra estadísticas clave, actividad reciente y materiales más utilizados.
    Separa completamente la presentación de la lógica de negocio.
    """

    def __init__(self):
        """Inicializa el dashboard y configura la interfaz"""
        super().__init__()

        # Inicializar backend
        self.backend = get_admin_backend()

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_data()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            background: {COLORS['background']};
            border: none;
        """)

        # Widget contenedor principal
        container = QWidget()
        container.setStyleSheet(f"""
            background: {COLORS['background']};
            border: none;
        """)
        self.setWidget(container)

        # Layout principal
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 28, 32, 28)
        self.main_layout.setSpacing(24)

        # Agregar encabezado
        self._add_header()

        # Espacio para estadísticas (se llenará dinámicamente)
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(16)
        self.main_layout.addLayout(self.stats_grid)

        # Sección de dos columnas
        self._add_two_columns_section()

        self.main_layout.addStretch()

    def _add_header(self):
        """Agrega el encabezado del dashboard"""
        header = SectionHeader(
            "Dashboard — Administrador",
            "Vista general del sistema de gestión"
        )
        self.main_layout.addWidget(header)

    def _add_two_columns_section(self):
        """Agrega la sección de dos columnas (actividad y materiales)"""
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(20)

        # Columna izquierda: Actividad reciente
        activity_card = self._create_activity_card()
        cols_layout.addWidget(activity_card, 1)

        # Columna derecha: Materiales más solicitados
        materials_card = self._create_top_materials_card()
        cols_layout.addWidget(materials_card, 1)

        self.main_layout.addLayout(cols_layout)

    def _create_activity_card(self) -> CardWidget:
        """
        Crea la tarjeta de actividad reciente

        Returns:
            CardWidget: Tarjeta configurada con la actividad
        """
        card = CardWidget("Actividad Reciente")
        body, _ = card.body_layout()

        # Obtener datos del backend
        activities = self.backend.get_recent_activity()

        for idx, activity in enumerate(activities):
            # Crear fila para cada actividad
            row_layout = self._create_activity_row(activity)
            body.addLayout(row_layout)

            # Agregar separador (excepto después del último elemento)
            if idx < len(activities) - 1:
                separator = self._create_separator()
                body.addWidget(separator)

        return card

    def _create_activity_row(self, activity) -> QHBoxLayout:
        """
        Crea una fila individual de actividad

        Args:
            activity: Objeto ActivityLog del backend

        Returns:
            QHBoxLayout: Layout con la información de la actividad
        """
        row = QHBoxLayout()

        # Columna izquierda: Nombre y material
        left_col = QVBoxLayout()
        left_col.setSpacing(2)

        name_label = QLabel(activity.student_name)
        name_label.setStyleSheet("border: none; background: transparent;")
        left_col.addWidget(name_label)

        material_label = QLabel(activity.material_name)
        material_label.setStyleSheet(
            f"color: {COLORS['muted_fg']}; font-size: 13px; border: none; background: transparent;"
        )
        left_col.addWidget(material_label)

        row.addLayout(left_col)
        row.addStretch()

        # Columna derecha: Tipo de transacción y hora
        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignRight)

        # Convertir el tipo de transacción a string para el badge
        transaction_str = activity.transaction_type.value
        badge = status_badge(transaction_str)
        right_col.addWidget(badge)

        time_label = QLabel(activity.time)
        time_label.setStyleSheet(
            f"color: {COLORS['muted_fg']}; font-size: 12px; border: none; background: transparent;"
        )
        time_label.setAlignment(Qt.AlignRight)
        right_col.addWidget(time_label)

        row.addLayout(right_col)

        return row

    def _create_separator(self) -> QFrame:
        """
        Crea un separador visual entre elementos

        Returns:
            QFrame: Línea separadora
        """
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(
            f"background-color: {COLORS['border']}; border: none; max-height: 1px;"
        )
        return separator

    def _create_top_materials_card(self) -> CardWidget:
        """
        Crea la tarjeta de materiales más solicitados

        Returns:
            CardWidget: Tarjeta con el ranking de materiales
        """
        card = CardWidget("Materiales en Uso")
        body, _ = card.body_layout()

        # Obtener datos del backend
        materials = self.backend.get_top_materials()

        for material in materials:
            # Fila con nombre y conteo
            row_layout = self._create_material_row(material)
            body.addLayout(row_layout)

            # Barra de progreso
            progress_bar = self._create_progress_bar(material.percentage)
            body.addWidget(progress_bar)
            body.addSpacing(6)

        return card

    def _create_material_row(self, material) -> QHBoxLayout:
        """
        Crea una fila para un material individual

        Args:
            material: Objeto MaterialStats del backend

        Returns:
            QHBoxLayout: Layout con nombre y conteo del material
        """
        row = QHBoxLayout()

        name_label = QLabel(material.name)
        name_label.setStyleSheet("border: none; background: transparent;")
        row.addWidget(name_label)
        row.addStretch()

        count_label = QLabel(f"{material.loan_count} préstamos")
        count_label.setStyleSheet(
            f"color: {COLORS['muted_fg']}; font-size: 12px; border: none; background: transparent;  border: none;"
        )
        row.addWidget(count_label)

        return row

    def _create_progress_bar(self, percentage: float) -> QFrame:
        """
        Crea una barra de progreso visual

        Args:
            percentage (float): Porcentaje de uso (0-100)

        Returns:
            QFrame: Barra de progreso estilizada
        """
        # Contenedor de la barra
        bar_container = QFrame()
        bar_container.setFixedHeight(8)
        bar_container.setStyleSheet(f"""
            background: {COLORS['muted']};
            border: none;
            border-radius: 0px;
        """)

        # Layout para el contenedor
        container_layout = QHBoxLayout(bar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Barra de relleno
        fill_bar = QFrame()
        fill_bar.setFixedHeight(8)
        fill_bar.setStyleSheet(f"""
            background: {COLORS['primary']};
            border: none;
            border-radius: 0px;
        """)

        # Calcular ancho basado en porcentaje
        width = self.backend.get_material_percentage_width(percentage, max_width=220)
        fill_bar.setFixedWidth(width)

        container_layout.addWidget(fill_bar)
        container_layout.addStretch()

        return bar_container

    def _load_data(self):
        """Carga y muestra todos los datos en la interfaz"""
        # Limpiar grid de estadísticas existente
        self._clear_layout(self.stats_grid)

        # Cargar estadísticas
        stats_data = self.backend.get_dashboard_stats()
        for i, (label, value, color_key) in enumerate(stats_data):
            color = COLORS.get(color_key, COLORS['primary'])
            stat_card = StatCard(label, value, color)
            self.stats_grid.addWidget(stat_card, i // 3, i % 3)

    def _clear_layout(self, layout):
        """
        Limpia todos los widgets de un layout

        Args:
            layout: QLayout a limpiar
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def refresh_dashboard(self):
        """
        Refresca todos los datos del dashboard
        Método público que puede ser llamado para actualizar la vista
        """
        self.backend.refresh_data()
        self._load_data()

        # Recrear las tarjetas dinámicas
        # Nota: Esto es simplificado; en producción se deberían actualizar
        # solo los componentes necesarios en lugar de recrear todo
        while self.main_layout.count() > 2:  # Mantener header y stretch
            item = self.main_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # Reconstruir la sección de dos columnas
        self._add_two_columns_section()
    def refresh_page(self):
        """Recarga el dashboard completo desde los datos reales."""
        if hasattr(self.backend, 'refresh_data'):
            self.backend.refresh_data()

        # Limpiar stat cards
        self._clear_layout(self.stats_grid)

        # Reconstruir stat cards
        stats_data = self.backend.get_dashboard_stats()
        for i, (label, value, color_key) in enumerate(stats_data):
            color = COLORS.get(color_key, COLORS['primary'])
            stat_card = StatCard(label, value, color)
            self.stats_grid.addWidget(stat_card, i // 3, i % 3)

        # Reconstruir actividad reciente y top materiales
        # Eliminar las dos tarjetas antiguas (último layout agregado)
        while self.main_layout.count() > 3:   # header + stats_grid + stretch
            item = self.main_layout.takeAt(self.main_layout.count() - 2)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # Insertar de nuevo antes del stretch
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(20)
        cols_layout.addWidget(self._create_activity_card(), 1)
        cols_layout.addWidget(self._create_top_materials_card(), 1)
        self.main_layout.insertLayout(self.main_layout.count() - 1, cols_layout)
