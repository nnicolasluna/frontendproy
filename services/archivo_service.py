import os
import shutil
from models.models import Archivo
from database import db
from utils.metadata_extractor import MetadataExtractor
from config import Config

class ArchivoService:
    @staticmethod
    def procesar_archivo_descargado(ruta_archivo, id_evaluacion):
        """
        Procesa un archivo ya descargado, extrae metadatos y lo guarda en BD
        """
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"El archivo {ruta_archivo} no existe")
            
        # Extraer metadatos
        metadata = MetadataExtractor.get_file_metadata(ruta_archivo)
        
        # Crear registro en BD
        nuevo_archivo = Archivo(
            nombre_original=os.path.basename(ruta_archivo),
            ruta_almacenamiento=ruta_archivo,
            tipo_mime=metadata.get('mime_type'),
            tamano_bytes=metadata.get('size_bytes'),
            metadata_archivo=metadata,
            evaluacion_id=id_evaluacion
        )
        
        db.session.add(nuevo_archivo)
        db.session.commit()
        
        return nuevo_archivo

    @staticmethod
    def procesar_backup_whatsapp(ruta_archivo, id_evaluacion, backup_info):
        """
        Procesa un backup de WhatsApp con metadata específica
        
        Args:
            ruta_archivo: Ruta local del archivo descargado
            id_evaluacion: ID de la evaluación
            backup_info: Diccionario con información del backup (tipo_backup, app_origen, etc.)
        """
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"El archivo {ruta_archivo} no existe")
            
        # Extraer metadatos básicos
        metadata = MetadataExtractor.get_file_metadata(ruta_archivo)
        
        # Añadir metadata específica de WhatsApp
        metadata['whatsapp'] = {
            'tipo_backup': backup_info.get('tipo_backup', 'desconocido'),
            'app_origen': backup_info.get('app_origen', 'WhatsApp'),
            'fecha_backup': backup_info.get('fecha', ''),
            'ruta_original': backup_info.get('ruta', ''),
            'nombre_original': backup_info.get('nombre', os.path.basename(ruta_archivo))
        }
        
        # Crear registro en BD
        nuevo_archivo = Archivo(
            nombre_original=backup_info.get('nombre', os.path.basename(ruta_archivo)),
            ruta_almacenamiento=ruta_archivo,
            tipo_mime=metadata.get('mime_type', 'application/octet-stream'),
            tamano_bytes=metadata.get('size_bytes', backup_info.get('tamano', 0)),
            metadata_archivo=metadata,
            evaluacion_id=id_evaluacion
        )
        
        db.session.add(nuevo_archivo)
        db.session.commit()
        
        return nuevo_archivo

    @staticmethod
    def eliminar_archivo(id_archivo):
        archivo = Archivo.query.get(id_archivo)
        if archivo:
            # Eliminar archivo físico (opcional, depende de requerimientos)
            # if os.path.exists(archivo.ruta_almacenamiento):
            #     os.remove(archivo.ruta_almacenamiento)
            
            db.session.delete(archivo)
            db.session.commit()
            return True
        return False
