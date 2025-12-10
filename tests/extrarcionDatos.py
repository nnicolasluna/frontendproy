import adbutils
import os

# Conectar al primer dispositivo
device = adbutils.adb.device()

# 📂 Rutas comunes en Android (puedes agregar más)
rutas = [
    "/storage/emulated/0/DCIM/",           # Fotos y videos de cámara
    "/storage/emulated/0/Pictures/",       # Imágenes generales
    "/storage/emulated/0/Download/",       # Descargas
    "/storage/emulated/0/Documents/",      # Documentos
    "/storage/emulated/0/Music/",          # Música
    "/storage/emulated/0/Movies/",         # Videos
    "/storage/emulated/0/WhatsApp/Media/", # Multimedia de WhatsApp
    "/storage/emulated/0/Telegram/",       # Telegram
]

# 📋 Extensiones de archivos a buscar (por categoría)
extensiones = {
    "imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"],
    "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".3gp"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "otros": [".zip", ".rar", ".apk", ".json", ".xml"]
}

# Aplanar todas las extensiones en una sola lista
todas_extensiones = [ext for lista in extensiones.values() for ext in lista]

archivos_encontrados = []

# Carpeta local donde se guardarán los archivos
carpeta_destino = "archivos_descargados"
os.makedirs(carpeta_destino, exist_ok=True)

# 🔍 Función recursiva para buscar archivos en subdirectorios
def buscar_archivos_recursivo(ruta_base):
    try:
        # Listar contenido del directorio
        contenido = device.shell(f'ls -p "{ruta_base}"').splitlines()
        
        for linea in contenido:
            elementos = linea.split()
            for elemento in elementos:
                ruta_completa = os.path.join(ruta_base, elemento).replace("\\", "/")
                
                # Si es un directorio, buscar recursivamente
                if elemento.endswith("/"):
                    buscar_archivos_recursivo(ruta_completa)
                # Si es un archivo con extensión válida, agregarlo
                elif any(elemento.lower().endswith(ext) for ext in todas_extensiones):
                    archivos_encontrados.append(ruta_completa)
    except Exception as e:
        print(f"⚠️ No se pudo acceder a {ruta_base}: {e}")

# Recorrer todas las rutas
print("🔍 Buscando archivos en el dispositivo...\n")
for ruta in rutas:
    buscar_archivos_recursivo(ruta)

print(f"\n📦 Total de archivos encontrados: {len(archivos_encontrados)}\n")

# Mostrar resumen por tipo
for categoria, exts in extensiones.items():
    cantidad = sum(1 for archivo in archivos_encontrados if any(archivo.lower().endswith(ext) for ext in exts))
    if cantidad > 0:
        print(f"  • {categoria.capitalize()}: {cantidad}")

# 📥 Descargar todos los archivos
print(f"\n{'='*50}")
print("Iniciando descarga...")
print(f"{'='*50}\n")

for i, ruta_archivo in enumerate(archivos_encontrados, 1):
    try:
        # Mantener estructura de carpetas (opcional)
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # Si quieres mantener la estructura original, descomenta esto:
        # ruta_relativa = ruta_archivo.replace("/storage/emulated/0/", "")
        # destino = os.path.join(carpeta_destino, ruta_relativa)
        # os.makedirs(os.path.dirname(destino), exist_ok=True)
        
        # Guardar todos en una sola carpeta:
        destino = os.path.join(carpeta_destino, nombre_archivo)
        
        # Evitar sobrescribir archivos con el mismo nombre
        contador = 1
        nombre_base, extension = os.path.splitext(destino)
        while os.path.exists(destino):
            destino = f"{nombre_base}_{contador}{extension}"
            contador += 1
        
        device.sync.pull(ruta_archivo, destino)
        print(f"📥 [{i}/{len(archivos_encontrados)}] ✓ {nombre_archivo}")
        
    except Exception as e:
        print(f"❌ [{i}/{len(archivos_encontrados)}] Error: {os.path.basename(ruta_archivo)} - {e}")

print(f"\n{'='*50}")
print(f"🎉 Descarga completada!")
print(f"📁 Archivos guardados en: {os.path.abspath(carpeta_destino)}")
print(f"{'='*50}")