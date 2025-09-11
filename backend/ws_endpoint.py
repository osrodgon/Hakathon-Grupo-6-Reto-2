
# =================== NUEVO ENDPOINT WEBSOCKET PARA CÁMARA ===================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para recibir frames de video desde la cámara del frontend
    Compatible con el código JavaScript propuesto
    """
    await websocket.accept()
    session_start = datetime.now()
    print(f"🔌 WEBSOCKET /ws CONECTADO a las {session_start.strftime('%H:%M:%S')} - Análisis de frames en tiempo real")
    
    frame_count = 0
    
    try:
        while True:
            try:
                # Recibir frame como string base64 (formato: "data:image/jpeg;base64,...")
                frame_data = await websocket.receive_text()
                frame_count += 1
                current_time = datetime.now()
                
                # Procesar el frame
                if frame_data.startswith("data:image/jpeg;base64,"):
                    # Quitar el prefijo de data URL
                    header, encoded = frame_data.split(",", 1)
                    img_bytes = base64.b64decode(encoded)
                    
                    # Convertir a imagen OpenCV
                    np_arr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # 👉 Aquí aplicas tu modelo con OpenCV o IA
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # ejemplo simple
                        
                        # Calcular estadísticas del frame
                        height, width = frame.shape[:2]
                        mean_brightness = np.mean(gray)
                        
                        # Opcional: Guardar frame para debug (cada 30 frames)
                        if frame_count % 30 == 0:
                            cv2.imwrite("last_frame.jpg", frame)
                            print(f"💾 Frame debug guardado: last_frame.jpg")
                        
                        # Calcular métricas de rendimiento
                        processing_time = (datetime.now() - current_time).total_seconds()
                        session_duration = (current_time - session_start).total_seconds()
                        fps_avg = frame_count / session_duration if session_duration > 0 else 0
                        
                        print(f"📸 Frame #{frame_count} recibido: {width}x{height}, Brillo: {mean_brightness:.1f}")
                        
                        # Log cada 10 frames
                        if frame_count % 10 == 0:
                            print(f"🎯 {frame_count} frames | {fps_avg:.1f} FPS | {session_duration:.1f}s")
                    
                    else:
                        print(f"❌ Error decodificando frame #{frame_count}")
                
                else:
                    print(f"❌ Formato no válido en frame #{frame_count}: {frame_data[:50]}...")
                    
            except Exception as frame_error:
                print(f"❌ Error procesando frame #{frame_count}: {frame_error}")
                
    except WebSocketDisconnect:
        session_duration = (datetime.now() - session_start).total_seconds()
        print(f"🔌 Cliente /ws desconectado después de {frame_count} frames")
        print(f"📊 RESUMEN:")
        print(f"   • Frames: {frame_count}")
        print(f"   • Duración: {session_duration:.1f}s")
        print(f"   • FPS promedio: {frame_count/session_duration:.2f}" if session_duration > 0 else "   • FPS: N/A")
    except Exception as e:
        print(f"❌ ERROR /ws después de {frame_count} frames: {e}")
