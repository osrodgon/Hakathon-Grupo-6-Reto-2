#!/usr/bin/env python3
"""
Tareas para el agente de turismo de Madrid
Contiene las definiciones de tareas que usa el agente principal
"""

from crewai import Task

def crear_tarea_guia_turistica(agente, user_query, pdf_info, web_info, info_adicional=""):
    """
    Crea la tarea principal de guía turística para el agente
    
    Args:
        agente: El agente que ejecutará la tarea
        user_query (str): Consulta del usuario
        pdf_info (str): Información extraída de PDFs
        web_info (str): Información de búsquedas web
        info_adicional (str): Información adicional (como datos GPS)
    
    Returns:
        Task: Tarea configurada para CrewAI
    """
    
    return Task(
        description=f"""
        Crea una guía turística completa de Madrid usando TODA la información disponible.
        
        CONSULTA DEL USUARIO: "{user_query}"
        
        === INFORMACIÓN DISPONIBLE ===
        
        📚 INFORMACIÓN DE DOCUMENTOS LOCALES:
        {pdf_info}
        
        🌐 INFORMACIÓN DE INTERNET:
        {web_info}
        
        {info_adicional}
        
        INSTRUCCIONES:
        
        Debes proporcionar una guía completa que incluya:
        - Ubicación exacta y coordenadas GPS de los lugares encontrados
        - Cómo llegar (metro, bus, líneas específicas)
        - Horarios de apertura y precios cuando sea posible
        - Contexto histórico y cultural relevante
        - Recomendaciones prácticas e itinerarios sugeridos
        - Datos curiosos e interesantes
        
        RESULTADO ESPERADO: Una guía unificada, amigable y bien estructurada.
        """,
        agent=agente,
        expected_output="Una guía turística completa que integra información práctica y cultural de Madrid, máximo 250 palabras"
    )

def crear_tarea_busqueda_lugares(agente, user_query, lat, lon, radio_km, categoria=None):
    """
    Crea una tarea específica para búsqueda de lugares por coordenadas
    
    Args:
        agente: El agente que ejecutará la tarea
        user_query (str): Consulta del usuario
        lat (float): Latitud
        lon (float): Longitud
        radio_km (float): Radio de búsqueda en kilómetros
        categoria (str): Categoría de lugares a buscar
    
    Returns:
        Task: Tarea configurada para búsqueda por coordenadas
    """
    
    return Task(
        description=f"""
        Busca y analiza lugares cercanos a las coordenadas especificadas.
        
        CONSULTA: "{user_query}"
        COORDENADAS: {lat}, {lon}
        RADIO: {radio_km}km
        CATEGORÍA: {categoria or "Todas"}
        
        OBJETIVO:
        - Identificar lugares de interés turístico cercanos
        - Proporcionar información práctica de cada lugar
        - Sugerir rutas y horarios de visita
        - Incluir datos históricos y culturales relevantes
        
        FORMATO ESPERADO:
        Lista organizada por categorías con información detallada de cada lugar.
        """,
        agent=agente,
        expected_output="Lista detallada de lugares cercanos con información práctica y cultural, máximo 200 palabras"
    )

def crear_tarea_itinerario(agente, user_query, lugares_info, duracion="1 día"):
    """
    Crea una tarea para generar itinerarios personalizados
    
    Args:
        agente: El agente que ejecutará la tarea
        user_query (str): Consulta del usuario
        lugares_info (str): Información de lugares disponibles
        duracion (str): Duración del itinerario
    
    Returns:
        Task: Tarea configurada para generar itinerarios
    """
    
    return Task(
        description=f"""
        Crea un itinerario turístico personalizado para Madrid.
        
        CONSULTA: "{user_query}"
        DURACIÓN: {duracion}
        
        LUGARES DISPONIBLES:
        {lugares_info}
        
        INSTRUCCIONES:
        - Organizar lugares por proximidad geográfica
        - Considerar horarios de apertura y tiempo de visita
        - Incluir opciones de transporte entre ubicaciones
        - Sugerir momentos ideales para cada visita
        - Añadir recomendaciones gastronómicas cercanas
        
        RESULTADO: Itinerario hora por hora con rutas optimizadas.
        """,
        agent=agente,
        expected_output="Itinerario detallado hora por hora con rutas optimizadas y recomendaciones prácticas"
    )

def crear_tarea_transporte(agente, origen, destinos):
    """
    Crea una tarea especializada en información de transporte
    
    Args:
        agente: El agente que ejecutará la tarea
        origen (str): Punto de origen
        destinos (list): Lista de destinos
    
    Returns:
        Task: Tarea configurada para información de transporte
    """
    
    destinos_str = ", ".join(destinos) if isinstance(destinos, list) else str(destinos)
    
    return Task(
        description=f"""
        Proporciona información detallada de transporte en Madrid.
        
        ORIGEN: {origen}
        DESTINOS: {destinos_str}
        
        INFORMACIÓN REQUERIDA:
        - Opciones de metro (líneas, estaciones, tiempo estimado)
        - Rutas de autobús (líneas EMT, paradas)
        - Alternativas de taxi/VTC con precios aproximados
        - Opciones a pie con tiempo y distancia
        - Consejos para turistas sobre billetes y abonos
        
        RESULTADO: Guía completa de movilidad urbana.
        """,
        agent=agente,
        expected_output="Guía completa de opciones de transporte con tiempos, precios y recomendaciones prácticas"
    )

# Plantillas de tareas predefinidas
PLANTILLAS_TAREAS = {
    "turismo_general": {
        "descripcion": "Guía turística general de Madrid",
        "output_esperado": "Guía completa con principales atracciones turísticas"
    },
    "museos": {
        "descripcion": "Información específica sobre museos de Madrid",
        "output_esperado": "Lista detallada de museos con horarios, precios y contenido"
    },
    "gastronomia": {
        "descripcion": "Guía gastronómica de Madrid",
        "output_esperado": "Recomendaciones de restaurantes y platos típicos"
    },
    "vida_nocturna": {
        "descripcion": "Guía de ocio nocturno en Madrid",
        "output_esperado": "Opciones de entretenimiento nocturno y áreas recomendadas"
    },
    "familia": {
        "descripcion": "Actividades familiares en Madrid",
        "output_esperado": "Atracciones y actividades adecuadas para familias con niños"
    }
}

def crear_tarea_desde_plantilla(agente, tipo_plantilla, user_query, info_adicional=""):
    """
    Crea una tarea basada en plantillas predefinidas
    
    Args:
        agente: El agente que ejecutará la tarea
        tipo_plantilla (str): Tipo de plantilla a usar
        user_query (str): Consulta del usuario
        info_adicional (str): Información adicional
    
    Returns:
        Task: Tarea configurada según la plantilla
    """
    
    if tipo_plantilla not in PLANTILLAS_TAREAS:
        tipo_plantilla = "turismo_general"
    
    plantilla = PLANTILLAS_TAREAS[tipo_plantilla]
    
    return Task(
        description=f"""
        {plantilla["descripcion"]}
        
        CONSULTA DEL USUARIO: "{user_query}"
        
        {info_adicional}
        
        OBJETIVO: {plantilla["descripcion"]}
        
        Proporciona información detallada, práctica y actualizada.
        Incluye datos de ubicación, horarios, precios y recomendaciones.
        """,
        agent=agente,
        expected_output=plantilla["output_esperado"]
    )
