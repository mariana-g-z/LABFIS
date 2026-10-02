import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from styles import MAIN_STYLE, COLORS
from components import Sidebar

# Import all frontend pages from the frontend module
from frontend import (
    LoginPage,
    BecarioDashboard,
    AdminDashboard,
    RegistrarPrestamoPage,
    RegistrarDevolucionPage,
    ConsultaInventarioPage,
    HistorialPrestamosPage,
    GestionEstudiantesPage,
    GestionUsuariosPage,
    GestionMaterialesPage,
    ExportarHistorialPage,
    ConfiguracionPage,
)

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación.

    Maneja la autenticación, la navegación entre páginas y la sesión del usuario.
    Los frontends están en la carpeta frontend/, los backends en backend/.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lab Manager — Laboratorio de Física")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        self._role = None          # Rol del usuario logueado
        self._sidebar = None       # Barra lateral (se crea después del login)
        self._current_page_key = None  # Página actual

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        self._root_stack = QStackedWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self._root_stack)

      
        self._login_page = LoginPage()
        self._login_page.login_success.connect(self._on_login)
        self._root_stack.addWidget(self._login_page)   # index 0

      
        self._app_shell = QWidget()
        self._app_shell.setStyleSheet(f"background: {COLORS['background']};")
        shell_layout = QHBoxLayout(self._app_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # Stack para el contenido (cambia según la navegación)
        self._content_stack = QStackedWidget()
        shell_layout.addWidget(self._content_stack, 1)

        self._root_stack.addWidget(self._app_shell)   # index 1

      
        self._pages = {}
        self._build_pages()

        # Iniciar en la pantalla de login
        self._root_stack.setCurrentIndex(0)

    def _build_pages(self):
        """Inicializa todas las páginas de contenido (frontends)."""
        page_classes = {
            "dashboard_becario": BecarioDashboard,
            "dashboard_admin": AdminDashboard,
            "prestamo": RegistrarPrestamoPage,
            "devolucion": RegistrarDevolucionPage,
            "inventario": ConsultaInventarioPage,
            "historial": HistorialPrestamosPage,
            "estudiantes": GestionEstudiantesPage,
            "usuarios": GestionUsuariosPage,
            "materiales": GestionMaterialesPage,
            "exportar": ExportarHistorialPage,
            "configuracion": ConfiguracionPage,
        }
        for key, cls in page_classes.items():
            widget = cls()  # Cada frontend tiene su propio backend interno
            self._pages[key] = widget
            self._content_stack.addWidget(widget)

        # Conectar settings_saved de Configuración para refrescar todas las páginas
        cfg_page = self._pages.get("configuracion")
        if cfg_page and hasattr(cfg_page, 'settings_saved'):
            cfg_page.settings_saved.connect(self._refresh_all_pages)

    def _on_login(self, role: str):
        """
        Maneja el login exitoso.

        Args:
            role (str): Rol del usuario ('admin' o 'becario')
        """
        self._role = role
        self._setup_sidebar(role)
        self._root_stack.setCurrentIndex(1)

        # Pasar el rol a páginas que lo necesitan
        est_page = self._pages.get("estudiantes")
        if est_page:
            est_page.set_role(role)

        # Navegar al dashboard correspondiente según el rol
        dashboard_key = "dashboard_admin" if role == "admin" else "dashboard_becario"
        self._navigate(dashboard_key)

    def _setup_sidebar(self, role: str):
        """Crea y configura la barra lateral según el rol del usuario."""
        # Crear nueva barra lateral
        self._sidebar = Sidebar(role=role)
        self._sidebar.page_changed.connect(self._navigate)

        # Items comunes para ambos roles
        common_items = [
            ("▣", "Dashboard", "dashboard_admin" if role == "admin" else "dashboard_becario"),
            ("↑", "Registrar Préstamo", "prestamo"),
            ("↓", "Registrar Devolución", "devolucion"),
            ("☰", "Consultar Inventario", "inventario"),
            ("≡", "Historial de Préstamos", "historial"),
            ("◉", "Gestión de Estudiantes", "estudiantes"),
        ]

        # Items solo para administrador
        admin_only_items = [
            ("⊞", "Gestión de Usuarios", "usuarios"),
            ("◈", "Gestión de Materiales", "materiales"),
            ("⬇", "Exportar Historial", "exportar"),
            ("⚙", "Configuración", "configuracion"),
        ]

        # Agregar items comunes
        for icon, label, page_key in common_items:
            self._sidebar.add_nav_item(icon, label, page_key)

        # Agregar items de administrador si corresponde
        if role == "admin":
            for icon, label, page_key in admin_only_items:
                self._sidebar.add_nav_item(icon, label, page_key)

        # Insertar sidebar en el layout (posición 0)
        shell_layout = self._app_shell.layout()
        self._sidebar.setFixedWidth(240)
        self._sidebar.setMinimumHeight(0)
        shell_layout.insertWidget(0, self._sidebar)

        # Configurar stretch: sidebar fijo, contenido expandible
        shell_layout.setStretch(0, 0)  # Sidebar no se expande
        shell_layout.setStretch(1, 1)  # Stack de contenido se expande

    def _navigate(self, page_key: str):
        """
        Navega a una página específica.

        Args:
            page_key (str): Identificador de la página destino
        """
        # Manejar logout (caso especial)
        if page_key == "logout":
            self._logout()
            return

        # Navegar a la página si existe
        if page_key in self._pages:
            page = self._pages[page_key]
            # Refrescar datos al entrar a páginas de gestión
            if page_key in ("materiales", "estudiantes", "inventario",
                            "historial", "exportar", "usuarios",
                            "admin_dashboard", "becario_dashboard",
                            "dashboard_admin", "dashboard_becario",
                            "dashboard"):
                if hasattr(page, 'refresh_page'):
                    page.refresh_page()
                elif hasattr(page, 'refresh_materials'):
                    page.refresh_materials()
                elif hasattr(page, 'refresh_data'):
                    page.refresh_data()
            self._content_stack.setCurrentWidget(page)
            self._current_page_key = page_key
            if self._sidebar:
                self._sidebar.set_active(page_key)

    def _refresh_all_pages(self):
        """Recarga los datos de todas las páginas después de cambiar la configuración."""
        for key, page in self._pages.items():
            if key in ("materiales", "estudiantes", "inventario",
                       "historial", "exportar", "usuarios",
                       "admin_dashboard", "becario_dashboard",
                       "dashboard_admin", "dashboard_becario",
                       "dashboard"):
                if hasattr(page, 'refresh_page'):
                    try: page.refresh_page()
                    except Exception: pass
                elif hasattr(page, 'refresh_materials'):
                    try: page.refresh_materials()
                    except Exception: pass
                elif hasattr(page, 'refresh_data'):
                    try: page.refresh_data()
                    except Exception: pass

    def _logout(self):
        """Cierra la sesión y vuelve a la pantalla de login."""
        # Limpiar campos de login
        self._login_page.clear()
        self._role = None
        self._current_page_key = None

        # Eliminar sidebar
        if self._sidebar:
            self._app_shell.layout().removeWidget(self._sidebar)
            self._sidebar.deleteLater()
            self._sidebar = None

        # Volver a la pantalla de login
        self._root_stack.setCurrentIndex(0)

def main():
    """Punto de entrada principal de la aplicación."""
    app = QApplication(sys.argv)
    app.setStyleSheet(MAIN_STYLE)

    # Fuentes compatibles con macOS (eliminar "SF Pro Text")
    font = QFont("Helvetica Neue", 10)
    if not font.exactMatch():
        font = QFont("Arial", 10)
        if not font.exactMatch():
            font = QFont("Helvetica", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()