from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from models import DatabaseManager, TaxTable, TaxDate, Base
import sqlalchemy.orm
import sys

class TaxReminderCLI:
    """Command-line interface for the Tax Reminder application"""
    
    def __init__(self):
        self.db = DatabaseManager('sqlite:///tax_reminder.db')
        self.setup_default_tables()
    
    def setup_default_tables(self):
        """Inicializa las tablas por defecto si no existen"""
        default_tables = [
            ('first_fortnight', 'Impuestos del 1-15 del mes'),
            ('second_fortnight', 'Impuestos del 16 a fin de mes')
        ]
        
        for name, desc in default_tables:
            # This will only add the table if it doesn't already exist
            self.db.add_table(name, desc)
    
    def check_today(self):
        """Check for any tax dates due today or in the next 2 days"""
        today = date.today()
        today_reminders = []
        upcoming_reminders = []
        
        # Primero, obtener todos los vencimientos
        all_reminders = []
        with self.db.get_db() as db:
            results = db.query(TaxDate, TaxTable.description).join(
                TaxTable, TaxDate.table_name == TaxTable.name
            ).all()
            
            for date_obj, table_desc in results:
                all_reminders.append({
                    'table': date_obj.table_name,
                    'table_description': table_desc,
                    'month': date_obj.month,
                    'day': date_obj.day,
                    'description': date_obj.description
                })
        
        # Verificar para hoy y los próximos 2 días
        for days_ahead in range(0, 3):  # Hoy (0), mañana (1), pasado mañana (2)
            check_date = today + timedelta(days=days_ahead)
            
            for reminder in all_reminders:
                # Verificar si la fecha coincide con el día a verificar
                if reminder['month'] == check_date.month and reminder['day'] == check_date.day:
                    # Calcular días restantes
                    days_until = (check_date - today).days
                    
                    if days_until == 0:
                        today_reminders.append(reminder)
                    elif days_until > 0:  # Solo agregar fechas futuras
                        reminder_copy = reminder.copy()  # Crear una copia para no modificar el original
                        reminder_copy['days_until'] = days_until
                        upcoming_reminders.append(reminder_copy)
        
        # Display today's reminders
        if today_reminders:
            print("\n\033[93m\033[1m🔔 ¡RECORDATORIO DE IMPUESTOS!\033[0m\n")
            print("📅 Vencimientos para hoy:")
            self._print_reminders(today_reminders)
        
        # Display upcoming reminders (next 2 days)
        if upcoming_reminders:
            print("\n\033[94m\033[1m🔔 PRÓXIMOS VENCIMIENTOS\033[0m")
            month_names = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            
            for reminder in sorted(upcoming_reminders, key=lambda x: x['days_until']):
                days_text = "mañana" if reminder['days_until'] == 1 else f"en {reminder['days_until']} días"
                
                # Formatear los nombres de las quincenas
                table_desc = reminder['table_description']
                if 'First_Fortnight' in table_desc:
                    table_desc = table_desc.replace('First_Fortnight', 'Primera Quincena')
                elif 'Second_Fortnight' in table_desc:
                    table_desc = table_desc.replace('Second_Fortnight', 'Segunda Quincena')
                
                # Obtener el nombre del mes en español
                month_name = month_names[reminder['month'] - 1]
                
                print(f"\n• {table_desc}")
                print(f"  📅 {reminder['day']} de {month_name} ({days_text})")
                if reminder.get('description'):
                    print(f"  📝 {reminder['description']}")
        
        if not today_reminders and not upcoming_reminders:
            print("\n✅ No hay vencimientos de impuestos para hoy ni para los próximos 2 días.")
    
    def _print_reminders(self, reminders):
        """Helper method to print a list of reminders"""
        month_names = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        
        for reminder in reminders:
            # Formatear los nombres de las quincenas
            table_desc = reminder['table_description']
            if 'First_Fortnight' in table_desc:
                table_desc = table_desc.replace('First_Fortnight', 'Primera Quincena')
            elif 'Second_Fortnight' in table_desc:
                table_desc = table_desc.replace('Second_Fortnight', 'Segunda Quincena')
            
            # Obtener el nombre del mes en español
            month_name = month_names[reminder['month'] - 1]
            
            # Mostrar la información del recordatorio
            print(f"\n• {table_desc}")
            print(f"  📅 {reminder['day']} de {month_name}")
            if reminder.get('description'):
                print(f"  📝 {reminder['description']}")
    
    def _get_valid_input(self, prompt, input_type=int, valid_range=None, allow_cancel=True):
        """Ayuda para obtener y validar la entrada del usuario con opción de cancelar"""
        while True:
            user_input = input(prompt).strip()
            
            # Allow cancellation
            if allow_cancel and user_input.lower() == 'q':
                return None
                
            try:
                # Convert to desired type
                value = input_type(user_input)
                
                # Validar rango si se proporciona
                if valid_range and (value < valid_range[0] or value > valid_range[1]):
                    print(f"❌ Error: El valor debe estar entre {valid_range[0]} y {valid_range[1]}")
                    continue
                    
                return value
                
            except ValueError:
                type_names = {
                    'int': 'número entero',
                    'float': 'número decimal',
                    'str': 'texto'
                }
                type_name = type_names.get(input_type.__name__, 'valor')
                print(f"❌ Error: Por favor ingresa un {type_name} válido")
                
    def _date_exists(self, table_name, month, day):
        """Verifica si una fecha ya existe en la tabla especificada"""
        with self.db.get_db() as db:
            return bool(db.query(TaxDate).filter_by(
                table_name=table_name,
                month=month,
                day=day
            ).first())
    
    def add_date(self):
        """Agrega una nueva fecha de vencimiento de impuestos"""
        try:
            print("\n📅 Agregar Nueva Fecha de Vencimiento")
            print("-----------------------------------")
            print("  (presiona 'q' en cualquier momento para cancelar)\n")
            
            # Show available tables
            with self.db.get_db() as db:
                tables = db.query(TaxTable).all()
                if not tables:
                    print("❌ No se encontraron tablas. Primero crea una tabla.")
                    return
                    
                print("Tablas disponibles:")
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table.description}")
                
                # Obtener selección de tabla
                table_choice = self._get_valid_input(
                    "\nSelecciona una tabla (número): ",
                    int,
                    (1, len(tables))
                )
                if table_choice is None:
                    print("\nOperación cancelada.")
                    return
                    
                selected_table = tables[table_choice - 1]
                
                # Obtener mes
                month = self._get_valid_input(
                    "\nIngresa el mes (1-12): ",
                    int,
                    (1, 12)
                )
                if month is None:
                    print("\nOperación cancelada.")
                    return
                
                # Obtener día
                day = self._get_valid_input(
                    "Ingresa el día (1-31): ",
                    int,
                    (1, 31)
                )
                if day is None:
                    print("\nOperación cancelada.")
                    return
                
                # Validate the specific date (e.g., Feb 30)
                try:
                    date(2023, month, day)  # Using a non-leap year for simplicity
                except ValueError as e:
                    print(f"\n❌ Error: {str(e).capitalize()}")
                    return
                
                # Check if date already exists in this table
                if self._date_exists(selected_table.name, month, day):
                    print("\n❌ This date already exists in the selected table.")
                    return
                
                # Obtener descripción con opción de cancelar
                description = input("\nIngresa una descripción (opcional, presiona Enter para omitir): ").strip()
                if description.lower() == 'q':
                    print("\nOperación cancelada.")
                    return
                    
                description = description or None
                
                # Intentar agregar la fecha
                if self.db.add_date(selected_table.name, month, day, description):
                    print("\n✅ ¡Fecha agregada correctamente!")
                else:
                    print("\n❌ Error al agregar la fecha. Es posible que ya exista.")
                    
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado: {e}")
                
    def view_dates(self):
        """Ver todas las fechas de vencimiento en una tabla"""
        with self.db.get_db() as db:
            tables = db.query(TaxTable).all()
            if not tables:
                print("No se encontraron tablas.")
                return
                
            print("\nTablas disponibles:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table.description or 'Sin descripción'}")
            
            try:
                table_choice = int(input("\nSelecciona el número de la tabla: ")) - 1
                if not 0 <= table_choice < len(tables):
                    print("❌ Selección de tabla inválida.")
                    return
                    
                table = tables[table_choice]
                dates = db.query(TaxDate).filter(
                    TaxDate.table_name == table.name
                ).order_by(
                    TaxDate.month, TaxDate.day
                ).all()
                
                print(f"\n📅 {table.description or 'Sin descripción'}")
                print("-" * 50)
                
                if not dates:
                    print("No se encontraron fechas en esta tabla.")
                    return
                    
                current_month = None
                for date_obj in dates:
                    if date_obj.month != current_month:
                        current_month = date_obj.month
                        month_name = date(2023, current_month, 1).strftime('%B')
                        print(f"\n{month_name}:")
                        print("-" * 20)
                    
                    day_str = f"{date_obj.day}"
                    if date_obj.description:
                        print(f"  {day_str:>2} - {date_obj.description}")
                    else:
                        print(f"  {day_str:>2}")
                        
            except ValueError:
                print("Invalid input.")
    
    def update_descriptions(self):
        """Actualiza las descripciones de las tablas a los nuevos valores"""
        with self.db.get_db() as db:
            # Actualizar first_fortnight
            first = db.query(TaxTable).filter_by(name='first_fortnight').first()
            if first:
                first.description = 'Impuestos del 1-15 del mes'
                print("✓ Actualizada descripción de la primera quincena")
        
            # Actualizar second_fortnight
            second = db.query(TaxTable).filter_by(name='second_fortnight').first()
            if second:
                second.description = 'Impuestos del 16 a fin de mes'
                print("✓ Actualizada descripción de la segunda quincena")
            
            db.commit()
            print("¡Actualización de descripciones completada!")
    
    def clean_database(self):
        """Elimina todos los datos de la base de datos y la reinicia a los valores predeterminados"""
        confirm = input("\n⚠️  ADVERTENCIA: Esto eliminará TODAS las fechas y tablas de impuestos. ¿Continuar? (s/N): ").strip().lower()
        if confirm == 's':
            if self.db.clean_database():
                print("✅ La base de datos ha sido restablecida al estado predeterminado.")
            else:
                print("❌ Error al limpiar la base de datos.")
        else:
            print("Operación cancelada.")
            
    def edit_or_delete_date(self):
        """Permite editar o eliminar una fecha de vencimiento existente"""
        try:
            print("\n📝 Editar o Eliminar Fecha de Vencimiento")
            print("-----------------------------------")
            print("  (presiona 'q' en cualquier momento para cancelar)\n")
            
            # Obtener todas las fechas agrupadas por tabla
            with self.db.get_db() as db:
                # Obtener todas las tablas con sus fechas
                tables = db.query(TaxTable).options(
                    sqlalchemy.orm.joinedload(TaxTable.dates)
                ).order_by(TaxTable.name).all()
                
                if not tables:
                    print("❌ No hay tablas de impuestos disponibles.")
                    return
                
                # Mostrar menú de tablas
                print("\nTablas disponibles:")
                for i, table in enumerate(tables, 1):
                    print(f"{i}. {table.description or 'Sin descripción'} ({table.name})")
                
                # Seleccionar tabla
                table_choice = self._get_valid_input(
                    "\nSelecciona el número de la tabla: ",
                    int,
                    (1, len(tables)),
                    allow_cancel=True
                )
                if table_choice is None:
                    print("\nOperación cancelada.")
                    return
                
                selected_table = tables[table_choice - 1]
                
                if not selected_table.dates:
                    print(f"\n❌ No hay fechas en la tabla {selected_table.description or selected_table.name}.")
                    return
                
                # Mostrar fechas de la tabla seleccionada
                print(f"\n📅 Fechas en {selected_table.description or selected_table.name}:")
                for i, date_obj in enumerate(sorted(selected_table.dates, key=lambda d: (d.month, d.day)), 1):
                    month_name = date(2023, date_obj.month, 1).strftime('%B')
                    desc = f" - {date_obj.description}" if date_obj.description else ""
                    print(f"{i}. {date_obj.day:02d} de {month_name}{desc}")
                
                # Seleccionar fecha a editar/eliminar
                date_choice = self._get_valid_input(
                    "\nSelecciona el número de la fecha a editar/eliminar: ",
                    int,
                    (1, len(selected_table.dates)),
                    allow_cancel=True
                )
                if date_choice is None:
                    print("\nOperación cancelada.")
                    return
                
                selected_date = sorted(selected_table.dates, key=lambda d: (d.month, d.day))[date_choice - 1]
                
                # Menú de acciones
                print("\n¿Qué acción deseas realizar?")
                print("1. Editar fecha")
                print("2. Eliminar fecha")
                print("3. Cancelar")
                
                action = self._get_valid_input(
                    "\nSelecciona una opción (1-3): ",
                    int,
                    (1, 3)
                )
                
                if action == 1:  # Editar
                    print(f"\nEditando fecha: {selected_date.day:02d}/{selected_date.month:02d}")
                    
                    # Obtener nuevo día
                    new_day = self._get_valid_input(
                        f"Nuevo día (actual: {selected_date.day}): ",
                        int,
                        (1, 31),
                        allow_cancel=True
                    )
                    if new_day is None:
                        print("\nOperación cancelada.")
                        return
                    
                    # Obtener nuevo mes
                    new_month = self._get_valid_input(
                        f"Nuevo mes (1-12) (actual: {selected_date.month}): ",
                        int,
                        (1, 12),
                        allow_cancel=True
                    )
                    if new_month is None:
                        print("\nOperación cancelada.")
                        return
                    
                    # Validar la fecha
                    try:
                        date(2023, new_month, new_day)  # Usamos un año no bisiesto para validar
                    except ValueError as e:
                        print(f"\n❌ Fecha inválida: {e}")
                        return
                    
                    # Verificar si la nueva fecha ya existe
                    if (new_day != selected_date.day or new_month != selected_date.month) and \
                       self._date_exists(selected_table.name, new_month, new_day):
                        print("\n❌ Ya existe una fecha con ese día y mes en esta tabla.")
                        return
                    
                    # Obtener nueva descripción
                    new_desc = input(
                        f"Nueva descripción (actual: {selected_date.description or 'ninguna'}, presiona Enter para mantener): "
                    ).strip()
                    
                    # Actualizar la fecha
                    selected_date.day = new_day
                    selected_date.month = new_month
                    if new_desc:  # Solo actualizar si se ingresó algo
                        selected_date.description = new_desc if new_desc else None
                    
                    db.commit()
                    print("\n✅ Fecha actualizada correctamente.")
                    
                elif action == 2:  # Eliminar
                    confirm = input("\n⚠️  ¿Estás seguro de que deseas eliminar esta fecha? (s/N): ").strip().lower()
                    if confirm == 's':
                        db.delete(selected_date)
                        db.commit()
                        print("\n✅ Fecha eliminada correctamente.")
                    else:
                        print("\nOperación cancelada.")
                
                else:  # Cancelar
                    print("\nOperación cancelada.")
        
        except Exception as e:
            print(f"\n❌ Ocurrió un error: {e}")
            if 'db' in locals():
                db.rollback()
    
    def show_menu(self):
        """Muestra el menú principal"""
        while True:
            try:
                print("\n\033[1m📅 Recordatorio de Impuestos\033[0m")
                print("1. Ver vencimientos de hoy")
                print("2. Agregar nueva fecha de vencimiento")
                print("3. Listar todas las fechas de vencimiento")
                print("4. Editar o eliminar fechas")
                print("5. Confirmar pago del impuesto")
                print("6. Limpiar base de datos")
                print("7. Salir")
                
                choice = input("\nSeleccione una opción: ").strip()
                
                if choice == '1':
                    self.check_today()
                elif choice == '2':
                    self.add_date()
                elif choice == '3':
                    self.view_dates()
                elif choice == '4':
                    self.edit_or_delete_date()
                elif choice == '5':
                    self.confirm_payment()
                elif choice == '6':
                    self.clean_database()
                elif choice == '7':
                    print("\n¡Hasta luego! 👋")
                    sys.exit(0)
                else:
                    print("\n❌ Opción no válida. Por favor, intente de nuevo.")
            
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Ocurrió un error: {e}")
    
    def confirm_payment(self):
        """Confirma el pago del impuesto más cercano y lo elimina de la base de datos"""
        try:
            today = date.today()
            next_deadline = None
            
            with self.db.get_db() as db:
                # Obtener todas las fechas ordenadas por proximidad
                all_dates = db.query(TaxDate, TaxTable.description).join(
                    TaxTable, TaxDate.table_name == TaxTable.name
                ).order_by(TaxDate.month, TaxDate.day).all()
                
                if not all_dates:
                    print("\nℹ️ No hay impuestos registrados.")
                    return
                
                # Encontrar la próxima fecha de vencimiento (puede ser hoy o en el futuro)
                for date_obj, table_desc in all_dates:
                    # Crear fecha de vencimiento para el año actual
                    deadline = date(today.year, date_obj.month, date_obj.day)
                    
                    # Si ya pasó este año, considerar el próximo año
                    if deadline < today:
                        deadline = date(today.year + 1, date_obj.month, date_obj.day)
                    
                    if next_deadline is None or deadline < next_deadline['deadline']:
                        next_deadline = {
                            'date_obj': date_obj,
                            'table_desc': table_desc,
                            'deadline': deadline
                        }
                
                if next_deadline is None:
                    print("\nℹ️ No se encontraron vencimientos futuros.")
                    return
                
                # Mostrar información del próximo vencimiento
                date_obj = next_deadline['date_obj']
                month_name = date(2023, date_obj.month, 1).strftime('%B')
                days_until = (next_deadline['deadline'] - today).days
                
                print("\n\033[93m\033[1m📅 PRÓXIMO VENCIMIENTO\033[0m")
                print(f"\n• {next_deadline['table_desc']}")
                print(f"  📅 {date_obj.day:02d} de {month_name}")
                if date_obj.description:
                    print(f"  📝 {date_obj.description}")
                
                if days_until > 0:
                    print(f"\nℹ️ Este vencimiento es en {days_until} días.")
                elif days_until == 0:
                    print("\nℹ️ Este vencimiento es hoy.")
                else:
                    print(f"\n⚠️  Este vencimiento era hace {-days_until} días.")
                
                # Pedir confirmación
                confirm = input("\n¿Confirmar pago de este impuesto? (s/N): ").strip().lower()
                
                if confirm == 's':
                    # Eliminar el registro
                    db.delete(date_obj)
                    db.commit()
                    print("\n✅ ¡Pago confirmado! El impuesto ha sido registrado como pagado.")
                else:
                    print("\nOperación cancelada.")
                    
        except Exception as e:
            print(f"\n❌ Ocurrió un error al procesar el pago: {e}")
            if 'db' in locals():
                db.rollback()

def main():
    """Punto de entrada principal de la aplicación"""
    print("\n\033[1m💼 SISTEMA DE RECORDATORIO DE IMPUESTOS\033[0m")
    print("-----------------------------------")
    print("  Sistema de gestión de vencimientos fiscales\n")
    
    app = TaxReminderCLI()
    app.show_menu()

if __name__ == "__main__":
    main()