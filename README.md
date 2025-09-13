# 🏰 Ratoncito Pérez Tourism Agent - Madrid Experience
# MagicPerez - El gran viaje del ratón pérez

<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-green.svg" alt="Status">
  <img src="https://img.shields.io/badge/React-18.3.1-blue.svg" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-Latest-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</div>

## 📖 Descripción

Una aplicación web interactiva que combina la magia del **Ratoncito Pérez** con la rica historia y cultura de **Madrid**, creando experiencias únicas para familias que visitan la ciudad. El proyecto utiliza inteligencia artificial avanzada (CrewAI + Google Gemini) para proporcionar recomendaciones personalizadas de turismo.

### ✨ Características Principales

- 🤖 **Agente IA Inteligente** - Powered by CrewAI y Google Gemini
- 🗺️ **Integración con OpenStreetMap** - Localización precisa de lugares
- 📚 **Base de Conocimiento** - Procesamiento de PDFs con información turística
- 🎨 **Interfaz Moderna** - React + TailwindCSS + Lucide Icons
- ⚡ **API REST Robusta** - FastAPI con documentación automática
- 🏗️ **Arquitectura Escalable** - Frontend/Backend desacoplados

## 🏗️ Estructura del Proyecto

```
├── 📁 backend/                 # API FastAPI + Agente IA
│   ├── 📄 app.py              # Servidor FastAPI principal  
│   ├── 📄 requirements.txt     # Dependencias Python
│   ├── 📄 guia_madrid_resumida.md
│   ├── 📁 agent/              # Módulos del agente CrewAI
│   │   ├── 📄 agente_coordenadas.py
│   │   └── 📄 __init__.py
│   ├── 📁 pdfs_madrid/        # Base de conocimiento (PDFs)
│   └── 📁 vectorstore_cache/   # Cache de embeddings
├── 📁 frontend/               # Aplicación React
│   ├── 📄 package.json        # Dependencias Node.js
│   ├── 📄 tailwind.config.js  # Configuración TailwindCSS
│   ├── 📁 src/
│   │   ├── 📄 App.jsx          # Componente principal
│   │   ├── 📁 components/      # Componentes reutilizables
│   │   ├── 📁 pages/          # Páginas de la aplicación
│   │   ├── 📁 hooks/          # Custom React hooks
│   │   └── 📁 utils/          # Utilidades
│   └── 📁 public/             # Archivos estáticos
├── 📁 img_dataset/            # Imágenes del proyecto
├── 📁 model/                  # Modelos (futuras expansiones)
└── 📄 README.md
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.8+** 
- **Node.js 16+** y **npm**
- **Git**
- **API Key de Google Gemini** ([Obtener aquí](https://ai.google.dev/))

### 🔧 Configuración del Backend

1. **Clona el repositorio**
   ```powershell
   git clone https://github.com/juancmacias/Hakathon_Grupo-6_Reto-2.git
   cd Hakathon_Grupo-6_Reto-2
   ```

2. **Configura el entorno virtual de Python**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instala las dependencias**
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```

4. **Configura las variables de entorno**
- Para la obtención de key es esta dirección: [Generar api key](https://aistudio.google.com/apikey)
   ```powershell
   # Crea un archivo .env en la carpeta backend/
   echo "GOOGLE_API_KEY=tu_api_key_aqui" > .env
   ```

5. **Inicia el servidor backend**
   ```powershell
   python app.py
   ```
   
   El servidor estará disponible en: `http://localhost:8000`
   - 📊 Documentación API: `http://localhost:8000/docs`
   - 🔍 ReDoc: `http://localhost:8000/redoc`

### ⚛️ Configuración del Frontend

1. **Navega a la carpeta del frontend**
   ```powershell
   cd ../frontend
   ```

2. **Instala las dependencias**
   ```powershell
   npm install
   ```

3. **Inicia el servidor de desarrollo**
   ```powershell
   npm start
   ```
   
   La aplicación estará disponible en: `http://localhost:3000`

## 🌟 Uso

### 🖥️ Interfaz de Usuario

1. **Página Principal** - Introducción al Ratoncito Pérez y Madrid
2. **Chat Interactivo** - Conversación con el agente IA 
3. **Mapa Interactivo** - Visualización de lugares recomendados
4. **Perfil de Usuario** - Personalización de preferencias
5. **Acerca de** - Información del proyecto

### 🤖 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/chat` | Envía mensaje al agente IA |
| `GET` | `/health` | Estado del servidor |
| `GET` | `/places/{query}` | Busca lugares en OpenStreetMap |

### 💡 Ejemplo de Uso API

```bash
# Chatear con el agente
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Qué lugares puede visitar una familia con niños en Madrid?",
    "user_preferences": {
      "age_group": "family",
      "interests": ["culture", "parks"]
    }
  }'
```

## 🔄 Gestión de Ramas

### Estrategia de Branching

```
main/                    # Rama principal (producción)
├── develop/             # Rama de desarrollo
├── feature/            # Nuevas funcionalidades
│   ├── feature/chat-ui
│   ├── feature/maps-integration
│   └── feature/dockerfile
├── hotfix/             # Correcciones urgentes
└── release/            # Preparación de releases
```

### Comandos Git Útiles

```powershell
# Crear nueva rama feature
git checkout -b feature/nombre-feature

# Cambiar entre ramas
git checkout main
git checkout develop

# Mergear feature a develop
git checkout develop
git merge feature/nombre-feature

# Push de nueva rama
git push -u origin feature/nombre-feature
```

## 🛠️ Scripts de Desarrollo

### Backend
```powershell
# Activar entorno virtual
.\venv\Scripts\activate

# ir al directorio backend
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
python app.py

# Ejecutar servidor de desarrollo
python app.py
```

### Frontend
```powershell
# ir al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Servidor de desarrollo
npm start

# Build de producción
npm run build

# Análisis del bundle
npm run build && npx serve -s build
```

## 🤝 Contribución

1. **Fork** del repositorio
2. **Crea** una rama feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### 📋 Estándares de Código

- **Python**: Seguir PEP 8, usar `black` para formateo
- **JavaScript**: Prettier + ESLint configurado
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)

## 🚨 Troubleshooting

### Problemas Comunes

**❌ Error de importación en backend**
```powershell
# Solución: Verificar entorno virtual
.\venv\Scripts\activate
pip install -r requirements.txt
```

**❌ CORS error en frontend**
```javascript
// Verificar configuración CORS en backend/app.py
allow_origins=["http://localhost:3000"]
```

**❌ API Key no válida**
```powershell
# Verificar archivo .env
echo $env:GOOGLE_API_KEY  # Windows PowerShell
```

## 👥 Autores

**Grupo 6 - Factoría F5 Alvearium**

| Autor | GitHub | Rol |
|-------|--------|-----|
| Stephanie Ángeles | [@stephyangeles](https://github.com/stephyangeles) | Frontend Developer |
| Oscar Rodriguez | [@osrodgon](https://github.com/osrodgon) | Backend Developer |
| Monica G | [@monigogo](https://github.com/monigogo) | UI/UX Designer |
| Maribel Gutiérrez | [@MaribelGR-dev](https://github.com/MaribelGR-dev) | Full Stack Developer |
| Alfonso Bermúdez | [@GHalfbbt](https://github.GHalfbbt) | DevOps Engineer |
| Juan Carlos Macías | [@juancmacias](https://github.com/juancmacias) | Tech Lead & AI Engineer |

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia MIT** - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **Factoría F5** por la oportunidad del hackathon
- **CrewAI** por el framework de agentes IA
- **Google** por la API de Gemini
- **OpenStreetMap** por los datos geográficos
- **Comunidad Open Source** por las librerías utilizadas

---

<div align="center">
  <p><strong>¿Te gusta el proyecto? ¡Dale una ⭐!</strong></p>
  <p>Hecho con ❤️ por el Grupo 6</p>
</div>
