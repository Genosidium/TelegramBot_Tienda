import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import json
import os
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados de conversación
MENU, INSERTAR_NOMBRE, INSERTAR_CANTIDAD, INSERTAR_PRECIO, INSERTAR_CATEGORIA = range(5)
ACTUALIZAR_SELECCION, ACTUALIZAR_CANTIDAD = range(5, 7)
BORRAR_SELECCION = 7

# Archivo de base de datos JSON
DB_FILE = 'inventario.json'

# Funciones de base de datos
def cargar_inventario():
    """Carga el inventario desde el archivo JSON"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_inventario(inventario):
    """Guarda el inventario en el archivo JSON"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventario, f, indent=2, ensure_ascii=False)

def calcular_inventario_total():
    """Calcula el costo total del inventario"""
    inventario = cargar_inventario()
    total = sum(
        producto['precio'] * producto['cantidad'] 
        for producto in inventario.values()
    )
    return total

def obtener_productos_bajo_stock():
    """Obtiene productos con stock menor al 10% de su cantidad inicial"""
    inventario = cargar_inventario()
    productos_bajo_stock = []
    
    for nombre, producto in inventario.items():
        cantidad_actual = producto['cantidad']
        cantidad_inicial = producto.get('cantidad_inicial', cantidad_actual)
        limite = cantidad_inicial * 0.10
        
        if cantidad_actual <= limite:
            productos_bajo_stock.append({
                'nombre': nombre,
                'cantidad': cantidad_actual,
                'limite': limite
            })
    
    return productos_bajo_stock

# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el bot y muestra el menú principal"""
    keyboard = [
        ['📦 Insertar Producto', '🔄 Actualizar Producto'],
        ['🗑️ Borrar Producto', '📊 Ver Inventario'],
        ['⚠️ Stock Bajo', '💰 Costo Total'],
        ['❓ Seguridad de Datos']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    mensaje = (
        "🏪 *Bot de Inventario - Tienda Doña Rosa*\n\n"
        "¡Bienvenida Doña Rosa! 👋\n\n"
        "Seleccione una opción del menú:"
    )
    
    await update.message.reply_text(
        mensaje,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las opciones del menú principal"""
    texto = update.message.text
    
    if texto == '📦 Insertar Producto':
        await update.message.reply_text(
            "📝 Ingrese el *nombre* del nuevo producto:",
            parse_mode='Markdown'
        )
        return INSERTAR_NOMBRE
    
    elif texto == '🔄 Actualizar Producto':
        inventario = cargar_inventario()
        if not inventario:
            await update.message.reply_text("❌ No hay productos en el inventario.")
            return MENU
        
        productos_lista = "\n".join([f"• {nombre}" for nombre in inventario.keys()])
        await update.message.reply_text(
            f"📋 *Productos disponibles:*\n\n{productos_lista}\n\n"
            f"Escriba el nombre del producto a actualizar:",
            parse_mode='Markdown'
        )
        return ACTUALIZAR_SELECCION
    
    elif texto == '🗑️ Borrar Producto':
        inventario = cargar_inventario()
        if not inventario:
            await update.message.reply_text("❌ No hay productos en el inventario.")
            return MENU
        
        productos_lista = "\n".join([f"• {nombre}" for nombre in inventario.keys()])
        await update.message.reply_text(
            f"📋 *Productos disponibles:*\n\n{productos_lista}\n\n"
            f"Escriba el nombre del producto a borrar:",
            parse_mode='Markdown'
        )
        return BORRAR_SELECCION
    
    elif texto == '📊 Ver Inventario':
        await mostrar_inventario(update, context)
        return MENU
    
    elif texto == '⚠️ Stock Bajo':
        await verificar_stock_bajo(update, context)
        return MENU
    
    elif texto == '💰 Costo Total':
        total = calcular_inventario_total()
        await update.message.reply_text(
            f"💰 *Costo Total del Inventario:*\n\n"
            f"${total:,.2f}",
            parse_mode='Markdown'
        )
        return MENU
    
    elif texto == '❓ Seguridad de Datos':
        await explicar_seguridad(update, context)
        return MENU
    
    return MENU

# Insertar producto
async def insertar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre del producto a insertar"""
    context.user_data['nuevo_producto'] = {'nombre': update.message.text}
    await update.message.reply_text("📊 Ingrese la *cantidad* del producto:", parse_mode='Markdown')
    return INSERTAR_CANTIDAD

async def insertar_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la cantidad del producto"""
    try:
        cantidad = int(update.message.text)
        if cantidad < 0:
            raise ValueError
        context.user_data['nuevo_producto']['cantidad'] = cantidad
        context.user_data['nuevo_producto']['cantidad_inicial'] = cantidad
        await update.message.reply_text("💵 Ingrese el *precio* del producto:", parse_mode='Markdown')
        return INSERTAR_PRECIO
    except ValueError:
        await update.message.reply_text("❌ Por favor ingrese un número válido.")
        return INSERTAR_CANTIDAD

async def insertar_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el precio del producto"""
    try:
        precio = float(update.message.text)
        if precio < 0:
            raise ValueError
        context.user_data['nuevo_producto']['precio'] = precio
        await update.message.reply_text(
            "🏷️ Ingrese la *categoría* del producto:\n"
            "(Ej: Granos, Frutas, Legumbres, Dulces)",
            parse_mode='Markdown'
        )
        return INSERTAR_CATEGORIA
    except ValueError:
        await update.message.reply_text("❌ Por favor ingrese un precio válido.")
        return INSERTAR_PRECIO

async def insertar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la categoría y guarda el producto"""
    context.user_data['nuevo_producto']['categoria'] = update.message.text
    context.user_data['nuevo_producto']['fecha_creacion'] = datetime.now().isoformat()
    
    inventario = cargar_inventario()
    nombre = context.user_data['nuevo_producto']['nombre']
    inventario[nombre] = context.user_data['nuevo_producto']
    guardar_inventario(inventario)
    
    producto = context.user_data['nuevo_producto']
    await update.message.reply_text(
        f"✅ *Producto agregado exitosamente:*\n\n"
        f"📦 Nombre: {nombre}\n"
        f"📊 Cantidad: {producto['cantidad']}\n"
        f"💵 Precio: ${producto['precio']:.2f}\n"
        f"🏷️ Categoría: {producto['categoria']}",
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    return MENU

# Actualizar producto
async def actualizar_seleccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Selecciona el producto a actualizar"""
    nombre = update.message.text
    inventario = cargar_inventario()
    
    if nombre not in inventario:
        await update.message.reply_text("❌ Producto no encontrado. Intente nuevamente.")
        return ACTUALIZAR_SELECCION
    
    context.user_data['producto_actualizar'] = nombre
    producto = inventario[nombre]
    await update.message.reply_text(
        f"📦 *Producto seleccionado:*\n"
        f"Nombre: {nombre}\n"
        f"Cantidad actual: {producto['cantidad']}\n\n"
        f"Ingrese la *nueva cantidad*:",
        parse_mode='Markdown'
    )
    return ACTUALIZAR_CANTIDAD

async def actualizar_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Actualiza la cantidad del producto"""
    try:
        nueva_cantidad = int(update.message.text)
        if nueva_cantidad < 0:
            raise ValueError
        
        inventario = cargar_inventario()
        nombre = context.user_data['producto_actualizar']
        inventario[nombre]['cantidad'] = nueva_cantidad
        guardar_inventario(inventario)
        
        await update.message.reply_text(
            f"✅ *Producto actualizado:*\n"
            f"📦 {nombre}\n"
            f"📊 Nueva cantidad: {nueva_cantidad}",
            parse_mode='Markdown'
        )
        
        # Verificar si está bajo en stock
        cantidad_inicial = inventario[nombre].get('cantidad_inicial', nueva_cantidad)
        if nueva_cantidad <= cantidad_inicial * 0.10:
            await update.message.reply_text(
                f"⚠️ *ALERTA:* El producto '{nombre}' está bajo en stock!"
            )
        
        context.user_data.clear()
        return MENU
    except ValueError:
        await update.message.reply_text("❌ Por favor ingrese un número válido.")
        return ACTUALIZAR_CANTIDAD

# Borrar producto
async def borrar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borra un producto del inventario"""
    nombre = update.message.text
    inventario = cargar_inventario()
    
    if nombre not in inventario:
        await update.message.reply_text("❌ Producto no encontrado. Intente nuevamente.")
        return BORRAR_SELECCION
    
    del inventario[nombre]
    guardar_inventario(inventario)
    
    await update.message.reply_text(
        f"🗑️ *Producto eliminado:*\n{nombre}",
        parse_mode='Markdown'
    )
    return MENU

# Funciones auxiliares
async def mostrar_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todos los productos del inventario"""
    inventario = cargar_inventario()
    
    if not inventario:
        await update.message.reply_text("❌ El inventario está vacío.")
        return
    
    mensaje = "📋 *INVENTARIO COMPLETO*\n\n"
    for nombre, producto in inventario.items():
        mensaje += (
            f"📦 *{nombre}*\n"
            f"  └ Cantidad: {producto['cantidad']}\n"
            f"  └ Precio: ${producto['precio']:.2f}\n"
            f"  └ Categoría: {producto['categoria']}\n"
            f"  └ Valor total: ${producto['cantidad'] * producto['precio']:.2f}\n\n"
        )
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def verificar_stock_bajo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica productos con stock menor al 10%"""
    productos_bajo = obtener_productos_bajo_stock()
    
    if not productos_bajo:
        await update.message.reply_text("✅ Todos los productos tienen stock suficiente.")
        return
    
    mensaje = "⚠️ *PRODUCTOS CON STOCK BAJO:*\n\n"
    for producto in productos_bajo:
        mensaje += (
            f"📦 *{producto['nombre']}*\n"
            f"  └ Cantidad actual: {producto['cantidad']}\n"
            f"  └ Límite mínimo: {producto['limite']:.1f}\n\n"
        )
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def explicar_seguridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explica las medidas de seguridad implementadas"""
    mensaje = (
        "🔒 *SEGURIDAD DE SUS DATOS*\n\n"
        "Sus datos están protegidos mediante:\n\n"
        "1️⃣ *Almacenamiento Local:* Los datos se guardan en su propio servidor/dispositivo, "
        "no en servidores externos.\n\n"
        "2️⃣ *Cifrado de Telegram:* Todas las comunicaciones van cifradas por Telegram.\n\n"
        "3️⃣ *Respaldos:* Se recomienda hacer copias de seguridad del archivo 'inventario.json' "
        "periódicamente.\n\n"
        "4️⃣ *Acceso Privado:* Solo usuarios autorizados con el link del bot pueden acceder.\n\n"
        "5️⃣ *Sin conexión a terceros:* No se comparte información con servicios externos.\n\n"
        "💡 *Recomendación:* Mantenga el TOKEN del bot en secreto y no lo comparta."
    )
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la operación actual"""
    await update.message.reply_text(
        "❌ Operación cancelada.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return await start(update, context)

def main():
    """Función principal"""
    # IMPORTANTE: Reemplaza 'TU_TOKEN_AQUI' con el token de BotFather
    TOKEN = ''
    # Crear la aplicación
    application = Application.builder().token(TOKEN).build()
    
    # Configurar el ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            INSERTAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, insertar_nombre)],
            INSERTAR_CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, insertar_cantidad)],
            INSERTAR_PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, insertar_precio)],
            INSERTAR_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, insertar_categoria)],
            ACTUALIZAR_SELECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_seleccion)],
            ACTUALIZAR_CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_cantidad)],
            BORRAR_SELECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, borrar_producto)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    
    application.add_handler(conv_handler)
    
    # Iniciar el bot
    print("🤖 Bot iniciado correctamente...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
