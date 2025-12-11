from app import app, db
from models.models import User
from services.auth_service import AuthService
from services.user_service import UserService

def create_initial_admin():
    with app.app_context():
        # Crear tablas nuevamente para asegurar que la tabla User existe
        db.create_all()
        
        # Verificar si existe el admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default admin user...")
            try:
                UserService.crear_usuario(
                    username='admin',
                    email='admin@system.local',
                    password='admin',
                    nombre_completo='Systems Administrator',
                    es_admin=True
                )
                print("Admin user created successfully.")
                print("Username: admin")
                print("Password: admin")
            except Exception as e:
                print(f"Error creating admin: {e}")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    create_initial_admin()
