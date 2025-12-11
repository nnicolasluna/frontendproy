import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from models.models import User
from database import db

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def create_tokens(user: User):
        """Create access and refresh tokens for a user"""
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }

    @staticmethod
    def authenticate_user(username: str, password: str) -> User | None:
        """Authenticate a user by username and password"""
        user = User.query.filter_by(username=username).first()
        if user and AuthService.verify_password(password, user.password_hash):
            if not user.activo:
                raise Exception("Usuario inactivo")
            return user
        return None
