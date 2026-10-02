from .login_backend import get_auth_backend, AuthBackend, LoginResult
from .gestion_usuarios_backend import get_users_backend, GestionUsuariosBackend
from .gestion_materiales_backend import get_materials_backend, GestionMaterialesBackend
from .gestion_estudiantes_backend import get_students_backend, GestionEstudiantesBackend
from .exportar_historial_backend import get_export_backend, ExportarHistorialBackend
from .configuracion_backend import get_config_backend, ConfiguracionBackend
from .historial_prestamos_backend import get_historial_backend, HistorialPrestamosBackend
from .registrar_prestamo_backend import get_prestamo_backend, RegistrarPrestamoBackend
from .registrar_devolucion_backend import get_devolucion_backend, RegistrarDevolucionBackend
from .consulta_inventario_backend import get_inventory_backend, ConsultaInventarioBackend

__all__ = [
    # Auth
    "get_auth_backend",
    "AuthBackend",
    "LoginResult",
    # Users
    "get_users_backend",
    "GestionUsuariosBackend",
    # Materials
    "get_materials_backend",
    "GestionMaterialesBackend",
    # Students
    "get_students_backend",
    "GestionEstudiantesBackend",
    # Export
    "get_export_backend",
    "ExportarHistorialBackend",
    # Config
    "get_config_backend",
    "ConfiguracionBackend",
    # History
    "get_historial_backend",
    "HistorialPrestamosBackend",
    # Loan
    "get_prestamo_backend",
    "RegistrarPrestamoBackend",
    # Return
    "get_devolucion_backend",
    "RegistrarDevolucionBackend",
    # Inventory
    "get_inventory_backend",
    "ConsultaInventarioBackend",
]