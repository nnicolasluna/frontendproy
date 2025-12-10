from models.models import Llamada
from database import db
from datetime import datetime


class LlamadaService:
    @staticmethod
    def guardar_llamadas(lista_llamadas, evaluacion_id):
        """
        Guarda una lista de llamadas en la base de datos
        
        Args:
            lista_llamadas: Lista de diccionarios con datos de llamadas
            evaluacion_id: ID de la evaluación asociada
        
        Returns:
            Lista de llamadas guardadas
        """
        llamadas_guardadas = []
        
        for datos_llamada in lista_llamadas:
            nueva_llamada = Llamada(
                numero=datos_llamada.get('numero'),
                nombre_contacto=datos_llamada.get('nombre_contacto'),
                fecha=datos_llamada.get('fecha'),
                duracion_segundos=datos_llamada.get('duracion_segundos', 0),
                tipo=datos_llamada.get('tipo', 'desconocido'),
                metadata_llamada=datos_llamada.get('metadata') or {},
                evaluacion_id=evaluacion_id
            )
            
            db.session.add(nueva_llamada)
            llamadas_guardadas.append(nueva_llamada)
        
        db.session.commit()
        return llamadas_guardadas
    
    @staticmethod
    def obtener_llamadas_por_evaluacion(evaluacion_id):
        """
        Obtiene todas las llamadas de una evaluación
        """
        return Llamada.query.filter_by(evaluacion_id=evaluacion_id).order_by(Llamada.fecha.desc()).all()
    
    @staticmethod
    def contar_llamadas(evaluacion_id):
        """
        Cuenta las llamadas de una evaluación
        """
        return Llamada.query.filter_by(evaluacion_id=evaluacion_id).count()
    
    @staticmethod
    def obtener_resumen_llamadas(evaluacion_id):
        """
        Obtiene un resumen de las llamadas por tipo
        """
        llamadas = Llamada.query.filter_by(evaluacion_id=evaluacion_id).all()
        
        resumen = {
            'total': len(llamadas),
            'entrantes': 0,
            'salientes': 0,
            'perdidas': 0,
            'duracion_total_segundos': 0
        }
        
        for llamada in llamadas:
            if llamada.tipo == 'entrante':
                resumen['entrantes'] += 1
            elif llamada.tipo == 'saliente':
                resumen['salientes'] += 1
            elif llamada.tipo == 'perdida':
                resumen['perdidas'] += 1
            
            resumen['duracion_total_segundos'] += llamada.duracion_segundos or 0
        
        return resumen
