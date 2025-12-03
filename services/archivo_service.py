import os
import shutil
from models import Archivo
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
