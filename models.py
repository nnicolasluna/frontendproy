from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from database import db

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
            'cantidad_archivos': len(self.archivos)
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
