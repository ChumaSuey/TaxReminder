import os
import sys
import time
from datetime import date, timedelta

# Configurar título de la consola
if os.name == 'nt':  # Solo intentar en Windows
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("Recordatorio de Impuestos")
    except:
        pass

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Mostrar encabezado de la aplicación"""
    clear_screen()
    print("=" * 50)
    print("     📅 RECORDATORIO DE IMPUESTOS - PRÓXIMOS VENCIMIENTOS")
    print("=" * 50)
    print(f"Fecha de hoy: {date.today().strftime('%d/%m/%Y')}\n")

def check_upcoming_deadlines():
    """Check for tax deadlines due today or in the next 2 days"""
    import sys
    import os
    from models import DatabaseManager, TaxDate, TaxTable
    
    try:
        # Usar la ruta correcta para la base de datos
        if getattr(sys, 'frozen', False):
            # Si es un ejecutable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Si se ejecuta desde el código fuente
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Crear la ruta completa al archivo de la base de datos
        db_path = os.path.join(base_dir, 'tax_reminder.db')
        db_url = f'sqlite:///{db_path}'
        print(f"Conectando a la base de datos en: {db_url}")
        
        db = DatabaseManager(db_url)
        today = date.today()
        today_reminders = []
        upcoming_reminders = []
        has_errors = False

        # Check for today and next 2 days
        for days_ahead in range(0, 3):
            try:
                check_date = today + timedelta(days=days_ahead)
                with db.get_db() as session:
                    results = session.query(TaxDate, TaxTable.description).join(
                        TaxTable, TaxDate.table_name == TaxTable.name
                    ).filter(
                        TaxDate.month == check_date.month,
                        TaxDate.day == check_date.day
                    ).all()

                    for date_obj, table_desc in results:
                        # Calculate the correct year for the reminder
                        current_year = today.year
                        if date_obj.month < today.month or (date_obj.month == today.month and date_obj.day < today.day):
                            current_year += 1  # Next year if the date has passed this year
                        
                        reminder_date = date(current_year, date_obj.month, date_obj.day)
                        days_until = (reminder_date - today).days

                        reminder = {
                            'table': date_obj.table_name,
                            'table_description': table_desc,
                            'month': date_obj.month,
                            'day': date_obj.day,
                            'description': date_obj.description
                        }

                        if days_until == 0:
                            today_reminders.append(reminder)
                        elif days_until > 0:
                            reminder['days_until'] = days_until
                            upcoming_reminders.append(reminder)
            except Exception as e:
                print(f"⚠️  Error al verificar fechas: {str(e)}")
                has_errors = True
                continue

        # Display header
        print_header()
        
        # Display today's reminders
        if today_reminders:
            print("\n\033[93m\033[1m🔔 ¡VENCIMIENTOS PARA HOY!\033[0m\n")
            _print_reminders(today_reminders)
        
        # Display upcoming reminders (next 2 days)
        if upcoming_reminders:
            print("\n\033[94m\033[1m🔔 PRÓXIMOS VENCIMIENTOS\033[0m")
            for reminder in sorted(upcoming_reminders, key=lambda x: x['days_until']):
                days_text = "mañana" if reminder['days_until'] == 1 else f"en {reminder['days_until']} días"
                month_name = _get_month_name(reminder['month'])
                
                # Formatear los nombres de las quincenas
                table_desc = reminder['table_description']
                if 'First_Fortnight' in table_desc:
                    table_desc = table_desc.replace('First_Fortnight', 'Primera Quincena')
                elif 'Second_Fortnight' in table_desc:
                    table_desc = table_desc.replace('Second_Fortnight', 'Segunda Quincena')
                
                print(f"\n• {table_desc}")
                print(f"  📅 {reminder['day']} de {month_name} ({days_text})")
                if reminder.get('description'):
                    print(f"  📝 {reminder['description']}")
        
        if not today_reminders and not upcoming_reminders and not has_errors:
            print("\n✅ No hay vencimientos para hoy ni para los próximos 2 días.")
            
    except Exception as e:
        print(f"\n❌ Error al acceder a la base de datos: {str(e)}")
        print("Asegúrate de que el archivo 'tax_reminder.db' esté en el mismo directorio.")
        print("Si es la primera vez que usas la aplicación, crea primero los recordatorios\n"
              "usando el programa principal (main.py).")

def _get_month_name(month_number):
    """Get month name in Spanish"""
    months = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    return months[month_number - 1] if 1 <= month_number <= 12 else ""

def _print_reminders(reminders):
    """Helper function to print a list of reminders"""
    for reminder in reminders:
        # Formatear los nombres de las quincenas
        table_desc = reminder['table_description']
        if 'First_Fortnight' in table_desc:
            table_desc = table_desc.replace('First_Fortnight', 'Primera Quincena')
        elif 'Second_Fortnight' in table_desc:
            table_desc = table_desc.replace('Second_Fortnight', 'Segunda Quincena')
        
        month_name = _get_month_name(reminder['month'])
        print(f"\n• {table_desc}")
        print(f"  📅 {reminder['day']} de {month_name}")
        if reminder.get('description'):
            print(f"  📝 {reminder['description']}")

def main():
    """Main function"""
    check_upcoming_deadlines()
    
    # Pausa antes de salir
    print("\n" + "=" * 50)
    if os.name == 'nt':  # Solo pausar en Windows
        input("\nPresiona Enter para salir...")
    else:
        # En otros sistemas, esperar antes de salir
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSaliendo de la aplicación...")
        time.sleep(1)
    except Exception as e:
        print(f"\n\n❌ ¡Ups! Ocurrió un error inesperado: {str(e)}")
        if os.name == 'nt':
            input("Presiona Enter para salir...")