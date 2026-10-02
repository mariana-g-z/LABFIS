import hashlib
import re
import secrets
import string
from datetime import datetime
from backend import data_manager as dm
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

class UserRole(Enum):
    ADMIN = "Administrador"
    BECARIO = "Becario"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [role.value for role in cls]

    @classmethod
    def from_string(cls, role_str: str) -> 'UserRole':
        for role in cls:
            if role.value == role_str:
                return role
        return cls.BECARIO

class UserStatus(Enum):
    ACTIVE = "Activo"
    INACTIVE = "Inactivo"
    SUSPENDED = "Suspendido"
    LOCKED = "Bloqueado"

    @classmethod
    def get_all_values(cls) -> List[str]:
        return [status.value for status in cls]

@dataclass
class SystemUser:
    """Data class."""

    username: str
    full_name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    email: Optional[str] = None
    password_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_login: Optional[str] = None
    failed_attempts: int = 0
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['role'] = self.role.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemUser':
        data['role'] = UserRole.from_string(data['role']) if 'role' in data else UserRole.BECARIO
        data['status'] = UserStatus(data['status']) if 'status' in data else UserStatus.ACTIVE
        return cls(**data)

    def set_password(self, password: str) -> None:
        self.password_hash = self._hash_password(password)

    def verify_password(self, password: str) -> bool:
        return self.password_hash == self._hash_password(password)

    def increment_failed_attempts(self) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.status = UserStatus.LOCKED

    def reset_failed_attempts(self) -> None:
        self.failed_attempts = 0

    def update_last_login(self) -> None:
        self.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.reset_failed_attempts()

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def can_login(self) -> Tuple[bool, str]:
        if self.status == UserStatus.INACTIVE:
            return False, "Usuario inactivo"
        if self.status == UserStatus.SUSPENDED:
            return False, "Usuario suspendido"
        if self.status == UserStatus.LOCKED:
            return False, "Usuario bloqueado por múltiples intentos fallidos"
        return True, "OK"

    def get_role_display(self) -> str:
        return self.role.value

    def get_status_display(self) -> str:
        return self.status.value

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def generate_random_password(length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class AuthBackend:


    def __init__(self, user_backend: 'GestionUsuariosBackend'):
        self.user_backend = user_backend
        self.current_user: Optional[SystemUser] = None

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[SystemUser]]:

        user = self.user_backend.get_user_by_username(username)

        if not user:
            return False, "Usuario no encontrado", None

        can_login, message = user.can_login()
        if not can_login:
            return False, message, None

        if user.verify_password(password):
            user.update_last_login()
            self.current_user = user
            return True, f"Bienvenido {user.full_name}", user
        else:
            user.increment_failed_attempts()
            remaining = 5 - user.failed_attempts
            return False, f"Contraseña incorrecta. Intentos restantes: {remaining}", None

    def logout(self) -> None:
        self.current_user = None

    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def has_role(self, role: UserRole) -> bool:
        return self.is_authenticated() and self.current_user.role == role

    def get_current_user(self) -> Optional[SystemUser]:
        return self.current_user

class GestionUsuariosBackend:


    def __init__(self):
        self._users  = []
        self._loaded = False
        dm.register_reload_callback(self.reload)
        self.auth = AuthBackend(self)

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_from_file()

    def _load_from_file(self):
        """Carga usuarios del sistema desde data_manager."""
        self._users = []
        for row in dm.get_usuarios_sistema():
            try:
                role_str = str(row.get('role', '')).lower()
                role = UserRole.ADMIN if 'admin' in role_str else UserRole.BECARIO
                status_str = str(row.get('status', 'Activo')).lower()
                status = UserStatus.ACTIVE if status_str == 'activo' else UserStatus.INACTIVE
                u = SystemUser(
                    username      = str(row.get('username', '')),
                    full_name     = str(row.get('full_name', '')),
                    role          = role,
                    status        = status,
                    email         = str(row.get('email', '') or ''),
                    password_hash = str(row.get('password_hash', '') or ''),
                    notes         = str(row.get('notes', '') or ''),
                )
                self._users.append(u)
            except Exception as e:
                print(f"[GestionUsuarios] Error cargando usuario: {e}")
        self._loaded = True

    def reload(self):
        self._loaded = False
        self._users  = []
        self._load_from_file()

    def refresh_data(self):
        self.reload()

    def get_table_headers(self) -> List[str]:

        self._ensure_loaded()
        return ["Matrícula", "Nombre", "Rol", "Estado", "Acciones"]

    def get_all_users(self) -> List[SystemUser]:

        self._ensure_loaded()
        return self._users.copy()

    def get_user_by_username(self, username: str) -> Optional[SystemUser]:

        self._ensure_loaded()
        for user in self._users:
            if user.username == username:
                return user
        return None

    def search_users(self, search_text: str) -> List[SystemUser]:

        self._ensure_loaded()
        if not search_text:
            return self.get_all_users()

        search_lower = search_text.lower()
        results = []
        for user in self._users:
            if (search_lower in user.username.lower() or
                search_lower in user.full_name.lower()):
                results.append(user)
        return results

    def create_user(self, user_data: Dict[str, Any]) -> Tuple[bool, str, Optional['SystemUser']]:
        self._ensure_loaded()
        try:
            if not user_data.get('username') or not user_data.get('full_name'):
                return False, 'Username y nombre son requeridos', None
            if self.get_user_by_username(user_data['username']):
                return False, f"Ya existe un usuario con username {user_data['username']}", None
            role_str = user_data.get('role', 'Becario')
            try:
                role = UserRole.from_string(role_str)
            except (ValueError, AttributeError):
                role = UserRole.BECARIO
            new_user = SystemUser(
                username  = user_data['username'],
                full_name = user_data['full_name'],
                role      = role,
                status    = UserStatus.ACTIVE,
                email     = user_data.get('email', ''),
                notes     = user_data.get('notes', '')
            )
            if user_data.get('password'):
                new_user.set_password(user_data['password'])
            self._users.append(new_user)
            _r = dm.get_persona(new_user.username)
            if not _r:
                _r = {
                    'username': new_user.username, 'full_name': new_user.full_name,
                    'role': new_user.role.value, 'career': 'Laboratorio',
                    'email': getattr(new_user, 'email', '') or '',
                    'notes': getattr(new_user, 'notes', '') or '',
                    'status': new_user.status.value,
                    'password_hash': new_user.password_hash or '',
                    'active_loans': 0, 'created_at': ''
                }
            else:
                _r['full_name']     = new_user.full_name
                _r['role']          = new_user.role.value
                _r['email']         = getattr(new_user, 'email', '') or ''
                _r['notes']         = getattr(new_user, 'notes', '') or ''
                _r['status']        = new_user.status.value
                _r['password_hash'] = new_user.password_hash or ''
            dm.save_persona(_r)
            return True, f"Usuario {new_user.username} creado exitosamente", new_user
        except Exception as e:
            return False, f"Error al crear usuario: {str(e)}", None

    def update_user(self, username: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:

        self._ensure_loaded()
        user = self.get_user_by_username(username)
        if not user:
            return False, f"No se encontró el usuario {username}"

        # Actualizar campos permitidos
        allowed_fields = ['full_name', 'email', 'notes']
        for field in allowed_fields:
            if field in update_data:
                setattr(user, field, update_data[field])

        # Actualizar rol si viene
        if 'role' in update_data:
            try:
                new_role = UserRole.from_string(update_data['role'])
                user.role = new_role
            except ValueError:
                return False, f"Rol inválido: {update_data['role']}"

        # Actualizar estado si viene
        if 'status' in update_data:
            try:
                new_status = UserStatus(update_data['status'])
                user.status = new_status
            except ValueError:
                return False, f"Estado inválido: {update_data['status']}"

        # Actualizar contraseña si viene
        if 'password' in update_data and update_data['password']:
            user.set_password(update_data['password'])

        _r = dm.get_persona(user.username)
        if not _r:
            _r = {'username': user.username, 'full_name': user.full_name,
                   'role': user.role.value, 'career': 'Laboratorio',
                   'email': getattr(user, 'email', '') or '',
                   'notes': getattr(user, 'notes', '') or '',
                   'status': user.status.value,
                   'password_hash': user.password_hash or '',
                   'active_loans': 0, 'created_at': ''}
        else:
            _r['full_name']     = user.full_name
            _r['role']          = user.role.value
            _r['email']         = getattr(user, 'email', '') or ''
            _r['notes']         = getattr(user, 'notes', '') or ''
            _r['status']        = user.status.value
            _r['password_hash'] = user.password_hash or ''
        dm.save_persona(_r)
        _r = dm.get_persona(user.username)
        if not _r:
            _r = {
                'username': user.username, 'full_name': user.full_name,
                'role': user.role.value, 'career': 'Laboratorio',
                'email': getattr(user, 'email', '') or '',
                'notes': getattr(user, 'notes', '') or '',
                'status': user.status.value,
                'password_hash': user.password_hash or '',
                'active_loans': 0, 'created_at': ''
            }
        else:
            _r['full_name']     = user.full_name
            _r['role']          = user.role.value
            _r['email']         = getattr(user, 'email', '') or ''
            _r['notes']         = getattr(user, 'notes', '') or ''
            _r['status']        = user.status.value
            _r['password_hash'] = user.password_hash or ''
        dm.save_persona(_r)
        return True, f"Usuario {user.username} actualizado exitosamente"

    def reset_password(self, username: str, new_password: Optional[str] = None) -> Tuple[bool, str, str]:

        self._ensure_loaded()
        user = self.get_user_by_username(username)
        if not user:
            return False, f"No se encontró el usuario {username}", ""

        if new_password is None:
            new_password = SystemUser.generate_random_password()

        user.set_password(new_password)
        user.failed_attempts = 0

        _r = dm.get_persona(user.username)
        if not _r:
            _r = {'username': user.username, 'full_name': user.full_name,
                   'role': user.role.value, 'career': 'Laboratorio',
                   'email': getattr(user, 'email', '') or '',
                   'notes': getattr(user, 'notes', '') or '',
                   'status': user.status.value,
                   'password_hash': user.password_hash or '',
                   'active_loans': 0, 'created_at': ''}
        else:
            _r['full_name']     = user.full_name
            _r['role']          = user.role.value
            _r['email']         = getattr(user, 'email', '') or ''
            _r['notes']         = getattr(user, 'notes', '') or ''
            _r['status']        = user.status.value
            _r['password_hash'] = user.password_hash or ''
        dm.save_persona(_r)
        _r = dm.get_persona(user.username)
        if not _r:
            _r = {
                'username': user.username, 'full_name': user.full_name,
                'role': user.role.value, 'career': 'Laboratorio',
                'email': getattr(user, 'email', '') or '',
                'notes': getattr(user, 'notes', '') or '',
                'status': user.status.value,
                'password_hash': user.password_hash or '',
                'active_loans': 0, 'created_at': ''
            }
        else:
            _r['full_name']     = user.full_name
            _r['role']          = user.role.value
            _r['email']         = getattr(user, 'email', '') or ''
            _r['notes']         = getattr(user, 'notes', '') or ''
            _r['status']        = user.status.value
            _r['password_hash'] = user.password_hash or ''
        dm.save_persona(_r)
        return True, f"Contraseña restablecida para {user.username}", new_password

    def toggle_user_status(self, username: str) -> Tuple[bool, str]:
        self._ensure_loaded()
        user = self.get_user_by_username(username)
        if not user:
            return False, f"No se encontro el usuario {username}"
        if user.role == UserRole.ADMIN and user.status == UserStatus.ACTIVE:
            active_admins = sum(1 for u in self._users
                               if u.role == UserRole.ADMIN and u.status == UserStatus.ACTIVE)
            if active_admins <= 1:
                return False, "No se puede desactivar al unico administrador del sistema"
        if user.status == UserStatus.ACTIVE:
            user.status = UserStatus.INACTIVE
            msg = f"Usuario {user.username} desactivado"
        else:
            user.status = UserStatus.ACTIVE
            user.failed_attempts = 0
            msg = f"Usuario {user.username} activado"
        _r = dm.get_persona(user.username)
        if _r:
            _r['status'] = user.status.value
            dm.save_persona(_r)
        return True, msg

    def delete_user(self, username: str) -> Tuple[bool, str]:

        self._ensure_loaded()
        user = self.get_user_by_username(username)
        if not user:
            return False, f"No se encontró el usuario {username}"

        # No permitir eliminar al último administrador
        if user.role == UserRole.ADMIN:
            active_admins = sum(1 for u in self._users
                               if u.role == UserRole.ADMIN and u.status == UserStatus.ACTIVE)
            if active_admins <= 1:
                return False, "No se puede eliminar al único administrador del sistema"

        # Eliminar usuario
        self._users = [u for u in self._users if u.username != username]
        dm.delete_persona(username)

        return True, f"Usuario {username} eliminado del sistema"

    def get_roles(self) -> List[str]:

        return UserRole.get_all_values()

    def get_statuses(self) -> List[str]:

        return UserStatus.get_all_values()

    def get_statistics(self) -> Dict[str, Any]:

        total = len(self._users)
        active = sum(1 for u in self._users if u.status == UserStatus.ACTIVE)
        inactive = sum(1 for u in self._users if u.status == UserStatus.INACTIVE)
        admins = sum(1 for u in self._users if u.role == UserRole.ADMIN)
        becarios = sum(1 for u in self._users if u.role == UserRole.BECARIO)

        # Usuarios que han iniciado sesión recientemente (últimos 30 días)
        from datetime import timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_recently = 0
        for user in self._users:
            if user.last_login:
                try:
                    last_login_date = datetime.strptime(user.last_login.split()[0], "%Y-%m-%d")
                    if last_login_date >= thirty_days_ago:
                        active_recently += 1
                except (ValueError, IndexError):
                    pass

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'active_percentage': round(active / total * 100, 2) if total > 0 else 0,
            'admins': admins,
            'becarios': becarios,
            'active_recently': active_recently,
            'avg_failed_attempts': round(sum(u.failed_attempts for u in self._users) / total, 2) if total > 0 else 0
        }

    def get_audit_log(self, username: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:

        # En producción, esto vendría de una tabla de auditoría
        # Por ahora, retornamos datos simulados
        audit_events = []

        for user in self._users[:limit]:
            if username and user.username != username:
                continue

            if user.last_login:
                audit_events.append({
                    'timestamp': user.last_login,
                    'username': user.username,
                    'event': 'login',
                    'details': f"Inicio de sesión exitoso"
                })

            if user.failed_attempts > 0:
                audit_events.append({
                    'timestamp': user.created_at,
                    'username': user.username,
                    'event': 'failed_login_attempts',
                    'details': f"{user.failed_attempts} intentos fallidos"
                })

        # Ordenar por timestamp descendente
        audit_events.sort(key=lambda x: x['timestamp'], reverse=True)

        return audit_events[:limit]

    def export_users(self, format: str = "csv") -> str:

        if format.lower() == "csv":
            return self._export_to_csv()
        elif format.lower() == "json":
            return self._export_to_json()
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _export_to_csv(self) -> str:
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow(["Usuario", "Nombre Completo", "Rol", "Estado", "Email", "Último Login", "Notas"])

        # Escribir datos
        for user in self._users:
            writer.writerow([
                user.username,
                user.full_name,
                user.role.value,
                user.status.value,
                user.email or "",
                user.last_login or "",
                user.notes or ""
            ])

        return output.getvalue()

    def _export_to_json(self) -> str:
        import json
        data = [user.to_dict() for user in self._users]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _validate_username(self, username: str) -> bool:

        # Formato: letras minúsculas y números, 3-20 caracteres
        pattern = r'^[a-z0-9]{3,20}$'
        return bool(re.match(pattern, username))

    def get_available_username(self, base: str = "usuario") -> str:

        username = base.lower()
        if not self.get_user_by_username(username):
            return username

        counter = 1
        while self.get_user_by_username(f"{username}{counter}"):
            counter += 1
        return f"{username}{counter}"

    def refresh_data(self) -> None:

        pass

# Función helper para obtener instancia (Singleton pattern)
_backend_instance = None

def get_users_backend() -> GestionUsuariosBackend:

    global _backend_instance
    if _backend_instance is None:
        _backend_instance = GestionUsuariosBackend()
    return _backend_instance