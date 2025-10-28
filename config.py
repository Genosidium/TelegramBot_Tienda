"""
Archivo de configuración para el Bot de Telegram
Contiene las constantes y configuraciones del sistema
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env (si existe)
load_dotenv()

# ====================================
# CONFIGURACIÓN DEL BOT
# ====================================

# Token del bot de Telegram (obtenido de BotFather)
# Opción 1: Usar variable de entorno (más seguro)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or ''

# Chat ID del administrador (opcional)
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
if ADMIN_CHAT_ID:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    except ValueError:
        ADMIN_CHAT_ID = None

# Opción 2: Si prefieres hardcodearlo (menos seguro, solo para desarrollo)
# TELEGRAM_TOKEN = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'

# ====================================
# CONFIGURACIÓN DE BASE DE DATOS
# ====================================

# Nombre del archivo de base de datos (se puede sobrescribir desde .env con DATABASE_NAME)
DB_FILE = os.getenv('DATABASE_NAME', 'inventario.json')

# Directorio para respaldos (opcional)
BACKUP_DIR = 'backups'

# ====================================
# CONFIGURACIÓN DE INVENTARIO
# ====================================

# Porcentaje mínimo de stock para alertas
# Se acepta PORCENTAJE_ALERTA_MINIMO en .env. Si está en formato entero (ej. 10) lo convertimos a 0.10
_porcentaje_env = os.getenv('PORCENTAJE_ALERTA_MINIMO')
if _porcentaje_env:
    try:
        _val = float(_porcentaje_env)
        # Si el valor parece un porcentaje entero (>=1), convertir a fracción
        if _val > 1:
            STOCK_MINIMO_PORCENTAJE = _val / 100.0
        else:
            STOCK_MINIMO_PORCENTAJE = _val
    except Exception:
        STOCK_MINIMO_PORCENTAJE = 0.10
else:
    STOCK_MINIMO_PORCENTAJE = 0.10  # 10%

# Categorías predefinidas (opcional)
CATEGORIAS_DISPONIBLES = [
    'Granos',
    'Frutas',
    'Legumbres',
    'Dulces',
    'Bebidas',
    'Lácteos',
    'Carnes',
    'Verduras',
    'Otros'
]

# ====================================
# CONFIGURACIÓN DE SEGURIDAD
# ====================================

# IDs de usuarios autorizados (opcional, dejar lista vacía para permitir a todos)
# Para obtener tu ID, puedes usar el bot @userinfobot en Telegram
USUARIOS_AUTORIZADOS = []  # Ejemplo: [123456789, 987654321]

# Habilitar modo de solo lectura para ciertos usuarios (opcional)
USUARIOS_SOLO_LECTURA = []

# ====================================
# CONFIGURACIÓN DE MENSAJES
# ====================================

# Nombre de la tienda
NOMBRE_TIENDA = "Tienda Doña Rosa"

# Mensaje de bienvenida personalizado
MENSAJE_BIENVENIDA = f"""
🏪 *Bot de Inventario - {NOMBRE_TIENDA}*

¡Bienvenida Doña Rosa! 👋

Este bot te ayudará a:
• Gestionar tu inventario fácilmente
• Recibir alertas de stock bajo
• Calcular el valor total de tu inventario
• Mantener tus datos seguros

Selecciona una opción del menú para comenzar.
"""

# ====================================
# CONFIGURACIÓN DE LOGGING
# ====================================

# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = 'INFO'

# Archivo de log (None para no guardar en archivo)
LOG_FILE = 'bot.log'

# ====================================
# FUNCIONES AUXILIARES
# ====================================

def validar_configuracion():
    """
    Valida que la configuración esté correcta
    """
    errores = []
    
    if TELEGRAM_TOKEN == 'TU_TOKEN_AQUI':
        errores.append("⚠️ No has configurado el TOKEN del bot. Obtén uno en @BotFather")
    
    if not (0 < STOCK_MINIMO_PORCENTAJE < 1):
        errores.append("⚠️ El porcentaje de stock mínimo debe estar entre 0 y 1")
    
    return errores

def obtener_info_configuracion():
    """
    Retorna información sobre la configuración actual
    """
    return {
        'tienda': NOMBRE_TIENDA,
        'db_file': DB_FILE,
        'stock_minimo': f"{STOCK_MINIMO_PORCENTAJE * 100}%",
        'usuarios_autorizados': len(USUARIOS_AUTORIZADOS) if USUARIOS_AUTORIZADOS else "Todos",
        'log_level': LOG_LEVEL
    }

# ====================================
# VALIDACIÓN AL IMPORTAR
# ====================================

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar configuración
    print("=" * 50)
    print("CONFIGURACIÓN DEL BOT")
    print("=" * 50)
    
    errores = validar_configuracion()
    
    if errores:
        print("\n❌ ERRORES DE CONFIGURACIÓN:")
        for error in errores:
            print(f"  {error}")
    else:
        print("\n✅ Configuración válida")
    
    print("\n📋 INFORMACIÓN:")
    info = obtener_info_configuracion()
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
    
    print("\n" + "=" * 50)
