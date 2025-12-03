# Microservicio de Extracción de Archivos Android

Microservicio Flask para extraer archivos multimedia de dispositivos Android usando ADB.

## 🚀 Características

- ✅ Extracción de archivos multimedia (imágenes, videos, audio, documentos)
- ✅ API REST para integración con otros servicios
- ✅ Escaneo de archivos sin descargarlos
- ✅ Filtrado por categorías
- ✅ Información del dispositivo conectado
- ✅ Rutas personalizables

## 📋 Requisitos

- Python 3.8+
- ADB (Android Debug Bridge) instalado y configurado
- Dispositivo Android con depuración USB habilitada

## 🔧 Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Asegurarse de que ADB está en el PATH del sistema

3. Conectar dispositivo Android con depuración USB habilitada

## ▶️ Uso

### Ejecutar el servidor

```bash
python app.py
```

El servidor se ejecutará en `http://localhost:5000`

### Endpoints Disponibles

#### 1. Health Check
```http
GET /api/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "service": "Android File Extraction Service"
}
```

#### 2. Información del Dispositivo
```http
GET /api/device-info
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "marca": "Samsung",
    "modelo": "Galaxy S21",
    "version_android": "13",
    "serial": "ABC123XYZ"
  }
}
```

#### 3. Escanear Archivos
```http
POST /api/scan
Content-Type: application/json

{
  "categorias": ["imagenes", "videos"],
  "rutas": ["/storage/emulated/0/DCIM/"]
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "total_archivos": 150,
    "resumen_categorias": {
      "imagenes": 120,
      "videos": 30
    },
    "archivos": ["/storage/emulated/0/DCIM/foto1.jpg", "..."]
  }
}
```

#### 4. Extraer Archivos
```http
POST /api/extract
Content-Type: application/json

{
  "categorias": ["imagenes"],
  "carpeta_destino": "mis_fotos"
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "archivos_escaneados": 120,
    "archivos_descargados": 118,
    "archivos_fallidos": 2,
    "resumen_categorias": {
      "imagenes": 120
    },
    "carpeta_destino": "C:\\ruta\\completa\\mis_fotos"
  }
}
```

## 📁 Estructura del Proyecto

```
proyecto-grado/
├── app.py                    # Aplicación Flask principal
├── extraction_service.py     # Servicio de extracción
├── extrarcionDatos.py       # Script original
├── requirements.txt          # Dependencias
└── README.md                # Documentación
```

## 🎯 Categorías Disponibles

- `imagenes`: .jpg, .jpeg, .png, .gif, .bmp, .webp, .heic
- `videos`: .mp4, .avi, .mkv, .mov, .wmv, .flv, .3gp
- `audio`: .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma
- `documentos`: .pdf, .doc, .docx, .txt, .xls, .xlsx, .ppt, .pptx
- `otros`: .zip, .rar, .apk, .json, .xml

## 🔐 Consideraciones de Seguridad

- Este microservicio está diseñado para uso local/desarrollo
- Para producción, considera agregar autenticación y autorización
- Limita el acceso a redes de confianza

## 📝 Ejemplos de Uso

### Usando cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Información del dispositivo
curl http://localhost:5000/api/device-info

# Escanear solo imágenes
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"categorias": ["imagenes"]}'

# Extraer todos los archivos
curl -X POST http://localhost:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Usando Python

```python
import requests

# Extraer archivos
response = requests.post(
    'http://localhost:5000/api/extract',
    json={
        'categorias': ['imagenes', 'videos'],
        'carpeta_destino': 'mis_archivos'
    }
)

resultado = response.json()
print(f"Archivos descargados: {resultado['data']['archivos_descargados']}")
```

## 🛠️ Desarrollo

Para modificar el comportamiento:

1. **Agregar nuevas categorías**: Edita `EXTENSIONES` en `extraction_service.py`
2. **Agregar rutas**: Edita `RUTAS_DEFECTO` en `extraction_service.py`
3. **Nuevos endpoints**: Agrega rutas en `app.py`

## ℹ️ Notas

- Los archivos se descargan a la carpeta `archivos_descargados` por defecto
- Los archivos con nombres duplicados se renombran automáticamente
- El script original (`extrarcionDatos.py`) se mantiene como referencia
