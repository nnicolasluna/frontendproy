from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nombre_completo = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    es_admin = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'activo': self.activo,
            'es_admin': self.es_admin,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }

class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    # Datos del dispositivo
    dispositivo_marca = db.Column(db.String(100))
    dispositivo_modelo = db.Column(db.String(100))
    dispositivo_serial = db.Column(db.String(100))
    dispositivo_version_android = db.Column(db.String(50))
    
    # Metadatos adicionales de la evaluación
    metadata_evaluacion = db.Column(JSONB, default={})
    
    # Relación con archivos
    archivos = db.relationship('Archivo', backref='evaluacion', lazy=True, cascade="all, delete-orphan")
    
    # Relación con llamadas
    llamadas = db.relationship('Llamada', backref='evaluacion', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'dispositivo': {
                'marca': self.dispositivo_marca,
                'modelo': self.dispositivo_modelo,
                'serial': self.dispositivo_serial,
                'version_android': self.dispositivo_version_android
            },
            'metadata': self.metadata_evaluacion,
            'cantidad_archivos': len(self.archivos),
            'cantidad_llamadas': len(self.llamadas)
        }

class Archivo(db.Model):
    __tablename__ = 'archivos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_original = db.Column(db.String(255), nullable=False)
    ruta_almacenamiento = db.Column(db.String(500), nullable=False)
    tipo_mime = db.Column(db.String(100))
    tamano_bytes = db.Column(db.BigInteger)
    
    # Metadatos extraídos (EXIF, duración, resolución, etc.)
    metadata_archivo = db.Column(JSONB, default={})
    
    fecha_subida = db.Column(db.DateTime, default=datetime.now)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre_original,
            'tipo': self.tipo_mime,
            'tamano': self.tamano_bytes,
            'metadata': self.metadata_archivo,
            'fecha_subida': self.fecha_subida.isoformat(),
            'ruta': self.ruta_almacenamiento
        }

class Llamada(db.Model):
    __tablename__ = 'llamadas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50))
    nombre_contacto = db.Column(db.String(255))
    fecha = db.Column(db.DateTime)
    duracion_segundos = db.Column(db.Integer, default=0)
    tipo = db.Column(db.String(20))  # 'entrante', 'saliente', 'perdida', 'rechazada', 'bloqueada'
    
    # Metadatos adicionales
    metadata_llamada = db.Column(JSONB, default={})
    
    fecha_extraccion = db.Column(db.DateTime, default=datetime.now)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'nombre_contacto': self.nombre_contacto,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'duracion_segundos': self.duracion_segundos,
            'tipo': self.tipo,
            'metadata': self.metadata_llamada,
            'fecha_extraccion': self.fecha_extraccion.isoformat()
        }
