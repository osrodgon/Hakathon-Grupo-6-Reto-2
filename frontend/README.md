# 🐭✨ Ratoncito Pérez Madrid - Aventura Familiar

Una aplicación React interactiva que combina la magia del Ratoncito Pérez con la rica historia y cultura de Madrid, creando experiencias únicas para familias que visitan la ciudad.

## 🌟 Características Principales

### 👨‍👩‍👧‍👦 Experiencia Familiar Personalizada
- **Modo Niño**: Historias mágicas, juegos interactivos y aventuras con el Ratoncito Pérez
- **Modo Adulto**: Información histórica, cultural y práctica sobre Madrid
- **Accesibilidad**: Adaptaciones para diferentes necesidades

### 🗺️ Lugares Emblemáticos de Madrid
- Puerta del Sol
- Palacio Real
- Plaza Mayor
- Parque del Retiro
- Museo del Prado
- Templo de Debod

### 💬 Chat Interactivo
- Conversaciones personalizadas con el Ratoncito Pérez
- Respuestas contextuales según el perfil del usuario
- Sugerencias de actividades y juegos

### 🎨 Diseño Atractivo
- Colores inspirados en la identidad del Ratoncito Pérez
- Fuentes personalizadas: Fredoka para títulos, Nunito para texto
- Animaciones suaves y elementos interactivos

## 🛠️ Tecnologías Utilizadas

- **React 18** - Framework principal
- **Tailwind CSS** - Estilos y diseño responsivo
- **Lucide React** - Iconografía moderna
- **Hooks personalizados** - Gestión de estado avanzada
- **Local Storage** - Persistencia de preferencias

## 📁 Estructura del Proyecto

```
frontend/
├── public/
│   └── index.html          # HTML principal con fuentes Google
├── src/
│   ├── components/         # Componentes reutilizables
│   │   ├── common/        # Botones, Cards, Spinners
│   │   └── navigation/    # Menú flotante
│   ├── pages/             # Páginas principales
│   │   ├── LoadingPage.jsx
│   │   ├── ProfilePage.jsx
│   │   ├── HomePage.jsx
│   │   ├── ChatPage.jsx
│   │   ├── MapPage.jsx
│   │   └── AboutPage.jsx
│   ├── hooks/             # Hooks personalizados
│   │   ├── useUserProfile.js
│   │   └── useChat.js
│   ├── utils/             # Utilidades
│   │   ├── dateUtils.js
│   │   └── locationUtils.js
│   ├── data/              # Datos estáticos
│   │   └── madridPlaces.js
│   ├── config/            # Configuración
│   │   └── constants.js
│   ├── App.jsx            # Componente principal
│   ├── index.js           # Punto de entrada
│   └── index.css          # Estilos globales
├── package.json
└── tailwind.config.js
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Node.js (versión 16 o superior)
- npm o yarn

### Pasos de instalación

1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd Hakathon_Grupo-6_Reto-2/frontend
   ```

2. **Instalar dependencias**
   ```bash
   npm install
   ```

3. **Instalar Tailwind CSS**
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

4. **Iniciar el servidor de desarrollo**
   ```bash
   npm start
   ```

5. **Acceder a la aplicación**
   Abrir [http://localhost:3000](http://localhost:3000) en el navegador

## 🎮 Funcionalidades por Pantalla

### 🔄 Loading (Carga)
- Animación de carga con mensajes rotativos
- Transición automática después de 6 segundos
- Elementos visuales atractivos

### 👤 Profile (Perfil)
- Selección de tipo de usuario (niño/adulto)
- Configuración de idioma (español/inglés)
- Opciones de accesibilidad
- Persistencia en localStorage

### 🏠 Home (Inicio)
- Saludo personalizado
- Actividades sugeridas según la hora
- Estadísticas de progreso para niños
- Acceso rápido a funcionalidades principales

### 💬 Chat
- Conversación interactiva con el Ratoncito Pérez
- Respuestas contextuales según el perfil
- Indicador de escritura
- Sugerencias de preguntas

### 🗺️ Map (Mapa)
- Lista de lugares emblemáticos de Madrid
- Filtros por categoría
- Información detallada de cada lugar
- Cálculo de distancias
- Historias mágicas vs información histórica

### ℹ️ About (Nosotros)
- Información del equipo y proyecto
- Misión y valores
- Características principales
- Agradecimientos

## 🎨 Paleta de Colores

- **Amarillo Principal**: `#f8cb39` - Color característico del Ratoncito Pérez
- **Marrón**: `#ac8623` - Para títulos y elementos importantes
- **Rojo**: `#ee4337` - Para acciones y elementos destacados
- **Azul**: `#66c5fe` - Para elementos secundarios
- **Fondo**: `#fff9e8` - Fondo cálido y acogedor

## 📱 Diseño Responsivo

La aplicación está optimizada para:
- 📱 **Móviles** (320px+)
- 📟 **Tablets** (768px+)
- 💻 **Desktop** (1024px+)

## ♿ Accesibilidad

- Soporte para adaptaciones visuales
- Opciones para discapacidad auditiva
- Consideraciones de movilidad
- Navegación por teclado
- Contraste adecuado de colores

## 🌍 Internacionalización

- **Español** (es) - Idioma principal
- **Inglés** (en) - Idioma secundario
- Fácil extensión para más idiomas

## 🔧 Scripts Disponibles

```bash
# Iniciar desarrollo
npm start

# Construir para producción
npm run build

# Ejecutar tests
npm test

# Expulsar configuración (irreversible)
npm run eject
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para detalles.

## 👥 Equipo

- **Equipo Madrid Mágico** - Desarrollo y diseño
- **Ratoncito Pérez** - Director de Magia 🐭✨

## 🙏 Agradecimientos

- A todas las familias que inspiran este proyecto
- A Madrid, por ser una ciudad llena de magia e historia
- A la comunidad de React por las herramientas increíbles

---

**¡Hecho con ❤️ para familias visitando Madrid!**

🐭✨ *"La magia está en todas partes si sabes cómo buscarla"* - Ratoncito Pérez
