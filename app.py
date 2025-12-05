from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from extraction_service import AndroidFileExtractor
from config import Config
from database import init_db
from services.evaluacion_service import EvaluacionService
from services.archivo_service import ArchivoService
from services.llamada_service import LlamadaService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inicializar base de datos
with app.app_context():
    from database import db
    db.init_app(app)
    # Crear tablas si no existen (para desarrollo)
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Android File Extraction Service with PostgreSQL'
    }), 200

@app.route('/api/extract', methods=['POST'])
def extract_files():
    """
    Endpoint para extraer archivos y generar una evaluación.
    """
    try:
        data = request.get_json() if request.is_json else {}
        
        rutas = data.get('rutas')
        categorias = data.get('categorias')
        carpeta_destino = data.get('carpeta_destino', Config.UPLOAD_FOLDER)
        metadata_extra = data.get('metadata', {})
        
        # 1. Obtener info del dispositivo
        extractor = AndroidFileExtractor(carpeta_destino=carpeta_destino)
        try:
            info_dispositivo = extractor.obtener_info_dispositivo()
        except Exception as e:
            return jsonify({'success': False, 'error': f"Error al conectar dispositivo: {str(e)}"}), 500
            
        # 2. Crear Evaluación en BD
        evaluacion = EvaluacionService.crear_evaluacion(info_dispositivo, metadata_extra)
        
        # 3. Ejecutar extracción física
        resultado_extraccion = extractor.extraer_archivos(
            rutas_personalizadas=rutas,
            categorias_filtro=categorias
        )
        
        # 4. Procesar archivos descargados para extraer metadatos y guardar en BD
        archivos_procesados = []
        if resultado_extraccion['archivos_descargados'] > 0:
            # La carpeta destino tiene los archivos descargados
            carpeta_final = resultado_extraccion['carpeta_destino']
            for nombre_archivo in os.listdir(carpeta_final):
                ruta_completa = os.path.join(carpeta_final, nombre_archivo)
                if os.path.isfile(ruta_completa):
                    # Verificar si este archivo fue parte de la extracción reciente
                    # (Esto es una simplificación, idealmente el extractor retornaría las rutas exactas de los descargados)
                    try:
                        archivo_db = ArchivoService.procesar_archivo_descargado(ruta_completa, evaluacion.id)
                        archivos_procesados.append(archivo_db.to_dict())
                    except Exception as e:
                        print(f"Error procesando metadatos de {nombre_archivo}: {e}")
        
        # 5. Extraer y guardar llamadas del dispositivo
        llamadas_guardadas = []
        try:
            llamadas_extraidas = extractor.extraer_llamadas()
            if llamadas_extraidas:
                llamadas_db = LlamadaService.guardar_llamadas(llamadas_extraidas, evaluacion.id)
                llamadas_guardadas = [l.to_dict() for l in llamadas_db]
        except Exception as e:
            print(f"Error extrayendo llamadas: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'evaluacion': evaluacion.to_dict(),
                'extraccion': resultado_extraccion,
                'archivos_procesados': len(archivos_procesados),
                'llamadas_extraidas': len(llamadas_guardadas)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/evaluaciones', methods=['GET'])
def listar_evaluaciones():
    """Listar todas las evaluaciones"""
    try:
        evaluaciones = EvaluacionService.listar_evaluaciones()
        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in evaluaciones]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evaluaciones/<int:id>', methods=['GET'])
def obtener_evaluacion(id):
    """Obtener detalle de una evaluación con sus archivos"""
    try:
        evaluacion = EvaluacionService.obtener_evaluacion(id)
        if not evaluacion:
            return jsonify({'success': False, 'error': 'Evaluación no encontrada'}), 404
            
        return jsonify({
            'success': True,
            'data': {
                **evaluacion.to_dict(),
                'archivos': [a.to_dict() for a in evaluacion.archivos],
                'llamadas': [l.to_dict() for l in evaluacion.llamadas]
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evaluaciones/<int:id>/pdf', methods=['GET'])
def descargar_pdf_evaluacion(id):
    """Generar y descargar PDF de una evaluación"""
    try:
        pdf_buffer = EvaluacionService.generar_pdf(id)
        if not pdf_buffer:
            return jsonify({'success': False, 'error': 'Evaluación no encontrada'}), 404
            
        from flask import send_file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'reporte_evaluacion_{id}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['GET'])
def serve_file(file_id):
    """Servir un archivo por su ID para previsualización"""
    try:
        from flask import send_file
        from models import Archivo
        
        archivo = Archivo.query.get(file_id)
        if not archivo:
            return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
        
        # La ruta almacenada es relativa a la carpeta de descargas
        ruta_completa = archivo.ruta_almacenamiento
        
        # Si la ruta no es absoluta, construirla
        if not os.path.isabs(ruta_completa):
            ruta_completa = os.path.join(Config.UPLOAD_FOLDER, ruta_completa)
        
        if not os.path.exists(ruta_completa):
            return jsonify({'success': False, 'error': 'Archivo no existe en el sistema'}), 404
        
        # Determinar mimetype
        mimetype = archivo.tipo_mime or 'application/octet-stream'
        
        return send_file(
            ruta_completa,
            mimetype=mimetype,
            as_attachment=False,
            download_name=archivo.nombre_original
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/extract-calls', methods=['POST'])
def extract_calls_only():
    """
    Endpoint para extraer solo llamadas sin descargar archivos.
    """
    try:
        data = request.get_json() if request.is_json else {}
        metadata_extra = data.get('metadata', {})
        
        # 1. Obtener info del dispositivo
        extractor = AndroidFileExtractor()
        try:
            info_dispositivo = extractor.obtener_info_dispositivo()
        except Exception as e:
            return jsonify({'success': False, 'error': f"Error al conectar dispositivo: {str(e)}"}), 500
            
        # 2. Crear Evaluación en BD
        evaluacion = EvaluacionService.crear_evaluacion(info_dispositivo, metadata_extra)
        
        # 3. Extraer y guardar llamadas del dispositivo
        llamadas_guardadas = []
        try:
            llamadas_extraidas = extractor.extraer_llamadas()
            if llamadas_extraidas:
                llamadas_db = LlamadaService.guardar_llamadas(llamadas_extraidas, evaluacion.id)
                llamadas_guardadas = [l.to_dict() for l in llamadas_db]
        except Exception as e:
            print(f"Error extrayendo llamadas: {e}")
            return jsonify({'success': False, 'error': f"Error extrayendo llamadas: {str(e)}"}), 500
        
        return jsonify({
            'success': True,
            'data': {
                'evaluacion': evaluacion.to_dict(),
                'llamadas_extraidas': len(llamadas_guardadas),
                'llamadas': llamadas_guardadas
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/extract-whatsapp-backups', methods=['POST'])
def extract_whatsapp_backups():
    """
    Endpoint para extraer backups de WhatsApp del dispositivo.
    """
    try:
        data = request.get_json() if request.is_json else {}
        metadata_extra = data.get('metadata', {})
        carpeta_destino = data.get('carpeta_destino', Config.UPLOAD_FOLDER)
        
        # 1. Obtener info del dispositivo
        extractor = AndroidFileExtractor(carpeta_destino=carpeta_destino)
        try:
            info_dispositivo = extractor.obtener_info_dispositivo()
        except Exception as e:
            return jsonify({'success': False, 'error': f"Error al conectar dispositivo: {str(e)}"}), 500
            
        # 2. Crear Evaluación en BD
        evaluacion = EvaluacionService.crear_evaluacion(info_dispositivo, metadata_extra)
        
        # 3. Extraer backups de WhatsApp
        resultado_backups = extractor.extraer_backups_whatsapp()
        
        # 4. Procesar backups descargados para guardarlos en BD con metadata de WhatsApp
        archivos_procesados = []
        if resultado_backups['backups_descargados'] > 0 and resultado_backups['carpeta_destino']:
            for backup in resultado_backups['backups_encontrados']:
                if 'ruta_local' in backup:
                    try:
                        # Usar el nuevo método que guarda la metadata específica de WhatsApp
                        archivo_db = ArchivoService.procesar_backup_whatsapp(
                            ruta_archivo=backup['ruta_local'],
                            id_evaluacion=evaluacion.id,
                            backup_info=backup
                        )
                        archivos_procesados.append(archivo_db.to_dict())
                        print(f"✅ Backup guardado en BD: {backup['nombre']}")
                    except Exception as e:
                        print(f"❌ Error procesando backup {backup['nombre']}: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'evaluacion': evaluacion.to_dict(),
                'backups': resultado_backups,
                'archivos_procesados': len(archivos_procesados)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_files():
    """Escanear archivos sin descargarlos"""
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

if __name__ == '__main__':
    # Crear carpeta de descargas si no existe
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
