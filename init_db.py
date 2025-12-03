from app import app
from database import init_db

if __name__ == "__main__":
    print("Inicializando base de datos...")
    try:
        init_db(app)
        print("Tablas creadas exitosamente!")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
