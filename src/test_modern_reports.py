# test_modern_reports.py — Script de prueba para los nuevos formatos modernos
# ORM Analyzer IA PRO — Prueba de Formatos Modernos

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Añadir el directorio src al path
sys.path.append('src')

from report_generator_modern import create_modern_report
from pdf_generator_modern import create_modern_pdf_report

def create_sample_data():
    """Crear datos de muestra para probar los reportes"""
    np.random.seed(42)  # Para resultados reproducibles
    
    # Crear datos de muestra
    n_reviews = 150
    
    # Usuarios de muestra
    users = [
        "María García", "Juan Pérez", "Ana López", "Carlos Ruiz", "Laura Martín",
        "David Sánchez", "Elena González", "Miguel Torres", "Carmen Díaz", "Antonio Vega",
        "Isabel Moreno", "Francisco Jiménez", "Rosa Herrera", "Manuel Castro", "Pilar Ramos"
    ]
    
    # Fechas de muestra (últimos 6 meses)
    dates = pd.date_range(start='2024-07-01', end='2024-12-31', periods=n_reviews)
    
    # Generar valoraciones con distribución realista
    ratings = np.random.choice([1, 2, 3, 4, 5], size=n_reviews, p=[0.05, 0.10, 0.15, 0.30, 0.40])
    
    # Generar sentimientos basados en las valoraciones
    sentiment_map = {
        1: "muy_negativo",
        2: "negativo", 
        3: "neutro",
        4: "positivo",
        5: "muy_positivo"
    }
    sentiments = [sentiment_map[r] for r in ratings]
    
    # Textos de reseñas de muestra
    review_texts = [
        "Excelente servicio, muy recomendable",
        "Muy buena atención al cliente",
        "Servicio correcto, sin más",
        "Podría mejorar en algunos aspectos",
        "No me gustó nada la experiencia",
        "Muy profesional y eficiente",
        "Buen servicio en general",
        "Regular, esperaba algo mejor",
        "Increíble experiencia, volveré",
        "Muy mal servicio, no lo recomiendo",
        "Aceptable pero mejorable",
        "Fantástico, superó mis expectativas",
        "Bueno pero con margen de mejora",
        "Pésimo servicio, muy decepcionante",
        "Muy satisfecho con el resultado"
    ]
    
    # Crear DataFrame
    data = {
        'user': np.random.choice(users, n_reviews),
        'date': dates.strftime('%Y-%m-%d'),
        'rating_num': ratings,
        'text': np.random.choice(review_texts, n_reviews),
        'sentiment': sentiments
    }
    
    df = pd.DataFrame(data)
    return df

def test_modern_docx():
    """Probar generación de DOCX moderno"""
    print("Generando reporte DOCX moderno...")
    
    try:
        # Crear datos de muestra
        df = create_sample_data()
        
        # Configuración
        cfg = {
            'output_dir': './data/reports',
            'report_title': 'Informe ORM y CX - Versión Moderna',
            'openai_model': 'gpt-4o-mini',
            'openai_temperature': 0.3
        }
        
        # Generar reporte
        result = create_modern_report(
            df=df,
            client_name="Empresa_Ejemplo_ChIJ123456789",
            output_path="./data/reports",
            cfg=cfg,
            project_root="."
        )
        
        print(f"Reporte DOCX moderno generado: {result}")
        return True
        
    except Exception as e:
        print(f"Error generando DOCX moderno: {e}")
        return False

def test_modern_pdf():
    """Probar generación de PDF moderno"""
    print("Generando reporte PDF moderno...")
    
    try:
        # Crear datos de muestra
        df = create_sample_data()
        
        # Configuración
        cfg = {
            'output_dir': './data/reports',
            'report_title': 'Informe ORM y CX - Versión Moderna',
            'ai_analysis': """
            Análisis de Sentimiento Detallado:
            
            El análisis de las reseñas muestra una tendencia positiva general con un 70% de comentarios favorables. 
            Los clientes destacan principalmente la calidad del servicio y la atención al cliente.
            
            Recomendaciones:
            - Mantener los estándares actuales de servicio
            - Trabajar en las áreas de mejora identificadas
            - Implementar seguimiento proactivo con clientes
            """
        }
        
        # Generar reporte
        result = create_modern_pdf_report(
            df=df,
            client_name="Empresa_Ejemplo_ChIJ123456789",
            output_path="./data/reports",
            cfg=cfg,
            project_root="."
        )
        
        print(f"Reporte PDF moderno generado: {result}")
        return True
        
    except Exception as e:
        print(f"Error generando PDF moderno: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de formatos modernos...")
    print("=" * 50)
    
    # Crear directorio de salida
    Path("./data/reports").mkdir(parents=True, exist_ok=True)
    
    # Probar DOCX moderno
    docx_success = test_modern_docx()
    print()
    
    # Probar PDF moderno
    pdf_success = test_modern_pdf()
    print()
    
    # Resumen
    print("=" * 50)
    print("RESUMEN DE PRUEBAS:")
    print(f"DOCX Moderno: {'Exito' if docx_success else 'Fallo'}")
    print(f"PDF Moderno: {'Exito' if pdf_success else 'Fallo'}")
    
    if docx_success and pdf_success:
        print("\nTodas las pruebas completadas exitosamente!")
        print("Revisa los archivos generados en ./data/reports/")
    else:
        print("\nAlgunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
