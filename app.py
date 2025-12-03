from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from extraction_service import AndroidFileExtractor

app = Flask(__name__)
CORS(app)

# Configuración
DOWNLOAD_FOLDER = "archivos_descargados"

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Android File Extraction Service'
    }), 200

@app.route('/api/extract', methods=['POST'])
def extract_files():
    """
    Endpoint para extraer archivos del dispositivo Android.
    
    Body (JSON opcional):
    {
        "rutas": [...],  // Rutas personalizadas (opcional)
        "categorias": ["imagenes", "videos"],  // Categorías a extraer (opcional)
        "carpeta_destino": "mi_carpeta"  // Carpeta destino (opcional)
    }
    """
    try:
        # Obtener parámetros del request
        data = request.get_json() if request.is_json else {}
        
        rutas = data.get('rutas')
        categorias = data.get('categorias')
        carpeta_destino = data.get('carpeta_destino', DOWNLOAD_FOLDER)
        
        # Crear instancia del extractor
        extractor = AndroidFileExtractor(carpeta_destino=carpeta_destino)
        
        # Ejecutar extracción
        resultado = extractor.extraer_archivos(
            rutas_personalizadas=rutas,
            categorias_filtro=categorias
        )
        
        return jsonify({
            'success': True,
            'data': resultado
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/device-info', methods=['GET'])
def device_info():
    """Obtener información del dispositivo conectado"""
    try:
        extractor = AndroidFileExtractor()
        info = extractor.obtener_info_dispositivo()
        
        return jsonify({
            'success': True,
            'data': info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_files():
    """
    Escanear archivos sin descargarlos
    
    Body (JSON opcional):
    {
        "rutas": [...],  // Rutas personalizadas (opcional)
        "categorias": ["imagenes", "videos"]  // Categorías a buscar (opcional)
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        
        rutas = data.get('rutas')
        categorias = data.get('categorias')
        
        extractor = AndroidFileExtractor()
        resultado = extractor.escanear_archivos(
            rutas_personalizadas=rutas,
            categorias_filtro=categorias
        )
        
        return jsonify({
            'success': True,
            'data': resultado
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint no encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor'
    }), 500

if __name__ == '__main__':
    # Crear carpeta de descargas si no existe
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
