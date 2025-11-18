# test_openstego_manual.py
"""
Analiza archivos con SecurityService (OpenStego, etc.)
Uso: python tests/test_openstego_manual.py (desde backend/)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services import SecurityService
import json

app = create_app('testing')

with app.app_context():
    print("🔍 ANALIZADOR DE ESTEGANOGRAFÍA / SEGURIDAD")
    print("=" * 60)

    # 1. Archivo PNG (con mensaje oculto via OpenStego)
    png_path = input("📁 Ruta del archivo PNG (con mensaje oculto): ").strip()
    if os.path.isfile(png_path):
        print("\n" + "=" * 60)
        print("ANALIZANDO PNG...")
        print("=" * 60)
        result = SecurityService.check_file_steganography(png_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"✅ Risk Level: {result['risk_level']}")
        print(f"✅ Rejected: {'YES' if result['risk_level'] == 'high' else 'NO'}")
    else:
        print("❌ PNG no encontrado.")

    
    

    print("\n✅ Análisis finalizado.")