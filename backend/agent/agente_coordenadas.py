#!/usr/bin/env python3
"""
Agente CrewAI con Gemini + PDFs de Madrid + Internet
Versión simplificada sin herramientas de delegación
Ubicado en backend/agent para mejor organización
"""

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

# Importar tareas desde archivo en la misma carpeta
from tareas_madrid import crear_tarea_guia_turistica

# Definir herramientas para CrewAI
class MadridPDFSearchInput(BaseModel):
    """Input para búsqueda en PDFs de Madrid"""
    query: str = Field(description="Consulta para buscar en los PDFs de Madrid")

class MadridPDFSearchTool(BaseTool):
    name: str = "madrid_pdf_search"
    description: str = "Busca información específica en los PDFs oficiales de Madrid sobre turismo, historia y cultura"
    args_schema: Type[BaseModel] = MadridPDFSearchInput
    
    def _run(self, query: str) -> str:
        # Esta herramienta se configurará dinámicamente con el vectorstore
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

def crear_llm_gemini():
    """Configura el LLM Gemini para CrewAI usando litellm"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")
        
        # Configurar variables de entorno para litellm
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Usar configuración compatible con CrewAI/litellm
        from crewai.llm import LLM
        
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=api_key,
            temperature=0.7
        )
        
        print("✅ LLM Gemini configurado correctamente para CrewAI")
        return llm
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        sys.exit(1)

def obtener_info_pdfs(pdf_folder):
    """Obtiene información de los PDFs para verificar cambios"""
    if not os.path.exists(pdf_folder):
        return {}
    
    pdf_info = {}
    for filename in os.listdir(pdf_folder):
        if filename.endswith('.pdf'):
            filepath = os.path.join(pdf_folder, filename)
            # Usar timestamp de modificación y tamaño del archivo
            stat = os.stat(filepath)
            pdf_info[filename] = {
                'size': stat.st_size,
                'modified': stat.st_mtime
            }
    return pdf_info

def guardar_cache_info(cache_folder, pdf_info):
    """Guarda información del caché"""
    os.makedirs(cache_folder, exist_ok=True)
    cache_info_path = os.path.join(cache_folder, "cache_info.json")
    
    cache_data = {
        'created': datetime.now().isoformat(),
        'pdf_files': pdf_info
    }
    
    with open(cache_info_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

def cargar_cache_info(cache_folder):
    """Carga información del caché"""
    cache_info_path = os.path.join(cache_folder, "cache_info.json")
    if not os.path.exists(cache_info_path):
        return None
    
    try:
        with open(cache_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def necesita_actualizacion(pdf_folder, cache_folder):
    """Verifica si el vectorstore necesita actualización"""
    # Verificar si existe el cache
    if not os.path.exists(cache_folder) or not os.path.exists(os.path.join(cache_folder, "index.faiss")):
        return True, "Cache no existe"
    
    # Obtener información actual de PDFs
    pdf_info_actual = obtener_info_pdfs(pdf_folder)
    
    # Cargar información del cache
    cache_info = cargar_cache_info(cache_folder)
    if not cache_info:
        return True, "Información de cache no válida"
    
    pdf_info_cache = cache_info.get('pdf_files', {})
    
    # Comparar archivos
    if set(pdf_info_actual.keys()) != set(pdf_info_cache.keys()):
        return True, "Archivos diferentes"
    
    for filename, info_actual in pdf_info_actual.items():
        info_cache = pdf_info_cache.get(filename, {})
        if (info_actual.get('size') != info_cache.get('size') or 
            info_actual.get('modified') != info_cache.get('modified')):
            return True, f"Archivo modificado: {filename}"
    
    return False, "Cache válido"

def cargar_vectorstore_cache(cache_folder, embeddings):
    """Carga vectorstore desde caché"""
    try:
        vectorstore = FAISS.load_local(
            cache_folder, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vectorstore
    except Exception as e:
        print(f"⚠️ Error cargando cache: {e}")
        return None

def guardar_vectorstore_cache(vectorstore, cache_folder):
    """Guarda vectorstore en caché"""
    try:
        os.makedirs(cache_folder, exist_ok=True)
        vectorstore.save_local(cache_folder)
        return True
    except Exception as e:
        print(f"⚠️ Error guardando cache: {e}")
        return False

def procesar_pdfs(pdf_folder, embeddings):
    """Procesa los PDFs y crea documentos"""
    documents = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    for pdf_file in pdf_files:
        print(f"   📄 Procesando {pdf_file}...")
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            # Agregar metadata del archivo
            for doc in docs:
                doc.metadata['source_file'] = pdf_file
            
            split_docs = text_splitter.split_documents(docs)
            documents.extend(split_docs)
        except Exception as e:
            print(f"   ⚠️ Error procesando {pdf_file}: {e}")
    
    return documents, pdf_files

def inicializar_vectorstore():
    """Inicializa FAISS con los PDFs de Madrid usando sistema de caché"""
    print("📚 Inicializando vectorstore con PDFs de Madrid...")
    
    # Configurar rutas (ahora están en el directorio backend)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(current_dir, "..")
    pdf_folder = os.path.join(backend_dir, "pdfs_madrid")
    cache_folder = os.path.join(backend_dir, "vectorstore_cache")
    
    if not os.path.exists(pdf_folder):
        print(f"❌ Carpeta {pdf_folder} no encontrada")
        return None
    
    # Configurar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Verificar si necesita actualización
    necesita_update, razon = necesita_actualizacion(pdf_folder, cache_folder)
    
    if not necesita_update:
        print(f"✅ Cargando vectorstore desde caché ({razon})")
        vectorstore = cargar_vectorstore_cache(cache_folder, embeddings)
        if vectorstore:
            return vectorstore
        else:
            print("⚠️ Error cargando caché, regenerando...")
    
    print(f"🔄 Actualizando vectorstore ({razon})")
    
    # Procesar PDFs
    documents, pdf_files = procesar_pdfs(pdf_folder, embeddings)
    
    if not documents:
        print("❌ No se pudieron cargar documentos")
        return None
    
    # Crear vectorstore
    vectorstore = FAISS.from_documents(documents, embeddings)
    print(f"✅ Se procesaron {len(pdf_files)} PDFs en FAISS")
    
    # Guardar en caché
    if guardar_vectorstore_cache(vectorstore, cache_folder):
        pdf_info = obtener_info_pdfs(pdf_folder)
        guardar_cache_info(cache_folder, pdf_info)
        print("💾 Vectorstore guardado en caché")
    
    return vectorstore

def buscar_en_pdfs(vectorstore, query, k=5):
    """Busca información en los PDFs usando FAISS"""
    if not vectorstore:
        return "No hay vectorstore disponible."
    
    try:
        results = vectorstore.similarity_search(query, k=k)
        
        if not results:
            return "No se encontró información relevante en los PDFs."
        
        # Organizar resultados por archivo
        info_by_file = {}
        for doc in results:
            filename = doc.metadata.get('source_file', 'archivo_desconocido')
            content = doc.page_content.strip()
            
            if filename not in info_by_file:
                info_by_file[filename] = []
            
            if content and len(content) > 50:  # Filtrar contenido muy corto
                info_by_file[filename].append(content[:500])  # Limitar tamaño
        
        # Formatear respuesta
        response = "🔍 **Información encontrada en PDFs de Madrid:**\n\n"
        for i, (filename, contents) in enumerate(info_by_file.items(), 1):
            response += f"**{i}. Documento: {filename}**\n"
            for content in contents[:2]:  # Máximo 2 fragmentos por archivo
                response += f"{content}...\n\n"
        
        return response
    except Exception as e:
        return f"Error buscando en PDFs: {e}"

def buscar_en_internet(query, max_results=3):
    """Busca información en Internet usando Google"""
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query + ' Madrid turismo')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "No se pudo realizar búsqueda en Internet."
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Buscar resultados de búsqueda
        for result in soup.find_all('div', class_='BVG0Nb')[:max_results]:
            title_elem = result.find('h3')
            snippet_elem = result.find('span')
            
            if title_elem and snippet_elem:
                title = title_elem.get_text().strip()
                snippet = snippet_elem.get_text().strip()
                if len(snippet) > 100:
                    results.append(f"**{title}**\n{snippet[:300]}...")
        
        if results:
            return "🌐 **Información de Internet:**\n\n" + "\n\n".join(results)
        else:
            return "No se encontraron resultados relevantes en Internet."
    
    except Exception as e:
        return f"Error buscando en Internet: {e}"

def buscar_lugares_openstreetmap(lat, lon, radio_metros=1000, categoria=None):
    """
    Busca lugares cercanos usando OpenStreetMap Overpass API (gratuita)
    
    Args:
        lat (float): Latitud
        lon (float): Longitud
        radio_metros (int): Radio de búsqueda en metros
        categoria (str): Categoría de lugar (opcional)
    
    Returns:
        str: Información formateada de los lugares encontrados
    """
    try:
        # URL de Overpass API (gratuita)
        url = "https://overpass-api.de/api/interpreter"
        
        # Mapear categorías a tags de OpenStreetMap
        categoria_tags = {
            'museo': '["tourism"="museum"]',
            'restaurante': '["amenity"~"restaurant|cafe|bar"]',
            'hotel': '["tourism"~"hotel|guest_house"]',
            'parque': '["leisure"="park"]',
            'shopping': '["shop"]',
            'turismo': '["tourism"]',
            'entretenimiento': '["amenity"~"cinema|theatre"]',
            'cultura': '["tourism"~"museum|gallery|attraction"]'
        }
        
        # Construir query para Overpass
        if categoria and categoria.lower() in categoria_tags:
            tag_filter = categoria_tags[categoria.lower()]
        else:
            tag_filter = '["tourism"]'  # Por defecto, lugares turísticos
        
        query = f"""
        [out:json][timeout:25];
        (
          node{tag_filter}(around:{radio_metros},{lat},{lon});
          way{tag_filter}(around:{radio_metros},{lat},{lon});
          relation{tag_filter}(around:{radio_metros},{lat},{lon});
        );
        out center meta;
        """
        
        print(f"🔗 Consultando OpenStreetMap Overpass API...")
        print(f"📍 Coordenadas: {lat}, {lon}")
        print(f"📏 Radio: {radio_metros}m")
        print(f"🏷️ Categoría: {categoria or 'turismo'}")
        print()
        
        # Hacer petición
        response = requests.post(url, data={'data': query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return formatear_resultados_openstreetmap(data, lat, lon, radio_metros)
        else:
            return f"❌ Error en OpenStreetMap API: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error conectando con OpenStreetMap API: {e}"

def formatear_resultados_openstreetmap(data, lat, lon, radio_metros):
    """
    Formatea los resultados de OpenStreetMap en texto legible
    """
    elementos = data.get('elements', [])
    
    if not elementos:
        return f"🗺️ No se encontraron lugares cerca de ({lat}, {lon}) en un radio de {radio_metros/1000:.1f}km"
    
    resultado = f"🗺️ **Lugares encontrados cerca de ({lat}, {lon}) - Radio: {radio_metros/1000:.1f}km**\n"
    resultado += f"🌍 **Datos de OpenStreetMap (gratuito)**\n\n"
    
    # Agrupar por tipo
    por_categoria = {}
    
    for elemento in elementos:
        tags = elemento.get('tags', {})
        nombre = tags.get('name', 'Sin nombre')
        
        if nombre == 'Sin nombre':
            continue  # Saltar lugares sin nombre
        
        # Determinar categoría
        if 'tourism' in tags:
            if tags['tourism'] == 'museum':
                categoria = 'Museo'
            elif tags['tourism'] == 'attraction':
                categoria = 'Atracción Turística'
            elif tags['tourism'] == 'hotel':
                categoria = 'Hotel'
            else:
                categoria = 'Turismo'
        elif 'amenity' in tags:
            if tags['amenity'] in ['restaurant', 'cafe', 'bar']:
                categoria = 'Gastronomía'
            elif tags['amenity'] in ['cinema', 'theatre']:
                categoria = 'Entretenimiento'
            else:
                categoria = 'Servicios'
        elif 'leisure' in tags:
            categoria = 'Ocio'
        elif 'shop' in tags:
            categoria = 'Comercio'
        else:
            categoria = 'General'
        
        # Obtener coordenadas del elemento
        if elemento['type'] == 'node':
            elem_lat = elemento.get('lat', 0)
            elem_lon = elemento.get('lon', 0)
        else:
            # Para ways y relations, usar el centro
            center = elemento.get('center', {})
            elem_lat = center.get('lat', 0)
            elem_lon = center.get('lon', 0)
        
        # Calcular distancia
        if elem_lat and elem_lon:
            import math
            R = 6371000  # Radio de la Tierra en metros
            lat1_rad = math.radians(lat)
            lat2_rad = math.radians(elem_lat)
            delta_lat = math.radians(elem_lat - lat)
            delta_lon = math.radians(elem_lon - lon)
            
            a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distancia = R * c
        else:
            distancia = 0
        
        # Agrupar por categoría
        if categoria not in por_categoria:
            por_categoria[categoria] = []
        
        lugar_info = {
            'nombre': nombre,
            'distancia': distancia,
            'direccion': tags.get('addr:street', '') + ' ' + tags.get('addr:housenumber', ''),
            'website': tags.get('website', ''),
            'telefono': tags.get('phone', ''),
            'tipo': tags.get('tourism', tags.get('amenity', tags.get('leisure', tags.get('shop', '')))),
            'coordenadas': f"{elem_lat:.5f}, {elem_lon:.5f}"
        }
        
        por_categoria[categoria].append(lugar_info)
    
    # Formatear salida por categorías
    for categoria, lugares_cat in por_categoria.items():
        resultado += f"**📍 {categoria.upper()}:**\n"
        
        # Ordenar por distancia
        lugares_cat.sort(key=lambda x: x['distancia'])
        
        for lugar in lugares_cat[:5]:  # Máximo 5 por categoría
            resultado += f"• **{lugar['nombre']}**"
            
            if lugar['distancia'] > 0:
                resultado += f" ({lugar['distancia']:.0f}m)"
            
            resultado += f"\n"
            
            if lugar['direccion'].strip():
                resultado += f"  📍 {lugar['direccion'].strip()}\n"
            
            if lugar['telefono']:
                resultado += f"  📞 {lugar['telefono']}\n"
            
            if lugar['website']:
                resultado += f"  🌐 {lugar['website']}\n"
            
            if lugar['tipo']:
                resultado += f"  🏷️ Tipo: {lugar['tipo']}\n"
            
            resultado += f"  🗺️ Coordenadas: {lugar['coordenadas']}\n"
            resultado += "\n"
        
        resultado += "\n"
    
    return resultado

def main(user_query=None, vectorstore=None, llm=None, adulto=None, infantil=None, accesibilidad=None,
         lat=None, lon=None, radio_km=1.0, categoria_foursquare=None):
    """
    Función principal con integración de OpenStreetMap API
    
    Args:
        lat (float): Latitud para búsqueda de lugares cercanos
        lon (float): Longitud para búsqueda de lugares cercanos
        radio_km (float): Radio de búsqueda en kilómetros
        categoria_foursquare (str): Categoría para filtrar lugares (museo, restaurante, etc.)
    """
    if infantil:
        user_query += " con actividades para niños"
    if adulto:
        user_query += " con actividades para adultos"
    if accesibilidad:
        user_query += " con opciones accesibles"
    print(f"\n🔍 Procesando consulta: {user_query}")
    
    # Buscar información en PDFs e Internet
    pdf_info = buscar_en_pdfs(vectorstore, user_query)
    web_info = buscar_en_internet(user_query)
    
    # Búsqueda en OpenStreetMap si se proporcionan coordenadas
    lugares_info = ""
    if lat is not None and lon is not None:
        print(f"🌍 Buscando lugares cercanos con OpenStreetMap API...")
        radio_metros = int(radio_km * 1000)  # Convertir a metros
        lugares_info = buscar_lugares_openstreetmap(lat, lon, radio_metros, categoria_foursquare)
    
    # Preparar información adicional
    info_adicional = ""
    if lugares_info:
        info_adicional = f"\n\n🌍 LUGARES CERCANOS (OPENSTREETMAP):\n{lugares_info}"

    # Crear herramientas con información contextual
    pdf_search_tool = MadridPDFSearchTool()
    # Configurar la herramienta PDF con el vectorstore actual
    def pdf_search_with_context(query: str) -> str:
        return buscar_en_pdfs(vectorstore, query)
    pdf_search_tool._run = pdf_search_with_context

    internet_search_tool = InternetSearchTool()
    location_search_tool = LocationSearchTool()

    # Crear agente turístico (sin delegación para evitar errores)
    guia_turistico_raton = Agent(
        role='El ratoncito Pérez experto en turismo de Madrid. Su misión es ayudar a las familias a descubrir la ciudad de manera mágica y educativa.',
        goal='Proporcionar información turística práctica y completa sobre Madrid',
        backstory="""Eres un experto guía turístico de Madrid con años de experiencia. 
        Te especializas en información práctica: ubicaciones exactas, coordenadas GPS, 
        transporte público, horarios, precios, y recomendaciones de itinerarios. 
        También tienes conocimientos de historia y cultura para crear guías completas.""",
        llm=llm,
        verbose=True,
        allow_delegation=False  # Deshabilitado para evitar errores
    )
    raton_perez_guide = Agent(
        role="El narrador mágico y guía encantado de la tripulación. Es quien transforma los datos e información en una narrativa cohesiva, emocionante y personalizada para las familias. Se comunica directamente con los usuarios, entregando la experiencia final.",
        goal="Transformar una visita turística en una aventura mágica e interactiva, mezclando hechos históricos con cuentos fantásticos. Su objetivo es generar asombro, nostalgia y diversión, adaptando la experiencia para conectar a niños y adultos por igual.",
        backstory="Soy el Ratón Pérez, un mago-creador cuidadoso que vive en el corazón de Madrid. Llevo siglos recolectando dientes, pero también historias, secretos y leyendas de la ciudad. Mi misión no es solo guardar tesoros, sino también compartirlos. He visto la ciudad crecer y cambiar, y ahora, con mis ayudantes, quiero revelar sus misterios y su encanto a todas las familias, convirtiendo cada rincón en un capítulo de un cuento de hadas.",
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

    madrid_researcher = Agent(
        role="El historiador y erudito de la tripulación. Su trabajo es investigar, recopilar y validar la información histórica, cultural y curiosa sobre los lugares emblemáticos de Madrid. Es el encargado de proveer los hechos y los datos que el equipo necesita para construir las historias.",
        goal="Encontrar datos históricos, curiosidades y leyendas auténticas sobre los monumentos, plazas y edificios de Madrid para enriquecer la experiencia de la familia. Su objetivo es asegurar que la narrativa del Ratón Pérez tenga una base sólida y confiable.",
        backstory="Soy un incansable investigador con un ojo para los detalles. He pasado siglos en los archivos secretos de la Villa y Corte, descubriendo los misterios que se esconden en cada callejuela y cada piedra de la ciudad. Mi pasión es desenterrar los secretos mejor guardados y entregarlos a la tripulación para que la magia del Ratón Pérez sea tan real como la historia misma.",
        llm=llm,
        verbose=True,
        allow_delegation=True,
        tools=[pdf_search_tool, internet_search_tool]
    )

    game_designer = Agent(
        role="El mago de los desafíos y creador de aventuras. Se encarga de diseñar dinámicas de juego divertidas e interactivas que invitan a la familia a explorar y descubrir. Su rol es transformar los datos históricos y las historias mágicas en acertijos, misiones y retos para los niños.",
        goal="Convertir la visita a cada lugar en un juego o una misión. Su objetivo es proponer actividades que mantengan a los niños (y a los adultos) activos y comprometidos, garantizando que el aprendizaje sea una experiencia inolvidable y llena de diversión.",
        backstory="Soy el 'cerebro' detrás de las aventuras del Ratón Pérez. Mi hogar está lleno de mapas, lupas y pergaminos secretos. Me encargo de que cada historia tenga un misterio por resolver y cada rincón de Madrid un desafío que superar. He creado juegos para príncipes, exploradores y aventureros de todas las edades, y mi magia consiste en esconder pistas en los lugares más inesperados.",
        llm=llm,
        verbose=True,
        allow_delegation=True,
        tools=[pdf_search_tool, internet_search_tool, location_search_tool]
    )
    
    # Crear tareas dinámicas basadas en la consulta del usuario
    research_task_coor = Task(
        description=(
            f"Incluye datos históricos, arquitectura, curiosidades y leyendas. "
            f"Si se proporcionan listado de lugares cercanos {info_adicional} selecciona los mas relevantes y cercanos que se pueda ir a pie."
        ),
        expected_output="Crea una lista con los lugares mas relevantes y cercanos que se pueda ir a pie, que no supere los 3000 caracteres",
        agent=madrid_researcher,
    )
    research_task = Task(
        description=(
            f"Busca información detallada sobre: {user_query}. "
            f"Incluye datos históricos, arquitectura, curiosidades y leyendas. "
            f"Si se proporcionan coordenadas ({lat}, {lon}), busca también lugares cercanos."
        ),
        expected_output="Un documento de texto bien estructurado que contenga: Datos Históricos Principales, Curiosidades y Anécdotas, Leyendas Mágicas. Formato: Markdown.",
        agent=madrid_researcher,
    )

    game_task = Task(
        description=(
            f"Usando la información proporcionada por el Madrid Cultural Researcher sobre: {user_query}, "
            f"diseña un acertijo o una pista de 'busca el tesoro' que sea divertida para niños de 8 a 12 años. "
            f"La pista debe estar relacionada con los lugares o actividades mencionadas en la consulta."
        ),
        expected_output="Un acertijo o pista bien formulada y un breve texto de apoyo que explique al guía dónde y cómo usarla durante el tour. Formato: Markdown.",
        agent=game_designer,
    )

    narrative_task = Task(
        description=(
            f"Utilizando la información histórica del Madrid Cultural Researcher y el juego del Adventure Game Designer, "
            f"crea una narrativa mágica y cautivadora para guiar a una familia sobre: {user_query}. "
            f"La narrativa debe ser cálida, cercana y llena de asombro. Debe mezclar hechos reales con cuentos fantásticos, "
            f"apelando a la curiosidad de los niños y a la nostalgia de los adultos. "
            f"El resultado final debe ser un guion de tour inmersivo que invite a la familia a explorar y descubrir."
        ),
        expected_output="Un guion de tour completo en formato de narrativa que incluya: Una introducción, puntos de interés clave con sus datos históricos transformados en historias mágicas, la integración del acertijo o juego, frases que inviten a la exploración y una conclusión emotiva. Formato: Markdown.",
        agent=raton_perez_guide,
    )
    
    # Crear y ejecutar crew con los nuevos agentes
    crew = Crew(
        agents=[guia_turistico_raton, madrid_researcher, game_designer, raton_perez_guide],
        tasks=[research_task_coor, research_task, game_task, narrative_task],
        process=Process.sequential,
        verbose=True
    )
    
    print("\n" + "="*80)
    print("🎯 EJECUTANDO GUÍA TURÍSTICA DE MADRID")
    print("🤖 Agente CrewAI con información integrada")
    fuentes = "📚 PDFs + 🌐 Internet"
    if lugares_info:
        fuentes += " + 🌍 OpenStreetMap"
    print(fuentes)
    print("="*80)
    
    # Ejecutar
    resultado = crew.kickoff()
    
    print("\n" + "="*80)
    print("🎉 GUÍA TURÍSTICA GENERADA")
    print("📋 Información Práctica + Cultural integradas")
    print("="*80)
    print(resultado)
    
    # Guardar resultado en el directorio backend
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.join(current_dir, "..")
        output_file = os.path.join(backend_dir, "guia_madrid_final.md")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Guía Turística de Madrid\n\n")
            f.write(f"**Consulta:** {user_query}\n\n")
            if lat and lon:
                f.write(f"**Coordenadas:** {lat}, {lon} (Radio: {radio_km}km)\n\n")
            f.write(f"**Generado por:** Agentes CrewAI colaborativos con Gemini\n\n")
            f.write(f"---\n\n{resultado}")
        print(f"💾 Guía guardada en: {output_file}")
    except Exception as e:
        print(f"⚠️ Error guardando archivo: {e}")
    
    return resultado


def demo_openstreetmap():
    """
    Función de demostración para probar OpenStreetMap API sin entrada del usuario
    """
    print("🎯 DEMO: Probando OpenStreetMap Overpass API")
    print("=" * 50)
    
    # Coordenadas de ejemplo (Puerta del Sol)
    lat = 40.4170
    lon = -3.7036
    radio_metros = 1000  # 1km
    categoria = "turismo"
    
    print(f"📍 Coordenadas de prueba: {lat}, {lon}")
    print(f"📏 Radio: {radio_metros/1000}km")
    print(f"🏷️ Categoría: {categoria}")
    print()
    
    resultado = buscar_lugares_openstreetmap(lat, lon, radio_metros, categoria)
    print(resultado)
    
    return resultado


if __name__ == "__main__":
    import sys
    
    # Verificar si se pasó argumento 'demo'
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_openstreetmap()
        sys.exit(0)
    
    print("🚀 Iniciando Agente CrewAI con Gemini + PDFs + Internet + OpenStreetMap...")
    print("💡 Tip: Ejecuta 'python agente_coordenadas.py demo' para probar solo OpenStreetMap API")
    
    # Configurar LLM
    llm = crear_llm_gemini()
    
    # Inicializar vectorstore
    vectorstore = inicializar_vectorstore()
    
    # Obtener consulta del usuario
    print("\n🌟 ¿Qué te gustaría saber sobre Madrid? (o presiona Enter para usar consulta por defecto): ", end="")
    
    try:
        user_query = input().strip()
    except EOFError:
        user_query = ""
    
    if not user_query:
        user_query = "mejores atracciones turísticas de Madrid"
    
    # Preguntar por búsqueda con coordenadas
    print("\n📍 ¿Quieres buscar lugares cercanos usando coordenadas GPS? (s/n/ejemplo): ", end="")
    
    try:
        usar_coordenadas = input().strip().lower()
    except EOFError:
        usar_coordenadas = "ejemplo"  # Usar ejemplo por defecto si no hay entrada
    
    lat = None
    lon = None
    radio_km = 1.0
    categoria_foursquare = None
    
    if usar_coordenadas in ['s', 'si', 'sí', 'yes', 'y']:
        try:
            print("\n🗺️ Ingresa las coordenadas GPS:")
            print("   📍 Ejemplos de Madrid:")
            print("      • Puerta del Sol: 40.4170, -3.7036")
            print("      • Museo del Prado: 40.4138, -3.6921")
            print("      • Palacio Real: 40.4180, -3.7144")
            print("      • Parque del Retiro: 40.4153, -3.6844")
            
            lat_input = input("\n   📍 Latitud: ").strip()
            lon_input = input("   📍 Longitud: ").strip()
            
            lat = float(lat_input)
            lon = float(lon_input)
            
            # Radio de búsqueda
            radio_input = input(f"   📏 Radio de búsqueda en km (por defecto {radio_km}): ").strip()
            if radio_input:
                radio_km = float(radio_input)
            
            # Categoría
            print("\n📋 Categorías disponibles para OpenStreetMap:")
            print("   • museo, restaurante, hotel, parque, shopping, turismo, entretenimiento, cultura")
            categoria_input = input("   🏷️ Filtrar por categoría (opcional, Enter para todas): ").strip()
            if categoria_input:
                categoria_foursquare = categoria_input
            
            print(f"\n✅ Búsqueda con OpenStreetMap configurada:")
            print(f"   📍 Coordenadas: {lat}, {lon}")
            print(f"   📏 Radio: {radio_km}km")
            if categoria_foursquare:
                print(f"   🏷️ Categoría: {categoria_foursquare}")
                
        except (ValueError, EOFError):
            print("❌ Error: Coordenadas inválidas. Continuando sin búsqueda por coordenadas.")
            lat = None
            lon = None
    
    # Ejemplo rápido para testing
    elif usar_coordenadas in ['ejemplo', 'test', 'demo', '']:
        print("🎯 Usando coordenadas de ejemplo (Puerta del Sol)")
        lat = 40.4170
        lon = -3.7036
        radio_km = 1.0
        categoria_foursquare = "turismo"
        print(f"✅ Configuración de ejemplo: {lat}, {lon} - Radio: {radio_km}km - Categoría: {categoria_foursquare}")
    
    # Ejecutar agente principal
    main(user_query, vectorstore, llm, 
         lat=lat, 
         lon=lon, 
         radio_km=radio_km,
         categoria_foursquare=categoria_foursquare)
