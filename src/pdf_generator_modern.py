# pdf_generator_modern.py — Generador de PDF moderno con tablas estilo Excel
# ORM Analyzer IA PRO — Generador PDF Moderno

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Colores modernos
PRIMARY_COLOR = HexColor('#004E89')
SECONDARY_COLOR = HexColor('#1E88E5')
SUCCESS_COLOR = HexColor('#43A047')
WARNING_COLOR = HexColor('#FB8C00')
DANGER_COLOR = HexColor('#E53935')
TEXT_COLOR = HexColor('#2C2C2C')
LIGHT_GRAY = HexColor('#F5F5F5')
WHITE = HexColor('#FFFFFF')

# ========================== Estilos modernos ==========================
def _create_modern_styles():
    """Crear estilos modernos para el PDF"""
    styles = getSampleStyleSheet()
    
    # Título principal
    styles.add(ParagraphStyle(
        name='ModernTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtítulo
    styles.add(ParagraphStyle(
        name='ModernSubtitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=TEXT_COLOR,
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    # Encabezado de sección
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    ))
    
    # Texto normal moderno
    styles.add(ParagraphStyle(
        name='ModernNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=TEXT_COLOR,
        spaceAfter=8,
        fontName='Helvetica',
        alignment=TA_JUSTIFY
    ))
    
    # Texto de KPI
    styles.add(ParagraphStyle(
        name='KPITitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='KPIValue',
        parent=styles['Normal'],
        fontSize=20,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='KPINote',
        parent=styles['Normal'],
        fontSize=9,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    return styles

# ========================== Tablas modernas ==========================
def _create_kpi_table(data, styles):
    """Crear tabla de KPIs moderna"""
    try:
        # Preparar datos para la tabla
        table_data = []
        
        for title, value, note, color in data:
            # Crear celdas con contenido formateado
            title_cell = Paragraph(title.upper(), styles['KPITitle'])
            value_cell = Paragraph(str(value), styles['KPIValue'])
            note_cell = Paragraph(note, styles['KPINote'])
            
            table_data.append([title_cell, value_cell, note_cell])
        
        # Crear tabla
        table = Table(table_data, colWidths=[4*inch, 2*inch, 2*inch])
        
        # Aplicar estilo moderno
        table_style = TableStyle([
            # Bordes
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Colores de fondo alternados
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('BACKGROUND', (1, 0), (1, -1), WHITE),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_GRAY),
            
            # Alineación
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Espaciado
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        
        table.setStyle(table_style)
        return table
        
    except Exception as e:
        logger.error(f"Error creando tabla KPI: {e}")
        return None

def _create_data_summary_table(df, styles):
    """Crear tabla resumen de datos moderna"""
    try:
        # Calcular estadísticas
        total_reviews = len(df)
        avg_rating = df['rating_num'].mean() if total_reviews > 0 else 0
        
        # Distribución por estrellas
        star_dist = df['rating_num'].value_counts().sort_index()
        
        # Crear datos de la tabla
        table_data = [
            ['Métrica', 'Valor', 'Porcentaje'],
            ['Total de reseñas', f"{total_reviews:,}", "100%"],
            ['Valoración promedio', f"{avg_rating:.2f} ⭐", f"{(avg_rating/5*100):.1f}%"]
        ]
        
        # Añadir distribución por estrellas
        for star in range(5, 0, -1):
            count = star_dist.get(star, 0)
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            table_data.append([
                f'Reseñas {star} estrellas',
                f"{count:,}",
                f"{percentage:.1f}%"
            ])
        
        # Crear tabla
        table = Table(table_data, colWidths=[3*inch, 2*inch, 2*inch])
        
        # Aplicar estilo moderno
        table_style = TableStyle([
            # Bordes
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),
            
            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            
            # Alineación
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Primera columna a la izquierda
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Resto centrado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Espaciado
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        table.setStyle(table_style)
        return table
        
    except Exception as e:
        logger.error(f"Error creando tabla resumen: {e}")
        return None

def _create_languages_table_pdf(languages, styles):
    """Crear tabla de distribución de idiomas para PDF"""
    try:
        if not languages:
            return None

        # Crear datos de la tabla
        table_data = [['Idioma', 'Cantidad', 'Porcentaje', 'Análisis Estratégico']]

        for lang in languages:
            # Análisis estratégico
            if lang['percentage'] > 50:
                analisis = "🌍 Mercado principal - Comunicación prioritaria"
            elif lang['percentage'] > 20:
                analisis = "🎯 Mercado secundario - Atención especializada"
            elif lang['percentage'] > 10:
                analisis = "📈 Mercado emergente - Oportunidad de crecimiento"
            else:
                analisis = "🔍 Mercado nicho - Monitoreo selectivo"

            table_data.append([
                lang['name'],
                f"{lang['count']:,}",
                f"{lang['percentage']:.1f}%",
                analisis
            ])

        # Crear tabla
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 3*inch])

        # Aplicar estilo moderno
        table_style = TableStyle([
            # Bordes
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),

            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),

            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),

            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),

            # Alineación
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Primera columna a la izquierda
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Resto centrado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Espaciado
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])

        table.setStyle(table_style)
        return table

    except Exception as e:
        logger.error(f"Error creando tabla idiomas PDF: {e}")
        return None


def _create_sentiment_table(df, styles):
    """Crear tabla de análisis de sentimiento moderna"""
    try:
        sentiment_dist = df['sentiment'].value_counts()
        total = len(df)

        # Datos ordenados
        sentiments = [
            ("Muy Positivo", "muy_positivo", SUCCESS_COLOR),
            ("Positivo", "positivo", SUCCESS_COLOR),
            ("Neutro", "neutro", WARNING_COLOR),
            ("Negativo", "negativo", DANGER_COLOR),
            ("Muy Negativo", "muy_negativo", DANGER_COLOR)
        ]

        # Crear datos de la tabla
        table_data = [['Sentimiento', 'Cantidad', 'Porcentaje', 'Barra Visual']]

        for label, key, color in sentiments:
            count = sentiment_dist.get(key, 0)
            percentage = (count / total * 100) if total > 0 else 0

            # Crear barra visual
            bar_length = int(percentage / 2)  # Escala visual
            bar = "█" * bar_length + "░" * (20 - bar_length)

            table_data.append([
                label,
                f"{count:,}",
                f"{percentage:.1f}%",
                bar
            ])

        # Crear tabla
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2*inch])

        # Aplicar estilo moderno
        table_style = TableStyle([
            # Bordes
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),

            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),

            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),

            # Colores de sentimiento
            ('TEXTCOLOR', (0, 1), (0, 1), SUCCESS_COLOR),  # Muy Positivo
            ('TEXTCOLOR', (0, 2), (0, 2), SUCCESS_COLOR),  # Positivo
            ('TEXTCOLOR', (0, 3), (0, 3), WARNING_COLOR),  # Neutro
            ('TEXTCOLOR', (0, 4), (0, 4), DANGER_COLOR),   # Negativo
            ('TEXTCOLOR', (0, 5), (0, 5), DANGER_COLOR),   # Muy Negativo

            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),

            # Alineación
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Primera columna a la izquierda
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Resto centrado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Espaciado
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])

        table.setStyle(table_style)
        return table

    except Exception as e:
        logger.error(f"Error creando tabla sentimiento: {e}")
        return None

# ========================== Gráficos modernos ==========================
def _create_modern_rating_chart(df, path):
    """Crear gráfico de valoraciones moderno para PDF"""
    try:
        counts = df['rating_num'].value_counts().sort_index()
        
        # Configurar estilo moderno
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Colores modernos
        colors = ['#E53935', '#FF7043', '#FFB74D', '#66BB6A', '#43A047']
        bars = ax.bar(counts.index.astype(str), counts.values, color=colors, 
                     edgecolor='white', linewidth=2, alpha=0.9)
        
        # Personalizar gráfico
        ax.set_xlabel('Valoración (Estrellas)', fontsize=12, fontweight='bold', color='#2C2C2C')
        ax.set_ylabel('Número de Reseñas', fontsize=12, fontweight='bold', color='#2C2C2C')
        ax.set_title('Distribución de Valoraciones por Estrellas', 
                    fontsize=14, fontweight='bold', color='#004E89', pad=20)
        
        # Añadir valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=10)
        
        # Estilo de la grilla
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Colores de ejes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        
        plt.tight_layout()
        plt.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        return path
        
    except Exception as e:
        logger.error(f"Error creando gráfico de valoraciones: {e}")
        return None

def _create_modern_sentiment_chart(df, path):
    """Crear gráfico de sentimiento moderno para PDF"""
    try:
        order = ["muy_negativo", "negativo", "neutro", "positivo", "muy_positivo"]
        labels = ["Muy Negativo", "Negativo", "Neutro", "Positivo", "Muy Positivo"]
        colors = ["#C62828", "#E53935", "#FB8C00", "#43A047", "#2E7D32"]

        v = df['sentiment'].value_counts()
        vals = [int(v.get(k, 0)) for k in order]

        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.barh(labels, vals, color=colors, edgecolor='white', linewidth=2, alpha=0.9)

        # Personalizar gráfico
        ax.set_xlabel('Número de Reseñas', fontsize=12, fontweight='bold', color='#2C2C2C')
        ax.set_ylabel('Sentimiento', fontsize=12, fontweight='bold', color='#2C2C2C')
        ax.set_title('Distribución por Análisis de Sentimiento',
                    fontsize=14, fontweight='bold', color='#004E89', pad=20)

        # Añadir valores en las barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                   f'{int(vals[i])}', ha='left', va='center',
                   fontweight='bold', fontsize=10)

        # Estilo de la grilla
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Colores de ejes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

        plt.tight_layout()
        plt.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        return path

    except Exception as e:
        logger.error(f"Error creando gráfico de sentimiento: {e}")
        return None


def _create_modern_language_chart_pdf(languages, path):
    """Crear gráfico de distribución de idiomas moderno para PDF"""
    try:
        if not languages:
            return None

        # Preparar datos
        labels = [lang['name'] for lang in languages]
        sizes = [lang['percentage'] for lang in languages]
        colors = ['#004E89', '#1E88E5', '#43A047', '#FB8C00', '#E53935', '#8E24AA', '#3949AB', '#00ACC1', '#7CB342', '#F4511E']

        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))

        # Crear gráfico circular
        wedges, texts, autotexts = ax.pie(sizes, colors=colors[:len(labels)],
                                        autopct='%1.1f%%', startangle=90,
                                        wedgeprops={'edgecolor': 'white', 'linewidth': 3, 'alpha': 0.9})

        # Personalizar
        ax.set_title('Distribución de Idiomas en Reseñas\nAnálisis Multilingüe del Cliente',
                    fontsize=16, fontweight='bold', color='#004E89', pad=20)

        # Mejorar legibilidad
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
            text.set_color('#2C2C2C')
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
            autotext.set_color('white')

        # Añadir leyenda con cantidades
        legend_labels = [f"{lang['name']}: {lang['count']:,} reseñas" for lang in languages]
        ax.legend(wedges, legend_labels, title="Idiomas", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        plt.tight_layout()
        plt.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        return path

    except Exception as e:
        logger.error(f"Error creando gráfico de idiomas PDF: {e}")
        return None

# ========================== Generador principal ==========================
def create_modern_pdf_report(df, client_name, output_path, cfg, project_root="."):
    """Crear reporte PDF moderno con tablas estilo Excel"""
    try:
        client_clean = client_name.replace('_', ' ').strip()
        safe_name = client_clean.replace(' ', '_')
        client_dir = Path(cfg.get("output_dir", "./data/reports")) / safe_name
        client_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear estilos
        styles = _create_modern_styles()
        
        # Crear documento PDF
        pdf_path = client_dir / f"{safe_name}_informe_MODERNO.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # Lista de elementos del documento
        story = []
        
        # Portada
        title = Paragraph(f"📊 {cfg.get('report_title', 'Informe ORM y CX')}", styles['ModernTitle'])
        story.append(title)
        
        subtitle = Paragraph(f"Cliente: {client_clean}", styles['ModernSubtitle'])
        story.append(subtitle)
        
        date_text = Paragraph(f"Fecha: {datetime.now().strftime('%d de %B de %Y')}", styles['ModernSubtitle'])
        story.append(date_text)
        
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR))
        story.append(Spacer(1, 20))
        
        # Calcular KPIs
        avg = df["rating_num"].mean() if len(df) else 0
        total = len(df)
        pos = (df["sentiment"].isin(["positivo", "muy_positivo"]).sum() / total * 100) if total else 0
        neg = (df["sentiment"].isin(["negativo", "muy_negativo"]).sum() / total * 100) if total else 0
        
        # Tabla de KPIs
        kpi_data = [
            ("Valoración Media", f"{avg:.2f} ⭐", "Promedio global", "E7F0FA"),
            ("Total Reseñas", f"{total:,}", "Volumen analizado", "E8F5E8"),
            ("% Positivas", f"{pos:.0f}%", "Positivo + Muy positivo", "E8F5E8"),
            ("% Negativas", f"{neg:.0f}%", "Negativo + Muy negativo", "FFEBEE")
        ]
        
        kpi_table = _create_kpi_table(kpi_data, styles)
        if kpi_table:
            story.append(kpi_table)
            story.append(Spacer(1, 20))
        
        # Resumen de datos
        summary_header = Paragraph("📈 Resumen de Datos", styles['SectionHeader'])
        story.append(summary_header)
        
        summary_table = _create_data_summary_table(df, styles)
        if summary_table:
            story.append(summary_table)
            story.append(Spacer(1, 20))
        
        # Gráficos
        charts_header = Paragraph("📊 Indicadores Visuales", styles['SectionHeader'])
        story.append(charts_header)
        
        # Crear gráficos
        g1 = _create_modern_rating_chart(df, client_dir / "rating_chart_pdf.png")
        g2 = _create_modern_sentiment_chart(df, client_dir / "sentiment_chart_pdf.png")
        g3 = _create_modern_language_chart_pdf(cfg.get("languages", []), client_dir / "language_chart_pdf.png")
        
        if g1 and Path(g1).exists():
            img1 = Image(str(g1), width=6*inch, height=3.6*inch)
            story.append(img1)
            story.append(Spacer(1, 10))
        
        if g2 and Path(g2).exists():
            img2 = Image(str(g2), width=6*inch, height=3.6*inch)
            story.append(img2)
            story.append(Spacer(1, 20))
        
        # Análisis de sentimiento
        sentiment_header = Paragraph("🎯 Análisis de Sentimiento Detallado", styles['SectionHeader'])
        story.append(sentiment_header)

        sentiment_table = _create_sentiment_table(df, styles)
        if sentiment_table:
            story.append(sentiment_table)
            story.append(Spacer(1, 20))

        # Análisis de idiomas
        languages_header = Paragraph("🌍 Distribución de Idiomas", styles['SectionHeader'])
        story.append(languages_header)

        languages_table = _create_languages_table_pdf(cfg.get("languages", []), styles)
        if languages_table:
            story.append(languages_table)
            story.append(Spacer(1, 20))

        # Gráfico de idiomas
        if g3 and Path(g3).exists():
            img3 = Image(str(g3), width=6*inch, height=4.5*inch)
            story.append(img3)
            story.append(Spacer(1, 20))

        # Salto de página
        story.append(PageBreak())
        
        # Análisis IA (si está disponible)
        if 'ai_analysis' in cfg:
            ai_header = Paragraph("🤖 Análisis Inteligente", styles['SectionHeader'])
            story.append(ai_header)
            
            ai_text = cfg['ai_analysis']
            for line in ai_text.splitlines():
                if line.strip():
                    para = Paragraph(line, styles['ModernNormal'])
                    story.append(para)
        
        # Construir PDF
        doc.build(story)
        
        logger.info(f"✅ PDF moderno generado: {pdf_path}")
        return str(pdf_path)
        
    except Exception as e:
        logger.error(f"Error generando PDF moderno: {e}")
        raise
