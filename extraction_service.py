import adbutils
import os

class AndroidFileExtractor:
    """
    Servicio para extraer archivos multimedia de dispositivos Android usando ADB
    """
    
    # Rutas comunes en Android
    RUTAS_DEFECTO = [
        "/storage/emulated/0/DCIM/",
        "/storage/emulated/0/Pictures/",
        "/storage/emulated/0/Download/",
        "/storage/emulated/0/Documents/",
        "/storage/emulated/0/Music/",
        "/storage/emulated/0/Movies/",
        "/storage/emulated/0/WhatsApp/Media/",
        "/storage/emulated/0/Telegram/",
    ]
    
    # Extensiones por categoría
    EXTENSIONES = {
        "imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"],
        "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".3gp"],
        "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "otros": [".zip", ".rar", ".apk", ".json", ".xml"]
    }
    
    def __init__(self, carpeta_destino="archivos_descargados"):
        """
        Inicializar el extractor
        
        Args:
            carpeta_destino: Carpeta donde se guardarán los archivos descargados
        """
        self.carpeta_destino = carpeta_destino
        self.device = None
        self.archivos_encontrados = []
        
    def conectar_dispositivo(self):
        """Conectar al dispositivo Android"""
        try:
            self.device = adbutils.adb.device()
            return True
        except Exception as e:
            raise Exception(f"No se pudo conectar al dispositivo: {str(e)}")
    
    def obtener_info_dispositivo(self):
        """Obtener información del dispositivo conectado"""
        if not self.device:
            self.conectar_dispositivo()
        
        try:
            modelo = self.device.shell("getprop ro.product.model").strip()
            marca = self.device.shell("getprop ro.product.brand").strip()
            version = self.device.shell("getprop ro.build.version.release").strip()
            serial = self.device.serial
            
            return {
                "marca": marca,
                "modelo": modelo,
                "version_android": version,
                "serial": serial
            }
        except Exception as e:
            raise Exception(f"Error al obtener información del dispositivo: {str(e)}")
    
    def _obtener_extensiones_filtradas(self, categorias_filtro=None):
        """
        Obtener lista de extensiones según las categorías seleccionadas
        
        Args:
            categorias_filtro: Lista de categorías a incluir (None = todas)
        """
        if categorias_filtro:
            extensiones_filtradas = []
            for categoria in categorias_filtro:
                if categoria in self.EXTENSIONES:
                    extensiones_filtradas.extend(self.EXTENSIONES[categoria])
            return extensiones_filtradas
        else:
            # Todas las extensiones
            return [ext for lista in self.EXTENSIONES.values() for ext in lista]
    
    def _buscar_archivos_recursivo(self, ruta_base, extensiones_validas):
        """
        Buscar archivos recursivamente en un directorio
        
        Args:
            ruta_base: Ruta base para buscar
            extensiones_validas: Lista de extensiones a buscar
        """
        try:
            contenido = self.device.shell(f'ls -p "{ruta_base}"').splitlines()
            
            for linea in contenido:
                elementos = linea.split()
                for elemento in elementos:
                    ruta_completa = os.path.join(ruta_base, elemento).replace("\\", "/")
                    
                    # Si es un directorio, buscar recursivamente
                    if elemento.endswith("/"):
                        self._buscar_archivos_recursivo(ruta_completa, extensiones_validas)
                    # Si es un archivo con extensión válida
                    elif any(elemento.lower().endswith(ext) for ext in extensiones_validas):
                        self.archivos_encontrados.append(ruta_completa)
                        
        except Exception as e:
            print(f"⚠️ No se pudo acceder a {ruta_base}: {e}")
    
    def escanear_archivos(self, rutas_personalizadas=None, categorias_filtro=None):
        """
        Escanear archivos en el dispositivo sin descargarlos
        
        Args:
            rutas_personalizadas: Rutas personalizadas para buscar (None = usar rutas por defecto)
            categorias_filtro: Categorías a incluir en la búsqueda (None = todas)
        
        Returns:
            Diccionario con información de los archivos encontrados
        """
        if not self.device:
            self.conectar_dispositivo()
        
        # Resetear lista de archivos
        self.archivos_encontrados = []
        
        # Determinar rutas a escanear
        rutas = rutas_personalizadas if rutas_personalizadas else self.RUTAS_DEFECTO
        
        # Obtener extensiones válidas
        extensiones_validas = self._obtener_extensiones_filtradas(categorias_filtro)
        
        # Buscar archivos
        print("🔍 Escaneando archivos en el dispositivo...\n")
        for ruta in rutas:
            self._buscar_archivos_recursivo(ruta, extensiones_validas)
        
        # Crear resumen por categoría
        resumen_categorias = {}
        for categoria, exts in self.EXTENSIONES.items():
            cantidad = sum(1 for archivo in self.archivos_encontrados 
                          if any(archivo.lower().endswith(ext) for ext in exts))
            if cantidad > 0:
                resumen_categorias[categoria] = cantidad
        
        return {
            "total_archivos": len(self.archivos_encontrados),
            "resumen_categorias": resumen_categorias,
            "archivos": self.archivos_encontrados
        }
    
    def extraer_archivos(self, rutas_personalizadas=None, categorias_filtro=None):
        """
        Extraer archivos del dispositivo Android
        
        Args:
            rutas_personalizadas: Rutas personalizadas para buscar (None = usar rutas por defecto)
            categorias_filtro: Categorías a incluir (None = todas)
        
        Returns:
            Diccionario con el resultado de la extracción
        """
        # Primero escanear
        resultado_scan = self.escanear_archivos(rutas_personalizadas, categorias_filtro)
        
        if resultado_scan["total_archivos"] == 0:
            return {
                "archivos_escaneados": 0,
                "archivos_descargados": 0,
                "archivos_fallidos": 0,
                "resumen_categorias": {},
                "carpeta_destino": None
            }
        
        # Crear carpeta destino
        os.makedirs(self.carpeta_destino, exist_ok=True)
        
        # Descargar archivos
        archivos_descargados = 0
        archivos_fallidos = 0
        
        print(f"\n{'='*50}")
        print("Iniciando descarga...")
        print(f"{'='*50}\n")
        
        for i, ruta_archivo in enumerate(self.archivos_encontrados, 1):
            try:
                nombre_archivo = os.path.basename(ruta_archivo)
                destino = os.path.join(self.carpeta_destino, nombre_archivo)
                
                # Evitar sobrescribir archivos con el mismo nombre
                contador = 1
                nombre_base, extension = os.path.splitext(destino)
                while os.path.exists(destino):
                    destino = f"{nombre_base}_{contador}{extension}"
                    contador += 1
                
                self.device.sync.pull(ruta_archivo, destino)
                print(f"📥 [{i}/{len(self.archivos_encontrados)}] ✓ {nombre_archivo}")
                archivos_descargados += 1
                
            except Exception as e:
                print(f"❌ [{i}/{len(self.archivos_encontrados)}] Error: {os.path.basename(ruta_archivo)} - {e}")
                archivos_fallidos += 1
        
        print(f"\n{'='*50}")
        print(f"🎉 Descarga completada!")
        print(f"📁 Archivos guardados en: {os.path.abspath(self.carpeta_destino)}")
        print(f"{'='*50}")
        
        return {
            "archivos_escaneados": resultado_scan["total_archivos"],
            "archivos_descargados": archivos_descargados,
            "archivos_fallidos": archivos_fallidos,
            "resumen_categorias": resultado_scan["resumen_categorias"],
            "carpeta_destino": os.path.abspath(self.carpeta_destino)
        }
