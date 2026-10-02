import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from styles import COLORS
from components import add_shadow
from PySide6.QtGui import QPixmap, QPainter, QBrush
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

# Importar el backend
from backend.login_backend import get_auth_backend, LoginResult

class LoginPage(QWidget):
    """
    Página de inicio de sesión del sistema

    Permite a los usuarios autenticarse con sus credenciales
    y redirige al dashboard correspondiente según su rol.
    """

    # Señal emitida cuando el login es exitoso (rol del usuario)
    login_success = Signal(str)

    def __init__(self):
        """Inicializa la página de login"""
        super().__init__()

        # Inicializar backend de autenticación
        self.auth_backend = get_auth_backend()

        # Referencias a widgets
        self.username_input = None
        self.password_input = None
        self.error_label = None
        self.login_button = None
        self.progress_bar = None

        # Contador de intentos para mostrar ayuda
        self.attempt_count = 0

        # Configurar la interfaz
        self._setup_ui()

    def _setup_ui(self):
        """Configura la estructura básica de la interfaz"""
        self.setStyleSheet(f"background: {COLORS['background']};")

        # Layout principal (centrado)
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)

        # Tarjeta de login
        card = self._create_login_card()
        outer_layout.addWidget(card)

    def _create_login_card(self) -> QFrame:
        """Crea la tarjeta de login con todos los elementos"""
        card = QFrame()
        card.setFixedWidth(440)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Logo
        logo = self._create_logo()
        layout.addWidget(logo, alignment=Qt.AlignHCenter)

        # Títulos
        title = self._create_title()
        layout.addWidget(title)

        subtitle = self._create_subtitle()
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Campos de formulario
        self._add_form_fields(layout)

        # Mensaje de error
        self.error_label = self._create_error_label()
        layout.addWidget(self.error_label)

        # Botón de login
        self.login_button = self._create_login_button()
        layout.addWidget(self.login_button)

        # Barra de progreso (oculta inicialmente)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e2e8f0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Mensaje de ayuda
        hint = self._create_hint_label()
        layout.addWidget(hint)

        # Enlaces adicionales
        links = self._create_links()
        layout.addWidget(links)

        add_shadow(card, blur=32, opacity=0.10, y=4)
        return card


    def _create_logo(self) -> QLabel:
        size = 72
        logo = QLabel()
        logo.setFixedSize(size, size)
        logo.setAlignment(Qt.AlignCenter)

        # Sube de frontend/ a la raíz del proyecto y entra a assets/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "icon.png")

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
        logo.setStyleSheet("background: transparent;border: none;")
        return logo

    def _create_title(self) -> QLabel:
        """Crea el título principal"""
        title = QLabel("Sistema de Gestión de Préstamos")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['foreground']};
            border: none;
        """)
        return title

    def _create_subtitle(self) -> QLabel:
        """Crea el subtítulo"""
        subtitle = QLabel("Laboratorio de Física")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['muted_fg']}; border: none;")
        return subtitle

    def _add_form_fields(self, layout: QVBoxLayout):
        """Agrega los campos del formulario de login"""
        # Campo de usuario
        username_label = QLabel("Matrícula / Usuario")
        username_label.setStyleSheet(f"font-weight: 600; color: {COLORS['foreground']}; border: none;")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingresa tu matrícula")
        self.username_input.setFixedHeight(44)
        self._style_input(self.username_input)
        layout.addWidget(self.username_input)

        # Campo de contraseña
        password_label = QLabel("Contraseña")
        password_label.setStyleSheet(f"font-weight: 600; color: {COLORS['foreground']};border: none;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Ingresa tu contraseña")
        self.password_input.setFixedHeight(44)
        self._style_input(self.password_input)
        self.password_input.returnPressed.connect(self._do_login)
        layout.addWidget(self.password_input)

        # Opciones adicionales
        options_layout = QHBoxLayout()

        # Checkbox "Mostrar contraseña" (opcional)
        show_password_check = QPushButton(" Mostrar")
        show_password_check.setFlat(True)
        show_password_check.setCursor(Qt.PointingHandCursor)
        show_password_check.setStyleSheet("""
            QPushButton {
                color: #64748b;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #3b82f6;
            }
        """)
        show_password_check.clicked.connect(self._toggle_password_visibility)
        options_layout.addWidget(show_password_check)

        options_layout.addStretch()

        # Enlace "Olvidé mi contraseña"
        forgot_link = QPushButton("¿Olvidaste tu contraseña?")
        forgot_link.setFlat(True)
        forgot_link.setCursor(Qt.PointingHandCursor)
        forgot_link.setStyleSheet("""
            QPushButton {
                color: #64748b;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #3b82f6;
            }
        """)
        forgot_link.clicked.connect(self._show_forgot_password)
        options_layout.addWidget(forgot_link)

        layout.addLayout(options_layout)

    def _create_error_label(self) -> QLabel:
        """Crea la etiqueta para mensajes de error"""
        error_label = QLabel("")
        error_label.setWordWrap(True)
        error_label.setStyleSheet(f"""
            background: {COLORS.get('red_bg', '#fee2e2')};
            color: {COLORS.get('destructive', '#dc2626')};
            border: 1px solid {COLORS.get('destructive', '#dc2626')};
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 13px;

        """)
        error_label.hide()
        return error_label

    def _create_login_button(self) -> QPushButton:
        """Crea el botón de iniciar sesión"""
        btn = QPushButton("Iniciar Sesión")
        btn.setFixedHeight(46)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background: #14532d;
            }}
            QPushButton:disabled {{
                background: #94a3b8;
            }}
        """)
        btn.clicked.connect(self._do_login)
        return btn
        

    def _create_hint_label(self) -> QLabel:
        """Crea la etiqueta de ayuda con credenciales de prueba"""
        hint = QLabel(
            "<b>Credenciales de prueba:</b><br>"
            "• Administrador: <b>admin</b> / <b>admin</b><br>"
            "• Becario: <b>becario</b> / <b>becario</b>"
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            color: {COLORS['muted_fg']};
            font-size: 12px;
            padding: 10px;
            background: #f1f5f9;
            border-radius: 6px;
        """)
        return hint

    def _create_links(self) -> QWidget:
        """Crea los enlaces adicionales"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Enlace a términos y condiciones
        terms_link = QPushButton("Términos y Condiciones")
        terms_link.setFlat(True)
        terms_link.setCursor(Qt.PointingHandCursor)
        terms_link.setStyleSheet("""
            QPushButton {
                color: #64748b;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #3b82f6;
            }
        """)
        terms_link.clicked.connect(self._show_terms)

        layout.addWidget(terms_link)
        layout.addStretch()

        # Versión del sistema
        version_label = QLabel("Versión 1.0.0     ")
        version_label.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: none")
        layout.addWidget(version_label)

        return container

    def _style_input(self, widget: QLineEdit):
        """Aplica estilo a los campos de entrada"""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

    def _toggle_password_visibility(self):
        """Alterna la visibilidad de la contraseña"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def _show_forgot_password(self):
        """Muestra el diálogo de recuperación de contraseña"""
        QMessageBox.information(
            self,
            "Recuperar Contraseña",
            "Para recuperar tu contraseña, contacta al administrador del sistema.\n\n"
            "Credenciales de prueba:\n"
            "• admin / admin\n"
            "• becario / becario"
        )

    def _show_terms(self):
        """Muestra los términos y condiciones"""
        QMessageBox.information(
            self,
            "Términos y Condiciones",
            "Este sistema es de uso exclusivo para el personal autorizado del Laboratorio de Física.\n\n"
            "Queda prohibido compartir credenciales de acceso. "
            "Cada usuario es responsable de sus acciones en el sistema."
        )

    def _show_error(self, message: str):
        """Muestra un mensaje de error"""
        self.error_label.setText(message)
        self.error_label.show()

        # Ocultar después de 5 segundos
        QTimer.singleShot(5000, self.error_label.hide)

        # Efecto de vibración en el botón
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
            }}
        """)
        QTimer.singleShot(500, lambda: self._reset_button_style())

    def _reset_button_style(self):
        """Restablece el estilo del botón"""
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background: #14532d;
            }}
        """)

    def _start_loading(self):
        """Inicia la animación de carga"""
        self.login_button.setEnabled(False)
        self.login_button.setText("Iniciando sesión...")
        self.progress_bar.show()

        # Animación de progreso
        self.progress_value = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start(50)

    def _update_progress(self):
        """Actualiza la barra de progreso"""
        self.progress_value += 5
        self.progress_bar.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.progress_timer.stop()

    def _stop_loading(self):
        """Detiene la animación de carga"""
        self.login_button.setEnabled(True)
        self.login_button.setText("Iniciar Sesión")
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

    def _do_login(self):
        """Realiza el proceso de autenticación"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validar campos
        if not username or not password:
            self._show_error("Por favor ingresa usuario y contraseña.")
            return

        # Mostrar carga
        self._start_loading()

        # Pequeña pausa para mostrar la animación
        QTimer.singleShot(500, lambda: self._perform_authentication(username, password))

    def _perform_authentication(self, username: str, password: str):
        """
        Ejecuta la autenticación con el backend

        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
        """
        # Llamar al backend de autenticación
        result, session, message = self.auth_backend.authenticate(username, password)

        self._stop_loading()

        if result == LoginResult.SUCCESS:
            # Login exitoso
            self.attempt_count = 0
            self.clear()

            # Determinar rol para la señal
            role = "admin" if session and session.role.value == "admin" else "becario"

            # Emitir señal de éxito (sin messagebox bloqueante)
            self.login_success.emit(role)

        elif result == LoginResult.ACCOUNT_LOCKED:
            self.attempt_count += 1
            self._show_error(message)
            self._show_account_locked_help()

        elif result == LoginResult.ACCOUNT_INACTIVE:
            self.attempt_count += 1
            self._show_error(message)

        elif result == LoginResult.PASSWORD_EXPIRED:
            self._show_password_expired_dialog(username)

        else:  # INVALID_CREDENTIALS
            self.attempt_count += 1
            self._show_error(message)

            # Sugerir ayuda después de 3 intentos
            if self.attempt_count >= 3:
                self._show_login_help()

    def _show_account_locked_help(self):
        """Muestra ayuda para cuenta bloqueada"""
        reply = QMessageBox.question(
            self,
            "Cuenta Bloqueada",
            "Tu cuenta ha sido bloqueada temporalmente por múltiples intentos fallidos.\n\n"
            "¿Deseas contactar al administrador para desbloquearla?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "Contactar Administrador",
                "Por favor, contacta al administrador del sistema en:\n"
                "admin@laboratorio.edu\n\n"
                "Incluye tu nombre de usuario en el mensaje."
            )

    def _show_login_help(self):
        """Muestra ayuda para iniciar sesión"""
        QMessageBox.information(
            self,
            "¿Problemas para iniciar sesión?",
            "Verifica que:\n"
            "• El usuario y contraseña sean correctos\n"
            "• El bloqueo de mayúsculas no esté activado\n"
            "• Estés usando las credenciales correctas\n\n"
            "Credenciales de prueba:\n"
            "• admin / admin (Administrador)\n"
            "• becario / becario (Becario)"
        )

    def _show_password_expired_dialog(self, username: str):
        """Muestra diálogo para cambiar contraseña expirada"""
        QMessageBox.warning(
            self,
            "Contraseña Expirada",
            f"Tu contraseña ha expirado, {username}.\n\n"
            "Contacta al administrador para restablecer tu contraseña."
        )

    def clear(self):
        """Limpia los campos del formulario"""
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.hide()
        self.attempt_count = 0

    def set_default_credentials(self, username: str = "", password: str = ""):
        """Establece credenciales por defecto (útil para desarrollo)"""
        if username:
            self.username_input.setText(username)
        if password:
            self.password_input.setText(password)

    def focus_username(self):
        """Establece el foco en el campo de usuario"""
        self.username_input.setFocus()

class CambioPasswordDialog(QDialog):
    """Diálogo para cambio de contraseña"""

    def __init__(self, parent=None, username: str = ""):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Cambiar Contraseña")
        self.setFixedWidth(450)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Cambiar Contraseña")
        title.setStyleSheet("font-size: 16px; font-weight: 700; border: none;")
        layout.addWidget(title)

        info = QLabel(f"Usuario: <b>{self.username}</b>")
        info.setStyleSheet("color: #64748b;border: none;")
        layout.addWidget(info)

        layout.addSpacing(10)

        # Contraseña actual
        old_label = QLabel("Contraseña Actual *")
        old_label.setStyleSheet("font-weight: 600; border: none;")
        layout.addWidget(old_label)

        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.old_password.setFixedHeight(40)
        layout.addWidget(self.old_password)

        # Nueva contraseña
        new_label = QLabel("Nueva Contraseña *")
        new_label.setStyleSheet("font-weight: 600;border: none;")
        layout.addWidget(new_label)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setFixedHeight(40)
        layout.addWidget(self.new_password)

        # Confirmar contraseña
        confirm_label = QLabel("Confirmar Nueva Contraseña *")
        confirm_label.setStyleSheet("font-weight: 600; border: none;")
        layout.addWidget(confirm_label)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setFixedHeight(40)
        layout.addWidget(self.confirm_password)

        # Botones
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Cambiar Contraseña")
        save_btn.setStyleSheet(f"background: {COLORS['primary']}; color: white;")
        save_btn.clicked.connect(self._on_save)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def _on_save(self):
        new_pass = self.new_password.text()
        confirm_pass = self.confirm_password.text()

        if new_pass != confirm_pass:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return

        if len(new_pass) < 6:
            QMessageBox.warning(self, "Error", "La contraseña debe tener al menos 6 caracteres")
            return

        self.accept()

    def get_passwords(self):
        return {
            "old": self.old_password.text(),
            "new": self.new_password.text()
        }
