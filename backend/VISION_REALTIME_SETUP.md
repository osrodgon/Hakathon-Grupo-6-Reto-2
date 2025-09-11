# 🔍 Computer Vision en Tiempo Real con Modelo YOLO Personalizado

Este sistema implementa análisis de Computer Vision en tiempo real para identificar lugares de Madrid usando tu modelo YOLO personalizado alojado en Hugging Face.

## 🎯 Características Implementadas

### 1. **Análisis en Tiempo Real con YOLO**
- **WebSocket** para comunicación bidireccional
- **Modelo YOLO ONNX** descargado automáticamente de Hugging Face
- **Detección de objetos/lugares** en tiempo real
- **Inferencia local** (sin llamadas a APIs externas)

### 2. **Integración con Modelo YOLO Personalizado**
- **Descarga automática** desde tu repositorio de Hugging Face
- **ONNX Runtime** para inferencia rápida
- **Preprocesamiento automático** de imágenes (640x640)
- **Postprocesamiento** de bounding boxes y confianzas

### 3. **Procesamiento Optimizado**
- **CPU/GPU** automático según disponibilidad
- **Batch processing** para múltiples detecciones
- **Filtrado por confianza** configurable
- **Mapeo de clases** a lugares de Madrid

## 🛠️ Configuración del Modelo YOLO

### Paso 1: Configurar Variables de Entorno

Crea un archivo `.env` en la carpeta `backend/` con:

```bash
# Tu token de Hugging Face (con permisos de lectura)
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx

# Configuración de tu modelo YOLO
YOLO_REPO_ID=juancmamacias/detect_logo
YOLO_FILENAME=logo_detect_nano.onnx

# Umbral de confianza para detecciones
YOLO_CONFIDENCE_THRESHOLD=0.5
```

### Paso 2: Formato del Modelo YOLO

Tu modelo debe:
- **Ser formato ONNX** (.onnx)
- **Input shape**: [1, 3, 640, 640] (batch, channels, height, width)
- **Output shape**: [1, N, 85] donde N es número de detecciones
- **Output format**: [x_center, y_center, width, height, confidence, class_0_prob, class_1_prob, ...]

### Paso 3: Mapeo de Clases

Actualiza la función `get_class_name()` en `app.py` según las clases que detecta tu modelo:

```python
def get_class_name(class_id: int) -> str:
    class_names = {
        0: "puerta del sol",
        1: "plaza mayor", 
        2: "palacio real",
        # ... agregar todas tus clases
    }
    return class_names.get(class_id, f"clase_{class_id}")
```

## 🚀 Flujo de Procesamiento

### 1. **Carga del Modelo**
```python
# Al iniciar el servidor
model_path = hf_hub_download(
    repo_id="juancmamacias/detect_logo",
    filename="logo_detect_nano.onnx",
    token=HF_TOKEN
)
yolo_model = ort.InferenceSession(model_path)
```

### 2. **Preprocesamiento de Imagen**
```python
# Redimensionar a 640x640
# Normalizar píxeles (0-255 -> 0-1)  
# Cambiar formato HWC -> CHW
# Agregar batch dimension
```

### 3. **Inferencia YOLO**
```python
outputs = yolo_model.run(None, {input_name: input_tensor})
```

### 4. **Postprocesamiento**
```python
# Filtrar por confianza > threshold
# Obtener bounding boxes
# Mapear class_id a nombres de lugares
# Generar respuesta del Ratoncito Pérez
```

## � Cómo Usar

### Frontend:
1. **Abrir Cámara** → Clic en "Abrir Cámara"
2. **Modo Tiempo Real** → Clic en "Modo Tiempo Real"  
3. **Apuntar cámara** → YOLO analiza automáticamente cada 3 segundos
4. **Ver detecciones** → Bounding boxes y lugares identificados

### Backend:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu HF_TOKEN

# Ejecutar servidor
python app.py
```

## 📡 Endpoints Disponibles

### WebSocket: `/ws/vision-stream`
```javascript
// El frontend automáticamente envía frames cada 3 segundos
// Recibe respuestas con detecciones YOLO en tiempo real
```

### HTTP POST: `/vision`
```bash
curl -X POST "http://localhost:8000/vision" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@foto.jpg"
```

## 🔧 Personalización Avanzada

### Cambiar Umbral de Confianza
```python
# En postprocess_yolo_outputs()
conf_threshold = 0.3  # Más detecciones (menos precisas)
conf_threshold = 0.8  # Menos detecciones (más precisas)
```

### Cambiar Tamaño de Input
```python
# En preprocess_image_for_yolo()
target_size = (416, 416)  # Más rápido, menos preciso
target_size = (832, 832)  # Más lento, más preciso
```

### Agregar Nuevas Clases
1. **Reentrenar tu modelo YOLO** con nuevas clases
2. **Actualizar** `get_class_name()` con los nuevos IDs
3. **Agregar** a `MADRID_LANDMARKS` las descripciones

### Mensajes Personalizados del Ratoncito Pérez
```python
def generate_ratoncito_message(analysis_result):
    location = analysis_result.get('location', '')
    confidence = analysis_result.get('confidence', 0.0)
    
    if 'tu_nuevo_lugar' in location:
        return "¡Tu mensaje personalizado aquí! 🐭"
```

## 🐛 Resolución de Problemas

### Modelo No Se Descarga
- Verificar `HF_TOKEN` válido en `.env`
- Comprobar que el modelo es público o tienes acceso
- Verificar `YOLO_REPO_ID` y `YOLO_FILENAME` correctos

### Inferencia Lenta
- **CPU**: Normal para YOLO, considera modelo más pequeño
- **GPU**: Instalar `onnxruntime-gpu` para aceleración CUDA
- **Memoria**: Reducir `target_size` de entrada

### Pocas Detecciones
- Reducir `YOLO_CONFIDENCE_THRESHOLD`
- Verificar que las imágenes tengan buena iluminación
- Comprobar que el modelo fue entrenado con datos similares

### Errores de Formato
- Verificar que el modelo ONNX es compatible con ONNX Runtime
- Comprobar las dimensiones de entrada/salida del modelo

## 📊 Rendimiento

### Velocidad Típica:
- **CPU**: ~200-500ms por frame
- **GPU**: ~50-150ms por frame  
- **Modelo Nano**: Más rápido, menos preciso
- **Modelo Large**: Más lento, más preciso

### Memoria:
- **Modelo Nano**: ~6MB
- **Modelo Small**: ~14MB
- **Modelo Medium**: ~50MB

## 🔒 Seguridad

- **Token HF** solo para descarga, no expuesto al frontend
- **Procesamiento local** (no se envían imágenes a servicios externos)
- **Validación** de formatos y tamaños de imagen
- **Límites** de procesamiento para evitar sobrecarga

---

¡Tu sistema YOLO de Computer Vision en tiempo real está listo! 🎉🔍
