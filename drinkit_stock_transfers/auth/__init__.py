from .service import AuthService
from .storage import TokenStorage

auth_service = AuthService(TokenStorage())
