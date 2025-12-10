from models.models import Evaluacion, Archivo, Llamada
from database import db
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class EvaluacionService:
    @staticmethod
    def crear_evaluacion(datos_dispositivo, metadata_extra=None):
        """
        Crea una nueva evaluación
        """
        nueva_evaluacion = Evaluacion(
            dispositivo_marca=datos_dispositivo.get('marca'),
            dispositivo_modelo=datos_dispositivo.get('modelo'),
            dispositivo_serial=datos_dispositivo.get('serial'),
            dispositivo_version_android=datos_dispositivo.get('version_android'),
            metadata_evaluacion=metadata_extra or {}
        )
        
        db.session.add(nueva_evaluacion)
        db.session.commit()
        return nueva_evaluacion

    @staticmethod
    def obtener_evaluacion(id_evaluacion):
        return Evaluacion.query.get(id_evaluacion)

    @staticmethod
    def listar_evaluaciones():
        return Evaluacion.query.order_by(Evaluacion.fecha_creacion.desc()).all()
    
    @staticmethod
    def eliminar_evaluacion(id_evaluacion):
        evaluacion = Evaluacion.query.get(id_evaluacion)
        if evaluacion:
            db.session.delete(evaluacion)
            db.session.commit()
            return True
        return False

    @staticmethod
    def generar_pdf(id_evaluacion):
        evaluacion = EvaluacionService.obtener_evaluacion(id_evaluacion)
        if not evaluacion:
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        elements.append(Paragraph(f"Reporte de Evaluación #{evaluacion.id}", styles['Title']))
        elements.append(Paragraph(f"Fecha: {evaluacion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Información del Dispositivo
        elements.append(Paragraph("Información del Dispositivo", styles['Heading2']))
        data_dispositivo = [
            ["Marca", evaluacion.dispositivo_marca],
            ["Modelo", evaluacion.dispositivo_modelo],
            ["Serial", evaluacion.dispositivo_serial],
            ["Versión Android", evaluacion.dispositivo_version_android]
        ]
        t_dispositivo = Table(data_dispositivo, colWidths=[150, 300])
        t_dispositivo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_dispositivo)
        elements.append(Spacer(1, 20))

        # Archivos
        elements.append(Paragraph(f"Archivos Asociados ({len(evaluacion.archivos)})", styles['Heading2']))
        
        if evaluacion.archivos:
            data_archivos = [["Nombre", "Tipo", "Tamaño", "Metadata"]]
            for archivo in evaluacion.archivos:
                # Formatear metadata
                metadata_str = ""
                if archivo.metadata_archivo:
                    items = []
                    for k, v in archivo.metadata_archivo.items():
                        items.append(f"<b>{k}:</b> {v}")
                    metadata_str = "<br/>".join(items)
                
                data_archivos.append([
                    Paragraph(archivo.nombre_original, styles['Normal']), # Wrap long names
                    archivo.tipo_mime or "N/A",
                    f"{archivo.tamano_bytes / 1024:.2f} KB", # Convert to KB
                    Paragraph(metadata_str, styles['Normal']) # Wrap metadata
                ])
            
            t_archivos = Table(data_archivos, colWidths=[150, 80, 70, 230])
            t_archivos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(t_archivos)
        else:
            elements.append(Paragraph("No hay archivos asociados.", styles['Normal']))
        
        elements.append(Spacer(1, 20))

        # Llamadas
        elements.append(Paragraph(f"Registro de Llamadas ({len(evaluacion.llamadas)})", styles['Heading2']))
        
        if evaluacion.llamadas:
            data_llamadas = [["Número", "Contacto", "Fecha", "Duración", "Tipo"]]
            for llamada in evaluacion.llamadas:
                duracion_min = llamada.duracion_segundos // 60 if llamada.duracion_segundos else 0
                duracion_seg = llamada.duracion_segundos % 60 if llamada.duracion_segundos else 0
                
                data_llamadas.append([
                    llamada.numero or "Desconocido",
                    llamada.nombre_contacto or "Sin nombre",
                    llamada.fecha.strftime('%Y-%m-%d %H:%M') if llamada.fecha else "N/A",
                    f"{duracion_min}m {duracion_seg}s",
                    llamada.tipo or "N/A"
                ])
            
            t_llamadas = Table(data_llamadas, colWidths=[100, 120, 100, 70, 80])
            t_llamadas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(t_llamadas)
        else:
            elements.append(Paragraph("No hay llamadas registradas.", styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        return buffer
