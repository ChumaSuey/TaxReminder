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
from datetime import date, datetime, timedelta
import calendar
from typing import List, Dict, Any

# Add project root to path
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from models import DatabaseManager, TaxDate, TaxTable

class CalendarWidget(ttk.Frame):
    def __init__(self, parent, colors, on_date_click=None, on_month_change=None):
        super().__init__(parent, style='TFrame')
        self.colors = colors
        self.on_date_click = on_date_click
        self.on_month_change = on_month_change
        self.today = date.today()
        self.current_month = self.today.month
        self.current_year = self.today.year
        self.highlighted_days = {} # {day: color}
        
        self.setup_ui()
        self.draw_calendar()

    def setup_ui(self):
        # Header: Prev, Month Year, Next
        header = ttk.Frame(self, style='TFrame')
        header.pack(fill='x', pady=(0, 10))
        
        self.prev_btn = ttk.Button(header, text="<", width=3, command=self.prev_month)
        self.prev_btn.pack(side='left')
        
        self.month_year_label = ttk.Label(header, text="", font=('Segoe UI', 11, 'bold'))
        # Manually set foreground for this label as it's not a standard style yet
        self.month_year_label.config(foreground=self.colors['fg'], background=self.colors['bg'])
        self.month_year_label.pack(side='left', expand=True)
        
        self.next_btn = ttk.Button(header, text=">", width=3, command=self.next_month)
        self.next_btn.pack(side='right')
        
        # Days of week header
        days_header = ttk.Frame(self, style='TFrame')
        days_header.pack(fill='x')
        
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, day in enumerate(days):
            lbl = ttk.Label(days_header, text=day, width=5, anchor='center', 
                          foreground=self.colors['text_secondary'], font=('Segoe UI', 8))
            lbl.grid(row=0, column=i, pady=2)
            
        # Days grid
        self.days_frame = ttk.Frame(self, style='TFrame')
        self.days_frame.pack(fill='both', expand=True)

    def draw_calendar(self):
        # Clear previous days
        for widget in self.days_frame.winfo_children():
            widget.destroy()
            
        self.month_year_label.config(text=f"{self._get_month_name(self.current_month)} {self.current_year}")
        
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                
                # Style for the day
                bg = self.colors['card_bg']
                fg = self.colors['fg']
                
                # Check if it's today
                is_today = (day == self.today.day and 
                           self.current_month == self.today.month and 
                           self.current_year == self.today.year)
                
                # Check highlighting (taxes)
                highlight_color = self.highlighted_days.get(day)
                
                day_frame = tk.Frame(self.days_frame, bg=bg, width=30, height=30)
                day_frame.grid(row=r, column=c, padx=1, pady=1)
                day_frame.grid_propagate(False)
                
                if highlight_color:
                    day_frame.config(bg=highlight_color)
                elif is_today:
                    # Simple border for today if not highlighted
                    day_frame.config(highlightbackground=self.colors['accent_blue'], highlightthickness=1)

                lbl = tk.Label(day_frame, text=str(day), bg=day_frame['bg'], fg=fg, 
                             font=('Segoe UI', 9, 'bold' if highlight_color or is_today else 'normal'))
                lbl.pack(expand=True, fill='both')
                
                if self.on_date_click:
                    lbl.bind("<Button-1>", lambda e, d=day: self.on_date_click(self.current_year, self.current_month, d))

    def _get_month_name(self, month):
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return months[month - 1]

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.draw_calendar()
        if self.on_month_change:
            self.on_month_change(self.current_year, self.current_month)

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.draw_calendar()
        if self.on_month_change:
            self.on_month_change(self.current_year, self.current_month)
        
    def set_highlights(self, highlighted_days):
        self.highlighted_days = highlighted_days
        self.draw_calendar()

class TaxReminderMainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Recordatorio de Impuestos - Sistema Completo")
        self.root.geometry("800x600")
        
        self.db_path = os.path.join(base_dir, 'tax_reminder.db')
        self.db_url = f'sqlite:///{self.db_path}'
        self.db_manager = DatabaseManager(self.db_url)
        
        self.config_path = os.path.join(base_dir, 'config.json')
        self.load_config()
        
        self.setup_styles()
        self.create_widgets()
        
    def load_config(self):
        """Load settings from config.json"""
        default_config = {'anticipation_days': 3}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                    # Merge with defaults for missing keys
                    for k, v in default_config.items():
                        if k not in self.config:
                            self.config[k] = v
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save settings to config.json"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
        
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

        # Tab 3: Payment History
        self.tab_history = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_history, text='📜 Historial de Pagos')
        self.setup_history_tab()
        
        # Tab 4: Tools
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
        elif tab_text == '📜 Historial de Pagos':
            self.refresh_history_list()

    # ================= DASHBOARD TAB =================
    
    def setup_dashboard_tab(self):
        container = ttk.Frame(self.tab_dashboard, padding="20")
        container.pack(fill='both', expand=True)
        
        # Header Frame with Anticipation Control
        header_frame = ttk.Frame(container)
        header_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(header_frame, text="Resumen de Vencimientos", style='Header.TLabel').pack(side='left')
        
        days_frame = ttk.Frame(header_frame)
        days_frame.pack(side='right')
        
        ttk.Label(days_frame, text="Anticipación (días):", font=('Segoe UI', 9)).pack(side='left', padx=(0, 5))
        self.days_ahead_var = tk.IntVar(value=self.config.get('anticipation_days', 3))
        
        days_spin = ttk.Spinbox(days_frame, from_=0, to=30, width=5, 
                              textvariable=self.days_ahead_var, command=self.on_anticipation_change)
        days_spin.pack(side='left')
        days_spin.bind('<Return>', lambda e: self.on_anticipation_change())
        
        # Content Area - Two columns
        self.dashboard_columns = ttk.Frame(container)
        self.dashboard_columns.pack(fill='both', expand=True)
        
        # Left: Reminders List
        self.reminders_column = ttk.Frame(self.dashboard_columns)
        self.reminders_column.pack(side='left', fill='both', expand=True)
        
        self.dashboard_content = ttk.Frame(self.reminders_column)
        self.dashboard_content.pack(fill='both', expand=True)
        
        # Right: Calendar Panel
        self.calendar_column = ttk.Frame(self.dashboard_columns, width=280)
        self.calendar_column.pack(side='right', fill='y', padx=(20, 0))
        self.calendar_column.pack_propagate(False)
        
        ttk.Label(self.calendar_column, text="Calendario Fiscal", 
                 style='TLabel', font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        self.calendar = CalendarWidget(self.calendar_column, self.colors, 
                                     on_month_change=self.update_calendar_highlights)
        self.calendar.pack(pady=10)
        
        # Legend
        legend_frame = ttk.Frame(self.calendar_column)
        legend_frame.pack(fill='x', pady=5)
        
        # Pending circle
        p_frame = tk.Frame(legend_frame, bg=self.colors['accent_gold'], width=12, height=12)
        p_frame.pack(side='left', padx=(0, 5))
        ttk.Label(legend_frame, text="Pendiente", font=('Segoe UI', 8)).pack(side='left', padx=(0, 15))
        
        # Today blue border (implied)
        t_frame = tk.Frame(legend_frame, highlightbackground=self.colors['accent_blue'], highlightthickness=1, bg=self.colors['card_bg'], width=12, height=12)
        t_frame.pack(side='left', padx=(0, 5))
        ttk.Label(legend_frame, text="Hoy", font=('Segoe UI', 8)).pack(side='left')

        self.refresh_dashboard()

    def on_anticipation_change(self):
        """Update and save the anticipation days setting"""
        try:
            val = self.days_ahead_var.get()
            if 0 <= val <= 30:
                self.config['anticipation_days'] = val
                self.save_config()
                self.refresh_dashboard()
        except:
            pass

    def refresh_dashboard(self):
        # Clear current content
        for widget in self.dashboard_content.winfo_children():
            widget.destroy()
            
        # Update calendar highlights
        self.update_calendar_highlights(self.calendar.current_year, self.calendar.current_month)
            
        try:
            today = date.today()
            today_reminders = []
            upcoming_reminders = []
            
            anticipation = self.config.get('anticipation_days', 3)

            # Logic same as gui_short.py / mainshort.py
            for days_ahead in range(0, anticipation + 1):
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
                        if self.db_manager.is_paid(date_obj.id, current_year):
                            continue # Skip paid taxes

                        reminder = {
                            'id': date_obj.id,
                            'table_description': table_desc,
                            'month': date_obj.month,
                            'day': date_obj.day,
                            'description': date_obj.description,
                            'days_until': days_until,
                            'year': current_year
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

    def update_calendar_highlights(self, year, month):
        """Update the calendar to show highlighting for tax dates"""
        highlighted = {}
        try:
            with self.db_manager.get_db() as session:
                # Get all tax dates for this month
                tax_dates = session.query(TaxDate).filter(TaxDate.month == month).all()
                
                for td in tax_dates:
                    # Check if paid for THIS specific year
                    is_paid = self.db_manager.is_paid(td.id, year)
                    if not is_paid:
                        highlighted[td.day] = self.colors['accent_gold']
                        
            self.calendar.set_highlights(highlighted)
        except Exception as e:
            print(f"Error updating calendar: {e}")

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
            if messagebox.askyesno("Confirmar Pago", f"¿Confirmar '{desc}' como PAGADO?"):
                try:
                    self.db_manager.mark_as_paid(reminder['id'], reminder['year'])
                    self.refresh_dashboard() # Reload to hide
                    messagebox.showinfo("Hecho", "Pago confirmado correctamente.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al confirmar pago: {e}")

        ttk.Button(card, text="✅ Confirmar Pago", command=pay_action).pack(anchor='e', pady=(10, 0))

    # ================= MANAGE TAB =================

    def setup_manage_tab(self):
        container = ttk.Frame(self.tab_manage, padding="20")
        container.pack(fill='both', expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(container)
        toolbar.pack(fill='x', pady=(0, 15))
        
        ttk.Button(toolbar, text="➕ Agregar Nuevo", command=self.add_date_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="⚡ Generador Rápido", command=self.quick_generator_dialog).pack(side='left', padx=(0, 10))
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
                    self.refresh_dashboard()
                    self.refresh_history_list()
                    messagebox.showinfo("Éxito", "Eliminado correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def quick_generator_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Generador Rápido de Fechas")
        dialog.geometry("450x400")
        dialog.configure(bg=self.colors['bg'])
        
        # We need data for combo boxes
        with self.db_manager.get_db() as session:
            tables = session.query(TaxTable).all()
            table_options = {t.description: t.name for t in tables}
            table_names_display = list(table_options.keys())
        
        form = ttk.Frame(dialog, padding="20")
        form.pack(fill='both', expand=True)

        ttk.Label(form, text="⚡ Generar fechas recurrentes mensualmente", 
                 style='Header.TLabel', font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 20))

        ttk.Label(form, text="Tabla / Categoría:", style='TLabel').pack(anchor='w', pady=(0, 5))
        table_var = tk.StringVar(value=table_names_display[0] if table_names_display else "")
        table_cb = ttk.Combobox(form, textvariable=table_var, values=table_names_display, state="readonly")
        table_cb.pack(fill='x', pady=(0, 15))
        
        ttk.Label(form, text="Día del mes (1-31):", style='TLabel').pack(anchor='w', pady=(0, 5))
        day_var = tk.IntVar(value=15)
        day_spin = ttk.Spinbox(form, from_=1, to=31, textvariable=day_var)
        day_spin.pack(fill='x', pady=(0, 15))
        
        ttk.Label(form, text="Descripción común:", style='TLabel').pack(anchor='w', pady=(0, 5))
        desc_var = tk.StringVar(value="Pago Mensual")
        ttk.Entry(form, textvariable=desc_var).pack(fill='x', pady=(0, 25))
        
        def generate():
            try:
                sel_table = table_options[table_var.get()]
                day = day_var.get()
                description = desc_var.get()
                
                count = 0
                with self.db_manager.get_db() as session:
                    for m in range(1, 13):
                        # Validez básica del día para el mes (evitar 31 de abril, etc.)
                        try:
                            date(2024, m, day)
                        except ValueError:
                            continue # Saltar meses que no tienen ese día
                            
                        # Check if exists
                        exists = session.query(TaxDate).filter_by(
                            table_name=sel_table, month=m, day=day
                        ).first()
                        
                        if not exists:
                            new_date = TaxDate(table_name=sel_table, month=m, day=day, description=description)
                            session.add(new_date)
                            count += 1
                    session.commit()
                
                messagebox.showinfo("Éxito", f"Se generaron {count} nuevas fechas.")
                dialog.destroy()
                self.refresh_manage_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(form, text="🚀 Generar para todo el año", command=generate).pack(fill='x')

    # ================= HISTORY TAB =================
    def setup_history_tab(self):
        # Main container
        main_frame = ttk.Frame(self.tab_history)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header and filter
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame, text="Historial de Pagos", style='Header.TLabel').pack(side='left')
        
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side='right')
        
        ttk.Label(filter_frame, text="Año:").pack(side='left', padx=(0, 5))
        current_year = date.today().year
        self.year_var = tk.StringVar(value=str(current_year))
        
        year_cb = ttk.Combobox(filter_frame, textvariable=self.year_var, width=8, state='readonly')
        year_cb['values'] = [str(y) for y in range(current_year - 2, current_year + 3)]
        year_cb.pack(side='left', padx=(0, 10))
        year_cb.bind('<<ComboboxSelected>>', lambda e: self.refresh_history_list())
        
        ttk.Button(filter_frame, text="🔄 Actualizar", command=self.refresh_history_list).pack(side='left', padx=(0, 10))
        ttk.Button(filter_frame, text="📂 Exportar a CSV", command=self.export_history_action).pack(side='left')
        
        # Treeview for history
        # Contenedor para la tabla y el scrollbar para evitar que se mezclen con los botones
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True)
        
        columns = ('payment_id', 'tax_date_id', 'Impuesto', 'Fecha Vencimiento', 'Fecha Pago', 'Acción')
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='extended')
        
        self.history_tree.heading('payment_id', text='ID Pago')
        self.history_tree.heading('tax_date_id', text='ID Fecha')
        self.history_tree.heading('Impuesto', text='Impuesto')
        self.history_tree.heading('Fecha Vencimiento', text='Vencimiento')
        self.history_tree.heading('Fecha Pago', text='Fecha de Pago')
        self.history_tree.heading('Acción', text='Estado')
        
        self.history_tree.column('payment_id', width=0, stretch=tk.NO) # Hide ID columns
        self.history_tree.column('tax_date_id', width=0, stretch=tk.NO)
        self.history_tree.column('Impuesto', width=250)
        self.history_tree.column('Fecha Vencimiento', width=120)
        self.history_tree.column('Fecha Pago', width=120)
        self.history_tree.column('Acción', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Actions frame - Packed at the bottom of main_frame
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill='x', pady=(15, 0))
        
        self.btn_unmark = ttk.Button(actions_frame, text="🗑 Anular Pago(s)", command=self.unmark_payment_action, state='disabled')
        self.btn_unmark.pack(side='left', padx=5)
        
        self.btn_mark = ttk.Button(actions_frame, text="✅ Confirmar Pago(s) Manual", command=self.mark_payment_manual_action, state='disabled')
        self.btn_mark.pack(side='left', padx=5)
        
        # Vincular selección para habilitar/deshabilitar botones
        self.history_tree.bind('<<TreeviewSelect>>', lambda e: self._update_history_buttons())

    def _update_history_buttons(self):
        selected = self.history_tree.selection()
        if not selected:
            self.btn_unmark.configure(state='disabled')
            self.btn_mark.configure(state='disabled')
            return
            
        any_paid = False
        any_unpaid = False
        
        for sel in selected:
            item = self.history_tree.item(sel)
            values = item['values']
            if not values: continue
            
            estado = str(values[5])
            if "Pagado" in estado:
                any_paid = True
            else:
                any_unpaid = True
        
        # Enable unmark if there is at least one paid item selected
        if any_paid:
            self.btn_unmark.configure(state='normal')
        else:
            self.btn_unmark.configure(state='disabled')
            
        # Enable mark if there is at least one unpaid item selected
        if any_unpaid:
            self.btn_mark.configure(state='normal')
        else:
            self.btn_mark.configure(state='disabled')

    def refresh_history_list(self):
        # Clear existing
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        try:
            year_val = self.year_var.get()
            if not year_val: return
            year = int(year_val)
            
            # 1. Get all taxes
            all_taxes = []
            with self.db_manager.get_db() as db:
                results = db.query(TaxDate, TaxTable.description).join(
                    TaxTable, TaxDate.table_name == TaxTable.name
                ).all()
                all_taxes = [(d, t) for d, t in results]
                
            # 2. Get payments for the year
            payments = self.db_manager.get_payment_history(year)
            paid_ids = {p['tax_date_id']: p for p in payments}
            
            # 3. Populate tree
            for date_obj, table_desc in sorted(all_taxes, key=lambda x: (x[0].month, x[0].day)):
                desc = self._format_table_name(table_desc)
                vencimiento = f"{date_obj.day:02d} {self._get_month_name(date_obj.month)}"
                
                if date_obj.id in paid_ids:
                    p = paid_ids[date_obj.id]
                    self.history_tree.insert('', 'end', values=(
                        p['payment_id'], 
                        date_obj.id, 
                        desc, 
                        vencimiento, 
                        p['payment_date'], 
                        "✅ Pagado"
                    ), tags=('paid',))
                else:
                    self.history_tree.insert('', 'end', values=(
                        "", 
                        date_obj.id, 
                        desc, 
                        vencimiento, 
                        "-", 
                        "❌ Pendiente"
                    ), tags=('unpaid',))
                    
            self.history_tree.tag_configure('paid', foreground='green')
            self.history_tree.tag_configure('unpaid', foreground='red')
            
            # Reset buttons
            self._update_history_buttons()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar historial: {e}")

    def unmark_payment_action(self):
        selected_ids = []
        names = []
        
        for sel in self.history_tree.selection():
            item = self.history_tree.item(sel)
            vals = item['values']
            if not vals: continue
            
            # Solo procesar los que están pagados
            if "Pagado" in str(vals[5]) and vals[0]:
                selected_ids.append(int(vals[0]))
                names.append(vals[2])
                
        if not selected_ids:
            messagebox.showinfo("Aviso", "No hay pagos seleccionados para anular.")
            return
            
        count = len(selected_ids)
        msg = f"¿Anular {count} pago(s)?" if count > 1 else f"¿Anular el pago de '{names[0]} '?"
        
        if messagebox.askyesno("Confirmar", msg):
            success_count = 0
            for p_id in selected_ids:
                if self.db_manager.unmark_as_paid(p_id):
                    success_count += 1
            
            self.refresh_history_list()
            self.refresh_dashboard()
            messagebox.showinfo("Éxito", f"Se anularon {success_count} pago(s).")

    def mark_payment_manual_action(self):
        selected_tax_ids = []
        names = []
        
        for sel in self.history_tree.selection():
            item = self.history_tree.item(sel)
            vals = item['values']
            if not vals: continue
            
            # Solo procesar los que están pendientes
            if "Pendiente" in str(vals[5]):
                selected_tax_ids.append(int(vals[1]))
                names.append(vals[2])
                
        if not selected_tax_ids:
            messagebox.showinfo("Aviso", "No hay impuestos pendientes seleccionados para confirmar.")
            return
            
        year = int(self.year_var.get())
        count = len(selected_tax_ids)
        msg = f"¿Confirmar {count} pagos en el año {year}?" if count > 1 else f"¿Confirmar pago de '{names[0]}' para el año {year}?"
        
        if messagebox.askyesno("Confirmar Pago", msg):
            success_count = 0
            for t_id in selected_tax_ids:
                if self.db_manager.mark_as_paid(t_id, year):
                    success_count += 1
            
            self.refresh_history_list()
            self.refresh_dashboard()
            messagebox.showinfo("Éxito", f"Se confirmaron {success_count} pago(s).")

    def export_history_action(self):
        """Export current filtered history to CSV"""
        import csv
        from tkinter import filedialog
        
        try:
            year_val = self.year_var.get()
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"Historial_Pagos_{year_val}.csv"
            )
            
            if not filename:
                return
                
            # Get data from treeview (it's already filtered)
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["Impuesto", "Vencimiento", "Año", "Fecha de Pago", "Estado"])
                
                # Rows
                for item_id in self.history_tree.get_children():
                    vals = self.history_tree.item(item_id)['values']
                    if not vals: continue
                    # vals: payment_id (0), tax_date_id (1), Impuesto (2), Vencimiento (3), Pago (4), Estado (5)
                    writer.writerow([vals[2], vals[3], year_val, vals[4], vals[5]])
                    
            messagebox.showinfo("Éxito", f"Historial exportado correctamente a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

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
