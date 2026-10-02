import hashlib
import secrets
from backend import data_manager as dm
import string
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    BECARIO = "becario"

    @classmethod
    def get_display_name(cls, role: 'UserRole') -> str:
        names = {
            cls.ADMIN: "Administrador",
            cls.BECARIO: "Becario"
        }
        return names.get(role, "Desconocido")

    @classmethod
    def from_string(cls, role_str: str) -> 'UserRole':
        for role in cls:
            if role.value == role_str:
                return role
        return cls.BECARIO

class LoginResult(Enum):
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_INACTIVE = "account_inactive"
    ACCOUNT_SUSPENDED = "account_suspended"
    PASSWORD_EXPIRED = "password_expired"

@dataclass
class UserSession:
    """Data class."""

    username: str
    role: UserRole
    full_name: str
    login_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_activity: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ip_address: Optional[str] = None

    def update_activity(self) -> None:
        self.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_session_duration(self) -> str:
        try:
            start = datetime.strptime(self.login_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            duration = now - start

            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60

            if duration.days > 0:
                return f"{duration.days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except (ValueError, TypeError):
            return "Desconocido"

@dataclass
class LoginAttempt:
    """Data class."""

    username: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    success: bool = False
    ip_address: Optional[str] = None

class AuthBackend:


    # Configuración de seguridad
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    SESSION_TIMEOUT_MINUTES = 30

    def __init__(self):
        self._users = self._initialize_users()
        dm.register_reload_callback(self.reload_users)
        self._login_attempts: Dict[str, List[LoginAttempt]] = {}
        self._active_sessions: Dict[str, UserSession] = {}
        self._locked_accounts: Dict[str, datetime] = {}

    def _initialize_users(self) -> Dict[str, Dict[str, Any]]:
        """Carga usuarios (Administrador y Becario) desde personas.xlsx."""
        users = {}
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in dm.get_usuarios_sistema():
            username = str(row.get('username', ''))
            role_str = str(row.get('role', '')).lower()
            role = UserRole.ADMIN if 'admin' in role_str else UserRole.BECARIO
            users[username] = {
                "password_hash": str(row.get('password_hash', self._hash_password(username))),
                "role": role,
                "full_name": str(row.get('full_name', username)),
                "email": str(row.get('email', '')),
                "is_active": str(row.get('status', 'Activo')).lower() == 'activo',
                "is_locked": False,
                "failed_attempts": 0,
                "last_password_change": now,
                "password_expiry_days": 90,
            }
        # Garantizar al menos admin/becario por defecto si el xlsx está vacío
        if not users:
            for uname, pwd, role, fname in [
                ("admin",   "admin",   UserRole.ADMIN,   "Administrador del Sistema"),
                ("becario", "becario", UserRole.BECARIO, "Becario de Laboratorio"),
            ]:
                users[uname] = {
                    "password_hash": self._hash_password(pwd),
                    "role": role, "full_name": fname,
                    "email": "", "is_active": True,
                    "is_locked": False, "failed_attempts": 0,
                    "last_password_change": now, "password_expiry_days": 90,
                }
        return users

    def reload_users(self):
        """Recarga usuarios desde xlsx (llamar después de cambiar rutas)."""
        self._users = self._initialize_users()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _is_account_locked(self, username: str) -> Tuple[bool, Optional[str]]:

        if username in self._locked_accounts:
            lock_time = self._locked_accounts[username]
            time_locked = datetime.now() - lock_time

            if time_locked < timedelta(minutes=self.LOCKOUT_DURATION_MINUTES):
                remaining = self.LOCKOUT_DURATION_MINUTES - int(time_locked.seconds / 60)
                return True, f"Cuenta bloqueada. Intente nuevamente en {remaining} minutos."
            else:
                # Desbloquear cuenta después del tiempo
                del self._locked_accounts[username]
                if username in self._users:
                    self._users[username]["failed_attempts"] = 0

        return False, None

    def _is_password_expired(self, username: str) -> bool:
        user = self._users.get(username)
        if not user:
            return False

        try:
            last_change = datetime.strptime(user["last_password_change"], "%Y-%m-%d %H:%M:%S")
            expiry_days = user.get("password_expiry_days", 90)
            expiry_date = last_change + timedelta(days=expiry_days)
            return datetime.now() > expiry_date
        except (ValueError, TypeError):
            return False

    def _record_login_attempt(self, username: str, success: bool, ip_address: str = None) -> None:
        attempt = LoginAttempt(username=username, success=success, ip_address=ip_address)

        if username not in self._login_attempts:
            self._login_attempts[username] = []

        self._login_attempts[username].append(attempt)

        # Mantener solo los últimos 100 intentos
        if len(self._login_attempts[username]) > 100:
            self._login_attempts[username] = self._login_attempts[username][-100:]

    def authenticate(self, username: str, password: str, ip_address: str = None) -> Tuple[LoginResult, Optional[UserSession], str]:

        # Verificar bloqueo de cuenta
        is_locked, lock_message = self._is_account_locked(username)
        if is_locked:
            self._record_login_attempt(username, False, ip_address)
            return LoginResult.ACCOUNT_LOCKED, None, lock_message

        # Buscar usuario
        user = self._users.get(username)
        if not user:
            self._record_login_attempt(username, False, ip_address)
            return LoginResult.INVALID_CREDENTIALS, None, "Usuario o contraseña incorrectos."

        # Verificar si la cuenta está activa
        if not user.get("is_active", True):
            self._record_login_attempt(username, False, ip_address)
            return LoginResult.ACCOUNT_INACTIVE, None, "Cuenta inactiva. Contacte al administrador."

        # Verificar contraseña
        if user["password_hash"] != self._hash_password(password):
            # Incrementar intentos fallidos
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1

            # Bloquear cuenta si excede intentos máximos
            if user["failed_attempts"] >= self.MAX_LOGIN_ATTEMPTS:
                self._locked_accounts[username] = datetime.now()
                self._record_login_attempt(username, False, ip_address)
                return LoginResult.ACCOUNT_LOCKED, None, f"Cuenta bloqueada por {self.LOCKOUT_DURATION_MINUTES} minutos debido a múltiples intentos fallidos."

            self._record_login_attempt(username, False, ip_address)
            remaining = self.MAX_LOGIN_ATTEMPTS - user["failed_attempts"]
            return LoginResult.INVALID_CREDENTIALS, None, f"Usuario o contraseña incorrectos. Intentos restantes: {remaining}"

        # Verificar expiración de contraseña
        if self._is_password_expired(username):
            return LoginResult.PASSWORD_EXPIRED, None, "La contraseña ha expirado. Debe cambiarla."

        # Login exitoso
        user["failed_attempts"] = 0

        # Crear sesión
        session = UserSession(
            username=username,
            role=user["role"],
            full_name=user["full_name"],
            ip_address=ip_address
        )

        # Guardar sesión activa
        self._active_sessions[username] = session

        self._record_login_attempt(username, True, ip_address)

        role_display = UserRole.get_display_name(user["role"])
        return LoginResult.SUCCESS, session, f"Bienvenido {user['full_name']} ({role_display})"

    def logout(self, username: str) -> bool:

        if username in self._active_sessions:
            del self._active_sessions[username]
            return True
        return False

    def get_active_session(self, username: str) -> Optional[UserSession]:
        session = self._active_sessions.get(username)
        if session:
            session.update_activity()
        return session

    def get_all_active_sessions(self) -> List[UserSession]:
        # Actualizar actividad y limpiar sesiones expiradas
        expired = []
        for username, session in self._active_sessions.items():
            session.update_activity()

            # Verificar timeout de sesión
            try:
                last_activity = datetime.strptime(session.last_activity, "%Y-%m-%d %H:%M:%S")
                time_inactive = datetime.now() - last_activity
                if time_inactive > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
                    expired.append(username)
            except (ValueError, TypeError):
                pass

        # Eliminar sesiones expiradas
        for username in expired:
            del self._active_sessions[username]

        return list(self._active_sessions.values())

    def get_login_attempts(self, username: str = None, limit: int = 50) -> List[LoginAttempt]:

        attempts = []
        for user, user_attempts in self._login_attempts.items():
            if username and user != username:
                continue
            attempts.extend(user_attempts)

        # Ordenar por timestamp descendente
        attempts.sort(key=lambda x: x.timestamp, reverse=True)

        return attempts[:limit]

    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:

        user = self._users.get(username)
        if not user:
            return False, "Usuario no encontrado"

        # Verificar contraseña actual
        if user["password_hash"] != self._hash_password(old_password):
            return False, "Contraseña actual incorrecta"

        # Validar nueva contraseña
        if len(new_password) < 6:
            return False, "La nueva contraseña debe tener al menos 6 caracteres"

        if new_password == old_password:
            return False, "La nueva contraseña debe ser diferente a la actual"

        # Actualizar contraseña
        user["password_hash"] = self._hash_password(new_password)
        user["last_password_change"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user["failed_attempts"] = 0

        return True, "Contraseña cambiada exitosamente"

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:

        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "La contraseña debe contener mayúsculas, minúsculas y números"

        return True, "Contraseña válida"

    def generate_temp_password(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(10))

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        user = self._users.get(username)
        if not user:
            return None

        return {
            "username": username,
            "full_name": user["full_name"],
            "role": user["role"],
            "email": user.get("email", ""),
            "is_active": user.get("is_active", True),
            "failed_attempts": user.get("failed_attempts", 0),
            "last_password_change": user.get("last_password_change", "")
        }

    def has_active_session(self, username: str) -> bool:
        return username in self._active_sessions

    def get_security_stats(self) -> Dict[str, Any]:
        total_attempts = sum(len(attempts) for attempts in self._login_attempts.values())
        failed_attempts = sum(
            len([a for a in attempts if not a.success])
            for attempts in self._login_attempts.values()
        )

        return {
            "total_login_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "failed_percentage": round(failed_attempts / total_attempts * 100, 2) if total_attempts > 0 else 0,
            "active_sessions": len(self._active_sessions),
            "locked_accounts": len(self._locked_accounts),
            "max_login_attempts": self.MAX_LOGIN_ATTEMPTS,
            "lockout_duration_minutes": self.LOCKOUT_DURATION_MINUTES,
            "session_timeout_minutes": self.SESSION_TIMEOUT_MINUTES
        }

# Función helper para obtener instancia (Singleton pattern)
_auth_backend_instance = None

def get_auth_backend() -> AuthBackend:

    global _auth_backend_instance
    if _auth_backend_instance is None:
        _auth_backend_instance = AuthBackend()
    return _auth_backend_instance