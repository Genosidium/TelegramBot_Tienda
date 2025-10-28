import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    """Clase para manejar la base de datos del inventario de Doña Rosa"""
    
    def __init__(self, db_name: str = "inventario.db"):
        """
        Inicializa la conexión a la base de datos
        
        Args:
            db_name: Nombre del archivo de base de datos
        """
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Crea la tabla de productos si no existe"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                cantidad REAL NOT NULL,
                cantidad_inicial REAL NOT NULL,
                precio REAL NOT NULL,
                categoria TEXT,
                fecha_creacion TEXT NOT NULL,
                fecha_actualizacion TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insertar_producto(self, nombre: str, cantidad: float, precio: float, 
                         categoria: str = "General") -> Dict:
        """
        Inserta un nuevo producto en el inventario
        
        Args:
            nombre: Nombre del producto
            cantidad: Cantidad inicial del producto
            precio: Precio unitario del producto
            categoria: Categoría del producto (Granos, Frutas, Legumbres, Dulces, etc.)
        
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO productos (nombre, cantidad, cantidad_inicial, precio, 
                                     categoria, fecha_creacion, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, cantidad, cantidad, precio, categoria, fecha_actual, fecha_actual))
            
            conn.commit()
            producto_id = cursor.lastrowid
            conn.close()
            
            return {
                "success": True,
                "message": f"✅ Producto '{nombre}' agregado exitosamente",
                "producto_id": producto_id
            }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": f"❌ El producto '{nombre}' ya existe. Use actualizar para modificarlo."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error al insertar producto: {str(e)}"
            }
    
    def actualizar_producto(self, nombre: str, cantidad: float = None, 
                          precio: float = None) -> Dict:
        """
        Actualiza la cantidad o precio de un producto existente
        
        Args:
            nombre: Nombre del producto a actualizar
            cantidad: Nueva cantidad (si se proporciona)
            precio: Nuevo precio (si se proporciona)
        
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Verificar si el producto existe
            cursor.execute('SELECT * FROM productos WHERE nombre = ?', (nombre,))
            producto = cursor.fetchone()
            
            if not producto:
                conn.close()
                return {
                    "success": False,
                    "message": f"❌ El producto '{nombre}' no existe en el inventario"
                }
            
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Actualizar según los parámetros proporcionados
            if cantidad is not None and precio is not None:
                cursor.execute('''
                    UPDATE productos 
                    SET cantidad = ?, precio = ?, fecha_actualizacion = ?
                    WHERE nombre = ?
                ''', (cantidad, precio, fecha_actual, nombre))
                mensaje = f"✅ Producto '{nombre}' actualizado: Cantidad={cantidad}, Precio=${precio}"
            elif cantidad is not None:
                cursor.execute('''
                    UPDATE productos 
                    SET cantidad = ?, fecha_actualizacion = ?
                    WHERE nombre = ?
                ''', (cantidad, fecha_actual, nombre))
                mensaje = f"✅ Cantidad de '{nombre}' actualizada a {cantidad}"
            elif precio is not None:
                cursor.execute('''
                    UPDATE productos 
                    SET precio = ?, fecha_actualizacion = ?
                    WHERE nombre = ?
                ''', (precio, fecha_actual, nombre))
                mensaje = f"✅ Precio de '{nombre}' actualizado a ${precio}"
            else:
                conn.close()
                return {
                    "success": False,
                    "message": "❌ Debe proporcionar al menos cantidad o precio para actualizar"
                }
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": mensaje
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error al actualizar producto: {str(e)}"
            }
    
    def borrar_producto(self, nombre: str) -> Dict:
        """
        Elimina un producto del inventario
        
        Args:
            nombre: Nombre del producto a eliminar
        
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Verificar si existe
            cursor.execute('SELECT * FROM productos WHERE nombre = ?', (nombre,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"❌ El producto '{nombre}' no existe en el inventario"
                }
            
            cursor.execute('DELETE FROM productos WHERE nombre = ?', (nombre,))
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"✅ Producto '{nombre}' eliminado del inventario"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error al borrar producto: {str(e)}"
            }
    
    def obtener_productos_bajos(self) -> List[Dict]:
        """
        Obtiene productos con cantidad inferior al 10% de su cantidad inicial
        
        Returns:
            Lista de productos con bajo inventario
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nombre, cantidad, cantidad_inicial, precio, categoria
                FROM productos
                WHERE cantidad <= (cantidad_inicial * 0.1)
                ORDER BY (cantidad / cantidad_inicial) ASC
            ''')
            
            productos = cursor.fetchall()
            conn.close()
            
            resultado = []
            for p in productos:
                porcentaje = (p[1] / p[2] * 100) if p[2] > 0 else 0
                resultado.append({
                    "nombre": p[0],
                    "cantidad": p[1],
                    "cantidad_inicial": p[2],
                    "precio": p[3],
                    "categoria": p[4],
                    "porcentaje": round(porcentaje, 2)
                })
            
            return resultado
        except Exception as e:
            print(f"Error al obtener productos bajos: {e}")
            return []
    
    def calcular_costo_total(self) -> Dict:
        """
        Calcula el costo total del inventario
        
        Returns:
            Diccionario con el costo total y detalles
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nombre, cantidad, precio, (cantidad * precio) as subtotal
                FROM productos
                ORDER BY subtotal DESC
            ''')
            
            productos = cursor.fetchall()
            conn.close()
            
            total = sum(p[3] for p in productos)
            
            detalles = [
                {
                    "nombre": p[0],
                    "cantidad": p[1],
                    "precio": p[2],
                    "subtotal": p[3]
                }
                for p in productos
            ]
            
            return {
                "total": round(total, 2),
                "cantidad_productos": len(productos),
                "detalles": detalles
            }
        except Exception as e:
            print(f"Error al calcular costo total: {e}")
            return {"total": 0, "cantidad_productos": 0, "detalles": []}
    
    def listar_productos(self) -> List[Dict]:
        """
        Lista todos los productos en el inventario
        
        Returns:
            Lista de todos los productos
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nombre, cantidad, cantidad_inicial, precio, categoria
                FROM productos
                ORDER BY nombre
            ''')
            
            productos = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "nombre": p[0],
                    "cantidad": p[1],
                    "cantidad_inicial": p[2],
                    "precio": p[3],
                    "categoria": p[4]
                }
                for p in productos
            ]
        except Exception as e:
            print(f"Error al listar productos: {e}")
            return []
    
    def buscar_producto(self, nombre: str) -> Optional[Dict]:
        """
        Busca un producto específico por nombre
        
        Args:
            nombre: Nombre del producto a buscar
        
        Returns:
            Diccionario con la información del producto o None si no existe
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nombre, cantidad, cantidad_inicial, precio, categoria, 
                       fecha_creacion, fecha_actualizacion
                FROM productos
                WHERE nombre = ?
            ''', (nombre,))
            
            producto = cursor.fetchone()
            conn.close()
            
            if producto:
                return {
                    "nombre": producto[0],
                    "cantidad": producto[1],
                    "cantidad_inicial": producto[2],
                    "precio": producto[3],
                    "categoria": producto[4],
                    "fecha_creacion": producto[5],
                    "fecha_actualizacion": producto[6]
                }
            return None
        except Exception as e:
            print(f"Error al buscar producto: {e}")
            return None
    
    def exportar_a_json(self, archivo: str = "backup_inventario.json"):
        """
        Exporta todos los productos a un archivo JSON
        
        Args:
            archivo: Nombre del archivo JSON de destino
        """
        try:
            productos = self.listar_productos()
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(productos, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al exportar a JSON: {e}")
            return False
        