# debug_vencimientos.py
import sqlite3
from datetime import date

def verificar_base_datos():
    print("=== VERIFICACIÓN DE BASE DE DATOS ===")
    print(f"Fecha actual: {date.today().strftime('%d/%m/%Y')}\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('../tax_reminder.db')
    cursor = conn.cursor()
    
    # Ver tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    print("Tablas en la base de datos:")
    for tabla in tablas:
        print(f" - {tabla[0]}")
    
    # Ver contenido de las tablas
    print("\n=== CONTENIDO DE TABLAS ===")
    for tabla in tablas:
        print(f"\nContenido de '{tabla[0]}':")
        try:
            cursor.execute(f"SELECT * FROM {tabla[0]}")
            columnas = [desc[0] for desc in cursor.description]
            print("  Columnas:", ", ".join(columnas))
            
            filas = cursor.fetchall()
            for fila in filas:
                print(f"  - {fila}")
        except sqlite3.Error as e:
            print(f"  Error al leer la tabla: {e}")
    
    # Verificar específicamente fechas de hoy (26 de septiembre)
    print("\n=== VENCIMIENTOS PARA HOY (26/09) ===")
    try:
        cursor.execute("""
            SELECT d.*, t.description as tabla_desc 
            FROM tax_dates d 
            JOIN tables t ON d.table_name = t.name 
            WHERE d.month = 9 AND d.day = 26
        """)
        vencimientos = cursor.fetchall()
        
        if vencimientos:
            print("Se encontraron los siguientes vencimientos para hoy:")
            for v in vencimientos:
                print(f"- {v}")
        else:
            print("No se encontraron vencimientos para hoy.")
            
            # Verificar si hay algún problema con los nombres de las tablas
            print("\nVerificando nombres de tablas...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            print("Tablas existentes:", [t[0] for t in cursor.fetchall()])
            
    except sqlite3.Error as e:
        print(f"Error al consultar vencimientos: {e}")
    
    conn.close()

if __name__ == "__main__":
    verificar_base_datos()
