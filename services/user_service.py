from models.models import User
from database import db
from services.auth_service import AuthService

class UserService:
    @staticmethod
    def crear_usuario(username, email, password, nombre_completo=None, es_admin=False):
        """Crear un nuevo usuario"""
        if User.query.filter_by(username=username).first():
            raise Exception("El nombre de usuario ya existe")
        
        if User.query.filter_by(email=email).first():
            raise Exception("El correo electrónico ya existe")
            
        password_hash = AuthService.hash_password(password)
        
        nuevo_usuario = User(
            username=username,
            email=email,
            password_hash=password_hash,
            nombre_completo=nombre_completo,
            es_admin=es_admin
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        return nuevo_usuario

    @staticmethod
    def listar_usuarios():
        """Listar todos los usuarios"""
        return User.query.order_by(User.id).all()

    @staticmethod
    def obtener_usuario(user_id):
        """Obtener usuario por ID"""
        return User.query.get(user_id)

    @staticmethod
    def actualizar_usuario(user_id, data):
        """Actualizar datos de usuario"""
        usuario = User.query.get(user_id)
        if not usuario:
            raise Exception("Usuario no encontrado")
            
        if 'nombre_completo' in data:
            usuario.nombre_completo = data['nombre_completo']
            
        if 'email' in data and data['email'] != usuario.email:
            if User.query.filter_by(email=data['email']).first():
                raise Exception("El correo electrónico ya está en uso")
            usuario.email = data['email']
            
        if 'password' in data and data['password']:
            usuario.password_hash = AuthService.hash_password(data['password'])
            
        if 'activo' in data:
            usuario.activo = data['activo']
            
        if 'es_admin' in data:
            usuario.es_admin = data['es_admin']
            
        db.session.commit()
        return usuario

    @staticmethod
    def eliminar_usuario(user_id):
        """Eliminar usuario (soft delete)"""
        usuario = User.query.get(user_id)
        if not usuario:
            raise Exception("Usuario no encontrado")
            
        # En lugar de eliminar físicamente, marcamos como inactivo
        # O si se prefiere eliminar: db.session.delete(usuario)
        # Pero soft delete es mejor práctica para mantener integridad referencial si tuviera relaciones
        usuario.activo = False
        db.session.commit()
        return True
