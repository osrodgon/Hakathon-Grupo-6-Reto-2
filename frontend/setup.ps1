# 🐭✨ Ratoncito Pérez Madrid - Script de Instalación y Ejecución

# Instalación automática de dependencias
Write-Host "🚀 Instalando dependencias de la aplicación Ratoncito Pérez Madrid..." -ForegroundColor Green

# Verificar si Node.js está instalado
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Node.js no está instalado. Por favor, instala Node.js primero." -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host "📦 Instalando dependencias principales..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencias principales instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al instalar dependencias principales" -ForegroundColor Red
    exit 1
}

# Instalar dependencias de desarrollo (Tailwind CSS)
Write-Host "🎨 Instalando Tailwind CSS y dependencias de desarrollo..." -ForegroundColor Yellow
npm install -D tailwindcss postcss autoprefixer

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tailwind CSS instalado correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al instalar Tailwind CSS" -ForegroundColor Red
    exit 1
}

# Mensaje de éxito
Write-Host "`n🎉 ¡Instalación completada exitosamente!" -ForegroundColor Green
Write-Host "🐭✨ La aplicación del Ratoncito Pérez Madrid está lista" -ForegroundColor Magenta

# Preguntar si quiere iniciar la aplicación
$response = Read-Host "`n¿Quieres iniciar la aplicación ahora? (s/n)"

if ($response -eq "s" -or $response -eq "S" -or $response -eq "si" -or $response -eq "SI") {
    Write-Host "`n🚀 Iniciando la aplicación..." -ForegroundColor Green
    Write-Host "📱 La aplicación se abrirá en http://localhost:3000" -ForegroundColor Yellow
    Write-Host "⏹️ Para detener la aplicación, presiona Ctrl+C" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 2
    npm start
} else {
    Write-Host "`n📝 Para iniciar la aplicación más tarde, ejecuta:" -ForegroundColor Yellow
    Write-Host "   cd frontend" -ForegroundColor Cyan
    Write-Host "   npm start" -ForegroundColor Cyan
    Write-Host "`n🐭✨ ¡Que tengas una aventura mágica en Madrid!" -ForegroundColor Magenta
}
