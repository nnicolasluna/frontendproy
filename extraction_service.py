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
        Buscar archivos recursivamente en un directorio obteniendo detalles
        
        Args:
            ruta_base: Ruta base para buscar
            extensiones_validas: Lista de extensiones a buscar
        """
        try:
            # Intentar primero con ls -l para obtener detalles
            cmd = f'ls -l "{ruta_base}"'
            contenido = self.device.shell(cmd).splitlines()
            
            # Verificar si ls -l funcionó (si hay contenido y parece tener formato largo)
            usar_ls_simple = True
            if contenido:
                # Verificar si alguna línea parece tener formato largo (al menos 5 columnas)
                for linea in contenido:
                    if len(linea.split()) >= 5:
                        usar_ls_simple = False
                        break
            
            if usar_ls_simple:
                # Fallback a ls -p si ls -l no dio resultados útiles
                self._buscar_archivos_simple(ruta_base, extensiones_validas)
                return

            for linea in contenido:
                partes = linea.split()
                if len(partes) < 8: 
                    continue
                    
                # Parsing de ls -l (simplificado)
                permisos = partes[0]
                tamano = partes[4]
                fecha = partes[5]
                hora = partes[6]
                nombre = " ".join(partes[7:])
                
                ruta_completa = os.path.join(ruta_base, nombre).replace("\\", "/")
                
                if permisos.startswith('d'):
                    if nombre not in ['.', '..']:
                        self._buscar_archivos_recursivo(ruta_completa, extensiones_validas)
                
                elif permisos.startswith('-'):
                    if any(nombre.lower().endswith(ext) for ext in extensiones_validas):
                        try:
                            tamano_bytes = int(tamano)
                        except:
                            tamano_bytes = 0
                            
                        self.archivos_encontrados.append({
                            "ruta": ruta_completa,
                            "nombre": nombre,
                            "tamano": tamano_bytes,
                            "fecha": f"{fecha} {hora}",
                            "tipo": os.path.splitext(nombre)[1].lower()
                        })
                        
        except Exception as e:
            print(f"⚠️ Error en ls -l para {ruta_base}: {e}. Intentando fallback...")
            try:
                self._buscar_archivos_simple(ruta_base, extensiones_validas)
            except Exception as e2:
                print(f"⚠️ Falló también el fallback para {ruta_base}: {e2}")

    def _buscar_archivos_simple(self, ruta_base, extensiones_validas):
        """Método fallback usando ls -p (solo nombres)"""
        contenido = self.device.shell(f'ls -p "{ruta_base}"').splitlines()
        for linea in contenido:
            elementos = linea.split()
            for elemento in elementos:
                ruta_completa = os.path.join(ruta_base, elemento).replace("\\", "/")
                if elemento.endswith("/"):
                    self._buscar_archivos_recursivo(ruta_completa, extensiones_validas)
                elif any(elemento.lower().endswith(ext) for ext in extensiones_validas):
                    # Crear objeto con metadatos dummy
                    self.archivos_encontrados.append({
                        "ruta": ruta_completa,
                        "nombre": elemento,
                        "tamano": 0,
                        "fecha": "",
                        "tipo": os.path.splitext(elemento)[1].lower()
                    })
    
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
            cantidad = 0
            for archivo in self.archivos_encontrados:
                # Manejar tanto formato antiguo (string) como nuevo (dict)
                if isinstance(archivo, dict):
                    nombre = archivo['nombre']
                else:
                    nombre = os.path.basename(archivo)
                    
                if any(nombre.lower().endswith(ext) for ext in exts):
                    cantidad += 1
            
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
        
        for i, item in enumerate(self.archivos_encontrados, 1):
            try:
                # Manejar tanto formato antiguo (string) como nuevo (dict)
                if isinstance(item, dict):
                    ruta_archivo = item['ruta']
                else:
                    ruta_archivo = item
                    
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

    def _run_adb_command(self, cmd):
        """Ejecuta comando adb y devuelve stdout en UTF-8; lanza excepción si falla."""
        import subprocess
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            )
            return proc.stdout
        except FileNotFoundError:
            raise RuntimeError("No se encontró 'adb' en PATH. Instala adb o añade al PATH.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error ejecutando adb: {e.stderr.strip() or e.stdout.strip()}")

    def _safe_int(self, value):
        """Convierte un valor a int eliminando comas y espacios."""
        try:
            if value is None:
                return 0
            return int(str(value).replace(',', '').strip())
        except (ValueError, TypeError):
            return 0

    def _parse_content_query_output(self, output):
        """
        Parsea la salida de `adb shell content query` en forma robusta.
        Estrategia: dividimos en tokens; cada token que contiene '=' inicia un par clave=valor.
        Si un token no contiene '=', se concatena al valor anterior (gestiona espacios en valores).
        """
        llamadas = []
        for line in output.splitlines():
            line = line.strip()
            if not line or not line.startswith("Row:"):
                continue
            tokens = line.split()
            # saltamos "Row:" y el número de fila si existe
            tokens = tokens[2:] if len(tokens) >= 2 else tokens[1:]
            fila = {}
            current_key = None
            for tok in tokens:
                if '=' in tok:
                    key, val = tok.split('=', 1)
                    fila[key] = val
                    current_key = key
                else:
                    # token sin '=': es parte del valor anterior (espacios dentro de valor)
                    if current_key is not None:
                        fila[current_key] = fila[current_key] + " " + tok
                    else:
                        continue
            llamadas.append(fila)
        return llamadas

    def _convert_dates(self, llamadas):
        """Convierte 'date' en ms a datetime en TZ local (Bolivia UTC-4)."""
        from datetime import datetime, timezone, timedelta
        TZ = timezone(timedelta(hours=-4))
        
        for f in llamadas:
            if 'date' in f:
                try:
                    ts_ms = self._safe_int(f['date'])
                    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).astimezone(TZ)
                    f['date_datetime'] = dt.replace(tzinfo=None)  # datetime sin tz para BD
                    f['date_readable'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    f['date_datetime'] = None
                    f['date_readable'] = f.get('date')
        return llamadas

    def extraer_llamadas(self):
        """
        Extrae el registro de llamadas del dispositivo Android usando subprocess.
        
        Returns:
            Lista de diccionarios con información formateada de cada llamada
        """
        # Mapeo de tipos de llamada
        tipos_llamada = {
            '1': 'entrante',
            '2': 'saliente',
            '3': 'perdida',
            '4': 'buzon_voz',
            '5': 'rechazada',
            '6': 'bloqueada'
        }
        
        try:
            cmd = ["adb", "shell", "content", "query", "--uri", "content://call_log/calls"]
            out = self._run_adb_command(cmd)
            llamadas_raw = self._parse_content_query_output(out)
            llamadas_raw = self._convert_dates(llamadas_raw)
            
            # Formatear para el servicio
            llamadas_formateadas = []
            for l in llamadas_raw:
                llamada = {
                    'numero': l.get('number'),
                    'nombre_contacto': l.get('name') or l.get('cached_name') or l.get('display_name'),
                    'fecha': l.get('date_datetime'),
                    'duracion_segundos': self._safe_int(l.get('duration', 0)),
                    'tipo': tipos_llamada.get(str(l.get('type', '')).replace(',', '').strip(), 'desconocido'),
                    'metadata': {
                        'date_readable': l.get('date_readable'),
                        'raw_type': l.get('type'),
                        'geocoded_location': l.get('geocoded_location'),
                        'presentation': l.get('presentation')
                    }
                }
                if llamada['numero'] or llamada['nombre_contacto']:
                    llamadas_formateadas.append(llamada)
            
            print(f"📞 Se encontraron {len(llamadas_formateadas)} llamadas")
            return llamadas_formateadas
            
        except Exception as e:
            print(f"❌ Error al extraer llamadas: {e}")
            return []
