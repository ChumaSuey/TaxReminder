import os
import sys

# FIX: Force Tcl/Tk paths for Windows Virtual Environments
if sys.platform == 'win32':
    # Path to the global Python installation where Tcl/Tk resides
    # Inferred from user's error log: C:/Users/luism/AppData/Local/Programs/Python/Python313
    PYTHON_INSTALL_DIR = r'C:\Users\luism\AppData\Local\Programs\Python\Python313'
    
    tcl_path = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
    tk_path = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')
    
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ['TCL_LIBRARY'] = tcl_path
        os.environ['TK_LIBRARY'] = tk_path
        print(f"Set TCL_LIBRARY={tcl_path}")
        print(f"Set TK_LIBRARY={tk_path}")

import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
from typing import List, Dict, Any

# Add project root to path to import models
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
sys.path.append(base_dir)

from models import DatabaseManager, TaxDate, TaxTable

class TaxReminderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Recordatorio de Impuestos")
        self.root.geometry("500x600")
        
        # Determine DB path
        self.db_path = os.path.join(base_dir, 'tax_reminder.db')
        self.db_url = f'sqlite:///{self.db_path}'
        
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def setup_styles(self):
        """Configure dark mode styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 'clam' allows better color customization usually
        
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'card_bg': '#2d2d2d',
            'accent_gold': '#ffd700',
            'accent_blue': '#4a90e2',
            'success': '#4caf50',
            'text_secondary': '#b0b0b0'
        }
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Frames
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat')
        
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
                           background=self.colors['card_bg'],
                           foreground=self.colors['fg'],
                           borderwidth=0)
        self.style.map('TButton',
                      background=[('active', self.colors['accent_blue'])],
                      foreground=[('active', self.colors['fg'])])

    def create_widgets(self):
        # Main Container with padding
        self.main_container = ttk.Frame(self.root, padding="20")
        self.main_container.pack(fill='both', expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title = ttk.Label(header_frame, text="📅 Recordatorio de Impuestos", style='Header.TLabel')
        title.pack(anchor='w')
        
        today_date = date.today().strftime('%d/%m/%Y')
        subtitle = ttk.Label(header_frame, text=f"Fecha: {today_date}", style='TLabel')
        subtitle.pack(anchor='w')
        
        # Separator
        ttk.Separator(self.main_container, orient='horizontal').pack(fill='x', pady=(0, 20))
        
        # Content Area (Scrollable could be added here if needed, but keeping it simple for short view)
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill='both', expand=True)

    def load_data(self):
        try:
            db = DatabaseManager(self.db_url)
            today = date.today()
            today_reminders = []
            upcoming_reminders = []

            # Logic adapted from mainshort.py
            for days_ahead in range(0, 3):
                check_date = today + timedelta(days=days_ahead)
                with db.get_db() as session:
                    results = session.query(TaxDate, TaxTable.description).join(
                        TaxTable, TaxDate.table_name == TaxTable.name
                    ).filter(
                        TaxDate.month == check_date.month,
                        TaxDate.day == check_date.day
                    ).all()

                    for date_obj, table_desc in results:
                        # Calculate current year logic
                        current_year = today.year
                        if date_obj.month < today.month or (date_obj.month == today.month and date_obj.day < today.day):
                            current_year += 1
                        
                        reminder_date = date(current_year, date_obj.month, date_obj.day)
                        days_until = (reminder_date - today).days

                        reminder = {
                            'table_description': table_desc,
                            'month': date_obj.month,
                            'day': date_obj.day,
                            'description': date_obj.description,
                            'days_until': days_until
                        }

                        if days_until == 0:
                            today_reminders.append(reminder)
                        elif days_until > 0:
                            upcoming_reminders.append(reminder)

            self.display_reminders(today_reminders, upcoming_reminders)

        except Exception as e:
            self.show_error(str(e))

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

    def display_reminders(self, today_reminders, upcoming_reminders):
        # Clear previous content if any (not strictly needed here as we run once)
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not today_reminders and not upcoming_reminders:
            no_data = ttk.Label(self.content_frame, 
                              text="✅ No hay vencimientos para hoy ni para los próximos 2 días.",
                              style='TLabel')
            no_data.pack(pady=20)
            return

        # Today's Reminders
        if today_reminders:
            ttk.Label(self.content_frame, text="🔔 ¡VENCIMIENTOS PARA HOY!", style='SubHeaderToday.TLabel').pack(anchor='w', pady=(0, 10))
            for reminder in today_reminders:
                self.create_reminder_card(reminder, is_today=True)
            ttk.Separator(self.content_frame, orient='horizontal').pack(fill='x', pady=20)

        # Upcoming Reminders
        if upcoming_reminders:
            ttk.Label(self.content_frame, text="🔔 PRÓXIMOS VENCIMIENTOS", style='SubHeaderUpcoming.TLabel').pack(anchor='w', pady=(0, 10))
            for reminder in sorted(upcoming_reminders, key=lambda x: x['days_until']):
                self.create_reminder_card(reminder, is_today=False)

    def create_reminder_card(self, reminder, is_today):
        card = ttk.Frame(self.content_frame, style='Card.TFrame', padding="10")
        card.pack(fill='x', pady=(0, 10))
        
        # Title/Table Name
        desc = self._format_table_name(reminder['table_description'])
        ttk.Label(card, text=f"• {desc}", style='CardText.TLabel', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        # Date and Time Info
        month_name = self._get_month_name(reminder['month'])
        days_text = ""
        if not is_today:
             days_text = f" (mañana)" if reminder['days_until'] == 1 else f" (en {reminder['days_until']} días)"
        
        date_text = f"📅 {reminder['day']} de {month_name}{days_text}"
        ttk.Label(card, text=date_text, style='CardText.TLabel').pack(anchor='w')
        
        # Description if exists
        if reminder.get('description'):
            ttk.Label(card, text=f"📝 {reminder['description']}", style='CardDesc.TLabel').pack(anchor='w', pady=(5, 0))

    def show_error(self, message):
        error_label = ttk.Label(self.content_frame, text=f"Error: {message}", foreground="red", background=self.colors['bg'])
        error_label.pack()

def main():
    root = tk.Tk()
    app = TaxReminderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
