#!/usr/bin/env python3
"""
Agent Package
Contiene el agente principal y las tareas
"""

from agente_coordenadas import main, demo_openstreetmap
from tareas_madrid import crear_tarea_guia_turistica, crear_tarea_busqueda_lugares

__all__ = [
    'main',
    'demo_openstreetmap', 
    'crear_tarea_guia_turistica',
    'crear_tarea_busqueda_lugares'
]
