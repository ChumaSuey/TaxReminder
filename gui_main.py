import os
import sys
import json

# FIX: Force Tcl/Tk paths for Windows Virtual Environments
if sys.platform == 'win32':
    PYTHON_INSTALL_DIR = r'C:\Users\luism\AppData\Local\Programs\Python\Python313'
    tcl_path = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
    tk_path = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ['TCL_LIBRARY'] = tcl_path
        os.environ['TK_LIBRARY'] = tk_path

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from typing import List, Dict, Any

# Add project root to path
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from models import DatabaseManager, TaxDate, TaxTable

class TaxReminderMainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Recordatorio de Impuestos - Sistema Completo")
        self.root.geometry("800x600")
        
        self.db_path = os.path.join(base_dir, 'tax_reminder.db')
        self.db_url = f'sqlite:///{self.db_path}'
        self.db_manager = DatabaseManager(self.db_url)
        
        self.setup_styles()
        self.create_widgets()
        
        self.ack_file = os.path.join(base_dir, 'acknowledgements.json')
        
    def _load_acks(self) -> Dict[str, Any]:
        if os.path.exists(self.ack_file):
            try:
                with open(self.ack_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_acks(self, data: Dict[str, Any]):
        try:
            with open(self.ack_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar pago: {e}")

    def _get_ack_key(self, table_name: str, month: int, day: int) -> str:
        # Match Telegram Bot format: YYYY_TableName_M_D
        # Note: We need the year of the tax date, not necessarily current year.
        # But for "upcoming" logic usually it's current or next year.
        # Ideally we pass the full date object or calculated year.
        # For now let's assume standard calculation logic inside the loop matches this.
        today = date.today()
        current_year = today.year
        if month < today.month or (month == today.month and day < today.day):
            current_year += 1
        return f"{current_year}_{table_name}_{month}_{day}"
        
    def setup_styles(self):
        """Configure dark mode styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'card_bg': '#2d2d2d',
            'accent_gold': '#ffd700',
            'accent_blue': '#4a90e2',
            'success': '#4caf50',
            'danger': '#f44336',
            'text_secondary': '#b0b0b0',
            'header_bg': '#333333'
        }
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Frames
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat')
        
        # Notebook (Tabs)
        self.style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        self.style.configure('TNotebook.Tab', 
                           padding=[10, 5], 
                           background=self.colors['header_bg'],
                           foreground=self.colors['text_secondary'])
        self.style.map('TNotebook.Tab',
                     background=[('selected', self.colors['accent_blue'])],
                     foreground=[('selected', self.colors['fg'])])
        
        # Labels
        self.style.configure('TLabel', 
                           background=self.colors['bg'], 
                           foreground=self.colors['fg'],
                           font=('Segoe UI', 10))
        self.style.configure('Header.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['fg'],
                           font=('Segoe UI', 16, 'bold'))
        self.style.configure('SubHeaderToday.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['accent_gold'],
                           font=('Segoe UI', 12, 'bold'))
        self.style.configure('SubHeaderUpcoming.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['accent_blue'],
                           font=('Segoe UI', 12, 'bold'))
        self.style.configure('CardText.TLabel',
                           background=self.colors['card_bg'],
                           foreground=self.colors['fg'],
                           font=('Segoe UI', 10))
        self.style.configure('CardDesc.TLabel',
                           background=self.colors['card_bg'],
                           foreground=self.colors['text_secondary'],
                           font=('Segoe UI', 9, 'italic'))

        # Buttons
        self.style.configure('TButton',
                           padding=[10, 5],
                           background=self.colors['card_bg'],
                           foreground=self.colors['fg'])
        self.style.map('TButton',
                      background=[('active', self.colors['accent_blue'])],
                      foreground=[('active', self.colors['fg'])])
                      
        self.style.configure('Danger.TButton',
                           background=self.colors['danger'],
                           foreground='white')
        self.style.map('Danger.TButton',
                      background=[('active', '#d32f2f')])
                      
        # Treeview
        self.style.configure("Treeview", 
                           background=self.colors['card_bg'],
                           foreground=self.colors['fg'],
                           fieldbackground=self.colors['card_bg'],
                           font=('Segoe UI', 10))
        self.style.configure("Treeview.Heading", 
                           background=self.colors['header_bg'],
                           foreground=self.colors['fg'],
                           font=('Segoe UI', 10, 'bold'))
        self.style.map("Treeview", 
                     background=[('selected', self.colors['accent_blue'])])

    def create_widgets(self):
        # Setup Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text='🏠 Inicio')
        self.setup_dashboard_tab()
        
        # Tab 2: Manage Dates
        self.tab_manage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manage, text='📅 Gestionar Fechas')
        self.setup_manage_tab()
        
        # Tab 3: Tools
        self.tab_tools = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tools, text='🛠 Herramientas')
        self.setup_tools_tab()
        
        # Refresh data on tab change
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        if tab_text == '🏠 Inicio':
            self.refresh_dashboard()
        elif tab_text == '📅 Gestionar Fechas':
            self.refresh_manage_list()

    # ================= DASHBOARD TAB =================
    
    def setup_dashboard_tab(self):
        container = ttk.Frame(self.tab_dashboard, padding="20")
        container.pack(fill='both', expand=True)
        
        # Header
        ttk.Label(container, text="Resumen de Vencimientos", style='Header.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Content Area
        self.dashboard_content = ttk.Frame(container)
        self.dashboard_content.pack(fill='both', expand=True)
        
        self.refresh_dashboard()

    def refresh_dashboard(self):
        # Clear current content
        for widget in self.dashboard_content.winfo_children():
            widget.destroy()
            
        try:
            today = date.today()
            today_reminders = []
            upcoming_reminders = []

            # Load acknowledgements
            acks = self._load_acks()

            # Logic same as gui_short.py / mainshort.py
            for days_ahead in range(0, 3):
                check_date = today + timedelta(days=days_ahead)
                with self.db_manager.get_db() as session:
                    results = session.query(TaxDate, TaxTable.description).join(
                        TaxTable, TaxDate.table_name == TaxTable.name
                    ).filter(
                        TaxDate.month == check_date.month,
                        TaxDate.day == check_date.day
                    ).all()

                    for date_obj, table_desc in results:
                        current_year = today.year
                        if date_obj.month < today.month or (date_obj.month == today.month and date_obj.day < today.day):
                            current_year += 1
                        
                        reminder_date = date(current_year, date_obj.month, date_obj.day)
                        days_until = (reminder_date - today).days

                        # Check if paid
                        ack_key = self._get_ack_key(date_obj.table_name, date_obj.month, date_obj.day)
                        if ack_key in acks:
                            continue # Skip paid taxes

                        reminder = {
                            'table_description': table_desc,
                            'month': date_obj.month,
                            'day': date_obj.day,
                            'description': date_obj.description,
                            'days_until': days_until,
                            'ack_key': ack_key # Pass key for button
                        }

                        if days_until == 0:
                            today_reminders.append(reminder)
                        elif days_until > 0:
                            upcoming_reminders.append(reminder)

            if not today_reminders and not upcoming_reminders:
                ttk.Label(self.dashboard_content, 
                        text="✅ No hay vencimientos pendientes para los próximos días.",
                        style='TLabel').pack(pady=20)
                return

            if today_reminders:
                ttk.Label(self.dashboard_content, text="🔔 HOY", style='SubHeaderToday.TLabel').pack(anchor='w', pady=(0, 10))
                for reminder in today_reminders:
                    self.create_dashboard_card(reminder, is_today=True)
                ttk.Separator(self.dashboard_content, orient='horizontal').pack(fill='x', pady=15)

            if upcoming_reminders:
                ttk.Label(self.dashboard_content, text="🔔 PRÓXIMOS", style='SubHeaderUpcoming.TLabel').pack(anchor='w', pady=(0, 10))
                for reminder in sorted(upcoming_reminders, key=lambda x: x['days_until']):
                    self.create_dashboard_card(reminder, is_today=False)

        except Exception as e:
            ttk.Label(self.dashboard_content, text=f"Error al cargar datos: {e}", foreground='red').pack()

    def _format_table_name(self, name):
        if 'First_Fortnight' in name:
            return name.replace('First_Fortnight', 'Primera Quincena')
        elif 'Second_Fortnight' in name:
            return name.replace('Second_Fortnight', 'Segunda Quincena')
        return name
        
    def _get_month_name(self, month_number):
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return months[month_number - 1] if 1 <= month_number <= 12 else ""

    def create_dashboard_card(self, reminder, is_today):
        card = ttk.Frame(self.dashboard_content, style='Card.TFrame', padding="10")
        card.pack(fill='x', pady=(0, 10))
        
        desc = self._format_table_name(reminder['table_description'])
        ttk.Label(card, text=f"• {desc}", style='CardText.TLabel', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        month_name = self._get_month_name(reminder['month'])
        days_text = ""
        if not is_today:
             days_text = f" (mañana)" if reminder['days_until'] == 1 else f" (en {reminder['days_until']} días)"
        
        ttk.Label(card, text=f"📅 {reminder['day']} de {month_name}{days_text}", style='CardText.TLabel').pack(anchor='w')
        if reminder.get('description'):
            ttk.Label(card, text=f"📝 {reminder['description']}", style='CardDesc.TLabel').pack(anchor='w', pady=(5, 0))

        # Pay Button
        def pay_action():
            if messagebox.askyesno("Confirmar Pago", f"¿Marcar '{desc}' como PAGADO?"):
                acks = self._load_acks()
                acks[reminder['ack_key']] = date.today().isoformat()
                self._save_acks(acks)
                self.refresh_dashboard() # Reload to hide
                messagebox.showinfo("Hecho", "Impuesto marcado como pagado.")

        ttk.Button(card, text="✅ Registrar Pago", command=pay_action).pack(anchor='e', pady=(10, 0))

    # ================= MANAGE TAB =================

    def setup_manage_tab(self):
        container = ttk.Frame(self.tab_manage, padding="20")
        container.pack(fill='both', expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(container)
        toolbar.pack(fill='x', pady=(0, 15))
        
        ttk.Button(toolbar, text="➕ Agregar Nuevo", command=self.add_date_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Editar", command=self.edit_date_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🗑 Eliminar", command=self.delete_date_dialog, style='Danger.TButton').pack(side='left')
        
        # Treeview Scrollbar
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill='both', expand=True)
        
        sb = ttk.Scrollbar(tree_frame)
        sb.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(tree_frame, 
                               columns=('id', 'table', 'date', 'desc'), 
                               show='headings',
                               yscrollcommand=sb.set,
                               selectmode='browse')
        
        self.tree.heading('id', text='ID') # Hidden column
        self.tree.heading('table', text='Tabla/Categoría')
        self.tree.heading('date', text='Fecha')
        self.tree.heading('desc', text='Descripción')
        
        self.tree.column('id', width=0, stretch=False) # Hide ID
        self.tree.column('table', width=200)
        self.tree.column('date', width=150)
        self.tree.column('desc', width=300)
        
        self.tree.pack(side='left', fill='both', expand=True)
        sb.config(command=self.tree.yview)

    def refresh_manage_list(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            with self.db_manager.get_db() as session:
                results = session.query(TaxDate, TaxTable.description).join(
                    TaxTable, TaxDate.table_name == TaxTable.name
                ).order_by(TaxDate.table_name, TaxDate.month, TaxDate.day).all()
                
                for date_obj, table_desc in results:
                    month_name = self._get_month_name(date_obj.month)
                    date_str = f"{date_obj.day} de {month_name}"
                    table_str = self._format_table_name(table_desc)
                    
                    self.tree.insert('', 'end', values=(
                        date_obj.id,
                        table_str,
                        date_str,
                        date_obj.description or ""
                    ))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar lista: {e}")

    def add_date_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Fecha")
        dialog.geometry("400x450")
        dialog.configure(bg=self.colors['bg'])
        
        self.create_date_form(dialog)

    def edit_date_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor selecciona un elemento para editar.")
            return
            
        item = self.tree.item(selection[0])
        date_id = item['values'][0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Fecha")
        dialog.geometry("400x450")
        dialog.configure(bg=self.colors['bg'])
        
        # Pre-load Data
        with self.db_manager.get_db() as session:
            date_obj = session.query(TaxDate).filter(TaxDate.id == date_id).first()
            if date_obj:
                self.create_date_form(dialog, date_obj)
            else:
                messagebox.showerror("Error", "No se encontró el registro.")
                dialog.destroy()

    def create_date_form(self, window, existing_date=None):
        # We need data for combo boxes
        with self.db_manager.get_db() as session:
            tables = session.query(TaxTable).all()
            table_options = {t.description: t.name for t in tables}
            table_names_display = list(table_options.keys())
        
        # Variables
        table_var = tk.StringVar(value=table_names_display[0] if table_names_display else "")
        month_var = tk.IntVar(value=1)
        day_var = tk.IntVar(value=1)
        desc_var = tk.StringVar()
        
        # Pre-fill if editing
        if existing_date:
            # Find display name for table name
            for desc, name in table_options.items():
                if name == existing_date.table_name:
                    table_var.set(desc)
                    break
            month_var.set(existing_date.month)
            day_var.set(existing_date.day)
            desc_var.set(existing_date.description or "")
        
        # Form Layout
        form = ttk.Frame(window, padding="20")
        form.pack(fill='both', expand=True)

        ttk.Label(form, text="Tabla / Categoría:", style='TLabel').pack(anchor='w', pady=(0, 5))
        table_cb = ttk.Combobox(form, textvariable=table_var, values=table_names_display, state="readonly")
        table_cb.pack(fill='x', pady=(0, 15))
        
        ttk.Label(form, text="Mes:", style='TLabel').pack(anchor='w', pady=(0, 5))
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        month_cb = ttk.Combobox(form, values=months, state="readonly")
        month_cb.pack(fill='x', pady=(0, 15))
        # Set month combobox index based on int value
        month_cb.current(month_var.get() - 1)
        
        ttk.Label(form, text="Día (1-31):", style='TLabel').pack(anchor='w', pady=(0, 5))
        day_spin = ttk.Spinbox(form, from_=1, to=31, textvariable=day_var)
        day_spin.pack(fill='x', pady=(0, 15))
        
        ttk.Label(form, text="Descripción (opcional):", style='TLabel').pack(anchor='w', pady=(0, 5))
        ttk.Entry(form, textvariable=desc_var).pack(fill='x', pady=(0, 20))
        
        def save():
            try:
                selected_desc = table_var.get()
                table_name = table_options[selected_desc]
                month_idx = month_cb.current() + 1
                day = day_var.get()
                description = desc_var.get().strip() or None
                
                # Basic validation
                try:
                    date(2023, month_idx, day)
                except ValueError:
                    messagebox.showerror("Error", "Fecha inválida (e.g. 30 de Febrero)")
                    return

                with self.db_manager.get_db() as session:
                    # Check duplicates unless simple edit
                    if not existing_date:
                        exists = session.query(TaxDate).filter_by(
                            table_name=table_name, month=month_idx, day=day
                        ).first()
                        if exists:
                            messagebox.showerror("Error", "Ya existe una fecha para ese día en esa tabla.")
                            return
                        
                        new_date = TaxDate(table_name=table_name, month=month_idx, day=day, description=description)
                        session.add(new_date)
                    else:
                        # Re-query to attach to this session
                        current = session.query(TaxDate).get(existing_date.id)
                        current.table_name = table_name
                        current.month = month_idx
                        current.day = day
                        current.description = description
                    
                    session.commit()
                    
                messagebox.showinfo("Éxito", "Guardado correctamente")
                window.destroy()
                self.refresh_manage_list()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(form, text="💾 Guardar", command=save).pack(fill='x')

    def delete_date_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor selecciona un elemento para eliminar.")
            return
            
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas eliminar esta fecha?"):
            item = self.tree.item(selection[0])
            date_id = item['values'][0]
            
            try:
                if self.db_manager.delete_date(date_id):
                    self.refresh_manage_list()
                    messagebox.showinfo("Éxito", "Eliminado correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ================= TOOLS TAB =================

    def setup_tools_tab(self):
        container = ttk.Frame(self.tab_tools, padding="20")
        container.pack(fill='both', expand=True)
        
        ttk.Label(container, text="Herramientas de Mantenimiento", style='Header.TLabel').pack(anchor='w', pady=(0, 20))
        
        frame = ttk.Frame(container, style='Card.TFrame', padding="15")
        frame.pack(fill='x')
        
        ttk.Label(frame, text="⚠️ Zona de Peligro", style='CardText.TLabel', foreground=self.colors['danger']).pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text="Esta acción eliminará todas las fechas y tablas, devolviendo la base de datos a su estado original.",
                 style='CardText.TLabel', wraplength=700).pack(anchor='w', pady=(0, 15))
        
        ttk.Button(frame, text="🗑 Limpiar Base de Datos Completa", 
                 command=self.clean_database_action, 
                 style='Danger.TButton').pack(anchor='w')

    def clean_database_action(self):
        if messagebox.askyesno("PELIGRO", "⚠️ ¿Estás seguro? Esto eliminará TODOS los datos y no se puede deshacer."):
            if self.db_manager.clean_database():
                # Re-init default tables
                cli_app = TaxReminderMainGUI(self.root) # Hacky way to re-trigger default table creation logic if it was in init
                # Actually, models.py clean_database re-calls create_tables, but we need default rows
                # Let's manually re-add defaults similar to main.py
                default_tables = [
                    ('first_fortnight', 'Impuestos del 1-15 del mes'),
                    ('second_fortnight', 'Impuestos del 16 a fin de mes')
                ]
                for name, desc in default_tables:
                    self.db_manager.add_table(name, desc)
                    
                messagebox.showinfo("Éxito", "Base de datos reiniciada.")
                self.refresh_dashboard()
                self.refresh_manage_list()
            else:
                messagebox.showerror("Error", "Falló la limpieza de la base de datos.")

def main():
    root = tk.Tk()
    app = TaxReminderMainGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
