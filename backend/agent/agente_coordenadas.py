#!/usr/bin/env python3
"""
Agente CrewAI Simplificado - Solo 2 Agentes especializados
Versión optimizada para Madrid con Ratón Pérez
"""

from email.policy import default
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import warnings
import json
import hashlib
from datetime import datetime
warnings.filterwarnings("ignore")

# Configuración de variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Imports principales
from crewai.llm import LLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

# Mapa para traducir los códigos de la WMO a descripciones en español
WEATHER_CODES = {
    0: "Cielo despejado",
    1: "Principalmente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con hielo",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    66: "Lluvia helada ligera",
    67: "Lluvia helada fuerte",
    71: "Nieve ligera",
    73: "Nieve moderada",
    75: "Nieve fuerte",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve fuertes",
    95: "Tormenta eléctrica",
    96: "Tormenta eléctrica con granizo ligero",
    99: "Tormenta eléctrica con granizo fuerte"
}

# Definir herramientas especializadas
class MadridPDFSearchInput(BaseModel):
    """Input para búsqueda en PDFs de Madrid"""
    query: str = Field(description="Consulta para buscar en los PDFs de Madrid")

class MadridPDFSearchTool(BaseTool):
    name: str = "madrid_pdf_search"
    description: str = "Busca información específica en los PDFs oficiales de Madrid sobre turismo, historia y cultura"
    args_schema: Type[BaseModel] = MadridPDFSearchInput
    
    def _run(self, query: str) -> str:
        return "Herramienta de búsqueda en PDFs configurada dinámicamente"

class InternetSearchInput(BaseModel):
    """Input para búsqueda en Internet"""
    query: str = Field(description="Consulta para buscar información en Internet")

class InternetSearchTool(BaseTool):
    name: str = "internet_search"
    description: str = "Busca información actualizada en Internet sobre Madrid, turismo y actividades"
    args_schema: Type[BaseModel] = InternetSearchInput
    
    def _run(self, query: str) -> str:
        return buscar_en_internet(query)

class LocationSearchInput(BaseModel):
    """Input para búsqueda de lugares cercanos"""
    lat: float = Field(description="Latitud")
    lon: float = Field(description="Longitud")
    radius_km: float = Field(default=1.0, description="Radio de búsqueda en kilómetros")
    category: str = Field(default="turismo", description="Categoría de lugares a buscar")

class LocationSearchTool(BaseTool):
    name: str = "location_search"
    description: str = "Busca lugares cercanos usando coordenadas GPS y OpenStreetMap"
    args_schema: Type[BaseModel] = LocationSearchInput
    
    def _run(self, lat: float, lon: float, radius_km: float = 1.0, category: str = "turismo") -> str:
        radius_meters = int(radius_km * 1000)
        return buscar_lugares_openstreetmap(lat, lon, radius_meters, category)
    
class WeatherSearchInput(BaseModel):
    """Input para la obtención de la previsión del tiempo"""
    latitude: float = Field(description="Latitud")
    longitude: float = Field(description="Longitud")
    forecast_days: int = Field(default=3, description="Número de días")
    
class WeatherSearchTool(BaseModel):
    name: str = "weather_search"
    description: str = "Obtiene la previsión del tiempo usando coordenadas GPS y Open-Meteo"
    args_schema: Type[BaseModel] =WeatherSearchInput
    
    def _run(self, latitude: float, longitude: float, forecast_days: int):
        return get_weather_forecast(latitude, longitude, forecast_days)

def crear_llm_gemini():
    """Configura el LLM Gemini para CrewAI usando litellm"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")
        
        os.environ["GEMINI_API_KEY"] = api_key
        
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=api_key,
            temperature=0.7
        )
        
        print("✅ LLM Gemini configurado correctamente para CrewAI")
        return llm
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        return None

def cargar_vectorstore():
    """Carga el vectorstore desde cache o crea uno nuevo"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(current_dir, "..", "vectorstore_cache")
        
        if os.path.exists(os.path.join(cache_dir, "index.faiss")):
            print("📚 Cargando vectorstore desde cache...")
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            vectorstore = FAISS.load_local(cache_dir, embeddings, allow_dangerous_deserialization=True)
            print("✅ Vectorstore cargado desde cache")
            return vectorstore
        else:
            print("❌ Cache no encontrado, necesita crear vectorstore")
            return None
    except Exception as e:
        print(f"❌ Error cargando vectorstore: {e}")
        return None

def buscar_en_pdfs(vectorstore, query, k=5):
    """Busca información en el vectorstore de PDFs de Madrid"""
    try:
        if not vectorstore:
            return "❌ Vectorstore no disponible"
        
        docs = vectorstore.similarity_search(query, k=k)
        
        resultados = []
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:500]
            source = doc.metadata.get('source', 'Fuente desconocida')
            resultados.append(f"📄 **Resultado {i}** ({os.path.basename(source)}):\n{content}\n")
        
        return "\n".join(resultados) if resultados else "No se encontró información relevante en los PDFs."
        
    except Exception as e:
        return f"❌ Error en búsqueda de PDFs: {e}"

def buscar_en_internet(query, max_results=3):
    """Busca información actualizada en Internet sobre Madrid"""
    try:
        query_encoded = quote_plus(f"{query} Madrid turismo 2024")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://www.google.com/search?q={query_encoded}&num={max_results}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Buscar resultados de búsqueda
            for i, item in enumerate(soup.find_all('div', class_='g')[:max_results], 1):
                title_elem = item.find('h3')
                snippet_elem = item.find('span', {'data-ved': True})
                
                if title_elem and snippet_elem:
                    title = title_elem.get_text()
                    snippet = snippet_elem.get_text()
                    results.append(f"🌐 **Resultado {i}**: {title}\n{snippet}\n")
            
            if results:
                return "\n".join(results)
        
        # Información de fallback para lugares famosos de Madrid
        fallback_info = get_madrid_fallback_info(query)
        if fallback_info:
            return f"📚 **Información disponible sobre Madrid:**\n{fallback_info}"
        else:
            return "❌ No se pudo acceder a la información de internet"
            
    except Exception as e:
        # Información de fallback en caso de error
        fallback_info = get_madrid_fallback_info(query)
        if fallback_info:
            return f"📚 **Información disponible sobre Madrid:**\n{fallback_info}"
        else:
            return f"❌ Error en búsqueda de internet: {e}"

def get_madrid_fallback_info(query):
    """Proporciona información básica sobre lugares famosos de Madrid"""
    query_lower = query.lower()
    
    madrid_info = {
        "puerta del sol": """
        🏛️ **Puerta del Sol - El Corazón de Madrid**

        **Historia:**
        - Plaza desde el siglo XV, originalmente una de las puertas de la muralla medieval
        - Kilómetro 0 de las carreteras radiales españolas
        - Lugar histórico de celebraciones y manifestaciones importantes

        **Atractivos principales:**
        - Reloj de la Casa de Correos (campanadas de Año Nuevo)
        - Estatua del Oso y el Madroño (escudo de Madrid)
        - Kilómetro 0 marcado en el suelo
        - Tiendas y cafeterías históricas

        **Información práctica:**
        - Acceso: Metro Sol (líneas 1, 2 y 3)
        - Horario: Acceso libre 24 horas
        - Mejores momentos: Mañana temprano o tarde-noche
        """,
                
                "parque del retiro": """
        🌳 **Parque del Retiro - El Pulmón Verde de Madrid**

        **Historia:**
        - Creado en el siglo XVII para recreo de la realeza
        - Abierto al público en 1868
        - 125 hectáreas de jardines y monumentos

        **Atractivos principales:**
        - Palacio de Cristal (1887)
        - Estanque Grande con barcas de remo
        - Rosaleda y Jardín de Vivaces
        - Múltiples monumentos y esculturas

        **Información práctica:**
        - Acceso: Metro Retiro, Príncipe de Vergara
        - Horario: 6:00-24:00 (horario variable según época)
        - Entrada: Gratuita
        """,
                
                "museo del prado": """
        🎨 **Museo del Prado - Tesoro Artístico Mundial**

        **Historia:**
        - Inaugurado en 1819
        - Una de las pinacotecas más importantes del mundo
        - Más de 8.000 pinturas y 1.000 esculturas

        **Atractivos principales:**
        - Obras de Velázquez, Goya, El Greco
        - Las Meninas, Las Pinturas Negras
        - Colección de pintura española, italiana y flamenca

        **Información práctica:**
        - Acceso: Metro Banco de España, Atocha
        - Horario: 10:00-20:00 (lunes a sábado), 10:00-19:00 (domingos)
        - Entrada: 15€ adultos, gratis última hora
        """,
                
                "palacio real": """
        👑 **Palacio Real - Residencia de la Realeza**

        **Historia:**
        - Construido en el siglo XVIII sobre el antiguo Alcázar
        - Residencia oficial de los Reyes de España
        - 3.418 habitaciones, una de las más grandes de Europa

        **Atractivos principales:**
        - Salón del Trono y Sala de Gasparini
        - Armería Real y Farmacia Real
        - Jardines de Sabatini y Campo del Moro

        **Información práctica:**
        - Acceso: Metro Ópera
        - Horario: 10:00-18:00 (verano hasta 19:00)
        - Entrada: 13€ adultos, reducida para familias
        """
    }
    
    # Buscar coincidencias en la query
    for lugar, info in madrid_info.items():
        if any(palabra in query_lower for palabra in lugar.split()):
            return info
    
    # Información general si no encuentra lugar específico
    if any(word in query_lower for word in ["madrid", "turismo", "ver", "visitar"]):
        return """
            🏙️ **Madrid - Capital de España**

            **Lugares imprescindibles:**
            - Puerta del Sol (centro neurálgico)
            - Parque del Retiro (naturaleza en la ciudad)
            - Museo del Prado (arte mundial)
            - Palacio Real (historia y arquitectura)
            - Gran Vía (shopping y espectáculos)
            - Mercado de San Miguel (gastronomía)

            **Consejos prácticos:**
            - Metro: Mejor transporte público
            - Horarios: Museos cierran los lunes
            - Comidas: 14:00-16:00 y 21:00-23:00
            - Propinas: 5-10% en restaurantes
            """
    
    return None

def buscar_lugares_openstreetmap(lat, lon, radius_meters=1000, category="tourism"):
    """Busca lugares cercanos usando la API de OpenStreetMap"""
    try:
        # Mapear categorías a tags de OSM
        tag_mapping = {
            'turismo': 'tourism',
            'museo': 'tourism=museum',
            'restaurante': 'amenity=restaurant',
            'hotel': 'tourism=hotel',
            'parque': 'leisure=park',
            'shopping': 'shop',
            'entretenimiento': 'amenity=cinema|amenity=theatre',
            'cultura': 'tourism=museum|tourism=gallery'
        }
        
        osm_tag = tag_mapping.get(category.lower(), 'tourism')
        
        # Construir consulta Overpass
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node[{osm_tag}](around:{radius_meters},{lat},{lon});
          way[{osm_tag}](around:{radius_meters},{lat},{lon});
          relation[{osm_tag}](around:{radius_meters},{lat},{lon});
        );
        out center meta;
        """
        
        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data=overpass_query, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            elementos = data.get('elements', [])
            
            if not elementos:
                return f"No se encontraron lugares de tipo '{category}' en un radio de {radius_meters/1000}km"
            
            # Procesar resultados
            lugares = []
            for elemento in elementos[:10]:  # Limitar a 10 resultados
                tags = elemento.get('tags', {})
                nombre = tags.get('name', 'Sin nombre')
                
                if nombre == 'Sin nombre':
                    continue
                
                # Información adicional
                direccion = tags.get('addr:street', '')
                if tags.get('addr:housenumber'):
                    direccion += f" {tags.get('addr:housenumber')}"
                
                descripcion = tags.get('description', '')
                website = tags.get('website', '')
                
                lugar_info = f"📍 **{nombre}**"
                if direccion:
                    lugar_info += f"\n   📍 {direccion}"
                if descripcion:
                    lugar_info += f"\n   📝 {descripcion[:100]}..."
                if website:
                    lugar_info += f"\n   🌐 {website}"
                
                lugares.append(lugar_info)
            
            return "\n\n".join(lugares) if lugares else f"No se encontraron lugares con nombre en la categoría '{category}'"
        else:
            return f"❌ Error en consulta a OpenStreetMap: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error buscando lugares: {e}"
    
def get_weather_forecast_json(latitude: float, longitude: float, forecast_days: int = 3):
    """
    Obtiene la previsión del tiempo para los próximos días.

    Args:
        latitude (float): La latitud de la ubicación.
        longitude (float): La longitud de la ubicación.
        forecast_days (int): El número de días para la previsión.

    Returns:
        list: Una lista de diccionarios con el pronóstico del tiempo.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Europe%2FMadrid&forecast_days={forecast_days}"
    
    try:
        response = requests.get(url)
                
        return response
    except requests.exceptions.RequestException as e:
        return None
    
def get_weather_forecast(latitude: float, longitude: float, forecast_days: int = 3):
    """
    Obtiene la previsión del tiempo para los próximos días.

    Args:
        latitude (float): La latitud de la ubicación.
        longitude (float): La longitud de la ubicación.
        forecast_days (int): El número de días para la previsión.

    Returns:
        list: Una lista de diccionarios con el pronóstico del tiempo.
    """
    
    response = get_weather_forecast_json(latitude, longitude, forecast_days)
    data = response.json()    

    if data:
        # Extraer los datos relevantes
        daily_data = data.get("daily", {})
        forecast = []

        if daily_data:
            for i in range(len(daily_data["time"])):
                weather_code = daily_data["weather_code"][i]

                # Convertir la cadena de fecha a un objeto datetime
                date_obj = datetime.strptime(daily_data['time'][i], "%Y-%m-%d")
                # Formatear la fecha en español
                formatted_date = date_obj.strftime("%A %d de %B")

                info = f"📈 **Fecha: {formatted_date.capitalize()}**n\n"
                info += f"    \n"
                info += f"    Máx. Temp: {daily_data['temperature_2m_max'][i]} °C\n"
                info += f"    Mín. Temp: {daily_data['temperature_2m_min'][i]} °C\n"
                info += f"    Condición: {WEATHER_CODES.get(weather_code, 'Condición desconocida')}\n"

                forecast.append(info)
                
        return forecast if forecast else "No se ha encontrado la previsión del tiempo."
    else:
        return f"❌ Error en consulta a Open-Meteo: {response.status_code}"

def main(user_query, llm, vectorstore, lat=None, lon=None, radio_km=1.0, 
         categoria_foursquare="turismo", infantil=False, adulto=False, accesibilidad=False):
    """
    Función principal con 2 agentes especializados CrewAI
    """
    print(f"\n🔍 Procesando consulta: {user_query}")
    if infantil:
        user_query += " actividades para niños"
    if adulto:  
        user_query += " actividades para niños y adolecentes"
    if accesibilidad:
        user_query += " accesibilidad para personas con movilidad reducida"

    
    # Crear herramientas especializadas
    pdf_search_tool = MadridPDFSearchTool()
    # Configurar la herramienta PDF con el vectorstore actual
    def pdf_search_with_context(query: str) -> str:
        return buscar_en_pdfs(vectorstore, query)
    pdf_search_tool._run = pdf_search_with_context

    internet_search_tool = InternetSearchTool()
    location_search_tool = LocationSearchTool()
    weather_search_tool = WeatherSearchTool()

    # AGENTE 1: Investigador Cultural de Madrid (Historia + Información actual)
    madrid_researcher = Agent(
        role="Investigador Cultural de Madrid",
        goal="Recopilar información histórica, cultural y práctica sobre Madrid. Combinar datos de archivos oficiales, PDFs especializados e información actualizada de internet para crear una base sólida de conocimiento verificable.",
        backstory="""Soy la Dra. Elena Vega, historiadora y investigadora cultural especializada en Madrid. 
        Trabajo para Madrid Destino y colaboro con el Archivo de Villa. Durante 20 años he documentado 
        la evolución de la ciudad, desde sus orígenes árabes hasta la actualidad. Mi especialidad es 
        conectar el pasado histórico con el presente vibrante de Madrid, encontrando las historias 
        humanas que hacen únicos los lugares. Tengo acceso privilegiado a archivos históricos y 
        mantengo una red de contactos locales que me proporcionan información actualizada.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        memory=False,
        tools=[pdf_search_tool, internet_search_tool, location_search_tool]
    )

    # AGENTE 2: Creador de Experiencias Familiares (Ratón Pérez + Actividades)
    family_guide_creator = Agent(
        role="Creador de Experiencias Familiares del Raton Perez",
        goal="Transformar información histórica y cultural en experiencias familiares memorables protagonizadas por el Ratón Pérez. Crear narrativas mágicas, diseñar actividades interactivas y proporcionar consejos prácticos para familias multigeneracionales.",
        backstory="""¡Hola! Soy Carmen Pérez, y trabajo directamente con el mismísimo Ratón Pérez desde hace años. 
        Soy pedagoga especializada en turismo familiar y storytelling. Junto con Ratoncito, hemos creado 
        más de 100 aventuras mágicas en Madrid, combinando metodologías educativas innovadoras con narrativas 
        fantásticas. Mi don especial es hablar el 'idioma' tanto de niños como de adultos, creando momentos 
        donde todos se sienten protagonistas. Conozco cada rincón child-friendly de Madrid y sé exactamente 
        dónde están los mejores helados después de una aventura cultural.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        memory=False,
        tools=[location_search_tool]
    )

    # TAREA 1: Investigación Cultural Completa
    research_task = Task(
        description=(
            f"INVESTIGACIÓN CULTURAL COMPLETA sobre: {user_query}\n\n"
            f"OBJETIVOS:\n"
            f"1. Recopilar información histórica precisa: fechas, personajes, eventos\n"
            f"2. Buscar datos prácticos actualizados: horarios, precios, accesibilidad\n"
            f"3. Identificar curiosidades y anécdotas verificables\n"
            f"4. Localizar lugares cercanos de interés (si hay coordenadas: {lat}, {lon})\n"
            f"5. Obtener información de transporte y logística\n\n"
            f"FUENTES A UTILIZAR:\n"
            f"- PDFs oficiales de Madrid (archivo especializado)\n"
            f"- Internet para información actualizada\n"
            f"- OpenStreetMap para lugares cercanos\n\n"
            f"Proporciona información sólida y verificable que será la base para la experiencia familiar."
        ),
        expected_output="Documento estructurado en Markdown con: 1) Información histórica verificada, 2) Datos prácticos actualizados, 3) Curiosidades interesantes, 4) Lugares cercanos relevantes, 5) Información de transporte y logística. Que no supere las 500 palabras.",
        agent=madrid_researcher,
        tools=[pdf_search_tool, internet_search_tool, location_search_tool]
    )

    # TAREA 2: Creación de Experiencia Familiar con el Ratón Pérez
    family_experience_task = Task(
        description=(
            f"CREAR EXPERIENCIA FAMILIAR MÁGICA basada en la investigación sobre: {user_query}\n\n"
            f"OBJETIVOS:\n"
            f"1. Transformar datos históricos en narrativa del Ratón Pérez\n"
            f"2. Diseñar 2-3 actividades interactivas para diferentes edades\n"
            f"3. Crear un acertijo o búsqueda del tesoro relacionada\n"
            f"4. Proporcionar consejos prácticos para familias\n"
            f"5. Incluir recomendaciones de horarios y presupuesto\n\n"
            f"ELEMENTOS REQUERIDOS:\n"
            f"- Historia protagonizada por el Ratón Pérez en primera persona\n"
            f"- Actividades para niños (6-12 años) y adolescentes\n"
            f"- Acertijo con pistas y solución\n"
            f"- Consejos de vestimenta y equipamiento\n"
            f"- Momentos fotográficos especiales\n"
            f"- Información sobre lugares cercanos para comer/descansar"
        ),
        expected_output="Guía familiar completa en formato Markdown con: 1) Historia narrada por el Ratón Pérez en primera persona, 2) Actividades interactivas paso a paso, 3) Acertijo con pistas y solución, 4) Consejos prácticos completos",
        agent=family_guide_creator,
        tools=[location_search_tool],
        context=[research_task]  # Depende de la investigación
    )
    
    # Crear crew simplificado con 2 agentes
    crew = Crew(
        agents=[madrid_researcher, family_guide_creator],
        tasks=[research_task, family_experience_task],
        process=Process.sequential,
        verbose=True,
        memory=False  # Desactivar memoria para evitar problemas
    )
    
    print("\n" + "="*80)
    print("🎯 EJECUTANDO GUÍA TURÍSTICA DE MADRID")
    print("🤖 2 Agentes CrewAI especializados + Ratón Pérez")
    fuentes = "📚 PDFs + 🌐 Internet + 🗺️ OpenStreetMap"
    if lat and lon:
        fuentes += f" (Coordenadas: {lat}, {lon})"
    print(fuentes)
    print("="*80)
    
    # Ejecutar crew
     
    resumen = crew.kickoff()
    print("\n" + "="*80)
    print("🎉 MINI-GUÍA GENERADA")
    print("="*80)
    print(resumen)
    # Guardar solo la versión corta
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.join(current_dir, "..")
        output_file = os.path.join(backend_dir, "guia_madrid_resumida.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Mini-Guía Turística de Madrid - Ratón Pérez\n\n")
            f.write(f"**Consulta:** {user_query}\n\n")
            if lat and lon:
                f.write(f"**Coordenadas:** {lat}, {lon} (Radio: {radio_km}km)\n\n")
            f.write(f"**Generado por:** 2 Agentes CrewAI especializados\n")
            f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"---\n\n{resumen}")
        print(f"✅ Mini-guía guardada en: {output_file}")
    except Exception as e:
        print(f"⚠️ Error guardando archivo: {e}")
    return resumen


def inicializar_vectorstore():
    """Función de compatibilidad para inicializar vectorstore (alias de cargar_vectorstore)"""
    return cargar_vectorstore()

def openstreetmap(lat=40.4170, lon=-3.7036, radius_km=1.0, category="turismo"):
    """
    Función para OpenStreetMap
    Busca lugares cercanos usando las coordenadas proporcionadas
    """
    try:
        radius_meters = int(radius_km * 1000)
        resultado = buscar_lugares_openstreetmap(lat, lon, radius_meters, category)
        
        print(f"\n🗺️ OPENSTREETMAP")
        print(f"📍 Coordenadas: {lat}, {lon}")
        print(f"📏 Radio: {radius_km}km")
        print(f"🏷️ Categoría: {category}")
        print("="*50)
        print(resultado)
        
        return resultado
    except Exception as e:
        print(f"❌ Error en OpenStreetMap: {e}")
        return f"Error: {e}"
    
def weather_forecast(latitude: float, longitude: float, forecast_days: int = 3):
    try:
        forecast_data = get_weather_forecast(latitude, longitude, forecast_days)

        print(f"\📈 Open-Meteo")
        print(f"📍 Coordenadas: {latitude}, {longitude}")
        print("="*50)
        print(forecast_data)
        
        return forecast_data
    except Exception as e:
        print(f"❌ Error en Open Meteo: {e}")
        return f"Error: {e}"

if __name__ == "__main__":
    # Prueba rápida del sistema simplificado
    print("🔥 SISTEMA DE GUÍAS TURÍSTICAS")
    print("🤖 2 Agentes CrewAI + Ratón Pérez")
    print("="*50)
    
    # Cargar LLM y vectorstore
    llm = crear_llm_gemini()
    vectorstore = cargar_vectorstore()
    
    if llm and vectorstore:
        resultado = main(
            user_query="Qué ver en el Parque del Retiro",
            llm=llm,
            vectorstore=vectorstore,
            lat=40.4152,
            lon=-3.6844,
            radio_km=1.0
        )
        print("\n🎯 RESULTADO FINAL:")
        print(resultado)
    else:
        print("❌ Error: No se pudo inicializar LLM o vectorstore")
