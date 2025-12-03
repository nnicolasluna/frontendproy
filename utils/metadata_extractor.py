import os
import mimetypes
import hashlib
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import mutagen

class MetadataExtractor:
    @staticmethod
    def get_file_metadata(file_path):
        """
        Extrae todos los metadatos posibles de un archivo
        """
        metadata = {
            "size_bytes": os.path.getsize(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "hash_sha256": MetadataExtractor._calculate_hash(file_path)
        }
        
        mime_type, _ = mimetypes.guess_type(file_path)
        metadata["mime_type"] = mime_type
        
        if mime_type:
            if mime_type.startswith('image/'):
                metadata.update(MetadataExtractor._get_image_metadata(file_path))
            elif mime_type.startswith('audio/') or mime_type.startswith('video/'):
                metadata.update(MetadataExtractor._get_media_metadata(file_path))
                
        return metadata

    @staticmethod
    def _calculate_hash(file_path, block_size=65536):
        """Calcula el hash SHA-256 del archivo"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    sha256.update(block)
            return sha256.hexdigest()
        except Exception as e:
            return f"Error calculating hash: {str(e)}"

    @staticmethod
    def _get_image_metadata(file_path):
        image_meta = {}
        try:
            with Image.open(file_path) as img:
                image_meta["width"] = img.width
                image_meta["height"] = img.height
                image_meta["format"] = img.format
                image_meta["mode"] = img.mode
                
                # Extraer EXIF si existe
                exif_data = img._getexif()
                if exif_data:
                    exif = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Convertir bytes a string si es necesario
                        if isinstance(value, bytes):
                            try:
                                value = value.decode()
                            except:
                                value = str(value)
                        # Convertir valores no serializables
                        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            value = str(value)
                        exif[tag] = value
                    image_meta["exif"] = exif
                    
                    # Intentar obtener geolocalización
                    if "GPSInfo" in exif:
                        image_meta["gps"] = str(exif["GPSInfo"])
                        
        except Exception as e:
            image_meta["error_extraction"] = str(e)
            
        return image_meta

    @staticmethod
    def _get_media_metadata(file_path):
        media_meta = {}
        try:
            file = mutagen.File(file_path)
            if file:
                if file.info:
                    # Duración en segundos
                    if hasattr(file.info, 'length'):
                        media_meta["duration_seconds"] = file.info.length
                    
                    # Bitrate
                    if hasattr(file.info, 'bitrate'):
                        media_meta["bitrate"] = file.info.bitrate
                        
                    # Sample rate
                    if hasattr(file.info, 'sample_rate'):
                        media_meta["sample_rate"] = file.info.sample_rate
                        
                    # Canales
                    if hasattr(file.info, 'channels'):
                        media_meta["channels"] = file.info.channels
                
                # Tags (título, artista, etc)
                if file.tags:
                    tags = {}
                    for key, value in file.tags.items():
                        # Convertir valores a string para asegurar serialización JSON
                        tags[key] = str(value)
                    media_meta["tags"] = tags
                    
        except Exception as e:
            media_meta["error_extraction"] = str(e)
            
        return media_meta
