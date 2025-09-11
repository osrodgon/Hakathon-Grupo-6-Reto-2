#!/usr/bin/env python3
"""
Launcher para la API FastAPI del Agente Turístico de Madrid
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.app import run_server
    
    if __name__ == "__main__":
        print("🎯 Ratoncito Pérez Agent - FastAPI Launcher")
        print("="*50)
        
        # Ejecutar servidor en modo desarrollo
        run_server(
            host="127.0.0.1",
            port=8000,
            reload=True
        )
        
except ImportError as e:
    print(f"❌ Error importando la aplicación FastAPI: {e}")
    print("🔧 Instala las dependencias con: pip install -r requirements.txt")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n👋 Servidor detenido por el usuario")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error ejecutando el servidor: {e}")
    sys.exit(1)
