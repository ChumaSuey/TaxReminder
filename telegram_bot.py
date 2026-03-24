import os
import sys
import json
import logging
import calendar
import time
import requests
from datetime import date, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

from models import DatabaseManager, TaxDate, TaxTable
import argparse

# --- Configuration (ENV) ---
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Load .env from the script's directory
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_PASSWORD = os.getenv("TELEGRAM_BOT_PASSWORD")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment!")
    print("Please create a .env file based on .env.template")
    # We don't exit here to allow help/version if added later, 
    # but the bot will fail on first request.

# Path setup
# (Already defined above for dotenv)

DATABASE_URL = f"sqlite:///{os.path.join(base_dir, 'tax_reminder.db')}"
AUTH_FILE = os.path.join(base_dir, "authorized_users.json")
DEV_FILE = os.path.join(base_dir, "dev_users.json")
CONFIG_FILE = os.path.join(base_dir, "config.json")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaxBot:
    def __init__(self, db_manager: DatabaseManager, auth_file: str, dev_file: str = DEV_FILE, config_file: str = CONFIG_FILE):
        self.db = db_manager
        self.auth_file = auth_file
        self.dev_file = dev_file
        self.config_file = config_file
        self.last_update_id = 0
        self.developer_mode = False
        self.reload_configs()

    def reload_configs(self):
        """Reload all JSON configuration files from disk."""
        self.authorized_users = self._load_data(self.auth_file)
        self.dev_users = self._load_data(self.dev_file)
        self.config = self._load_data(self.config_file)
        if 'anticipation_days' not in self.config:
            self.config['anticipation_days'] = 3

    def _load_data(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        return {}

    def _save_data(self, file_path: str, data: Dict[str, Any]):
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    def acknowledge_tax(self, tax_date_id: int, year: int):
        self.db.mark_as_paid(tax_date_id, year)

    def authorize_user(self, chat_id: int):
        self.authorized_users[str(chat_id)] = date.today().isoformat()
        self._save_data(self.auth_file, self.authorized_users)

    def is_authorized(self, chat_id: int) -> bool:
        # Reload to ensure manual edits to authorized_users.json are picked up
        self.authorized_users = self._load_data(self.auth_file)
        
        # Owner is always authorized
        if str(chat_id) == str(CHAT_ID):
            return True
        return str(chat_id) in self.authorized_users

    def get_upcoming_taxes(self) -> List[Dict[str, Any]]:
        self.reload_configs()
        today = date.today()
        upcoming = []
        anticipation = self.config.get('anticipation_days', 3)
        
        for days_ahead in range(0, anticipation + 1):
            check_date = today + timedelta(days=days_ahead)
            results = self.db.get_dates_by_month_day(check_date.month, check_date.day)
            for tax in results:
                if not self.db.is_paid(tax['id'], check_date.year):
                    tax['days_until'] = days_ahead
                    tax['year'] = check_date.year
                    tax['date_obj'] = check_date
                    upcoming.append(tax)
        return upcoming

    def get_pending_days_for_month(self, year, month):
        """Helper to find which days have pending taxes in a given month"""
        pending = []
        with self.db.get_db() as session:
            results = session.query(TaxDate).filter_by(month=month).all()
            for tax in results:
                if not self.db.is_paid(tax.id, year):
                    pending.append(tax.day)
        return set(pending)

    def get_text_calendar(self, year, month):
        """Generates the emoji-based text calendar grid"""
        # Ensure Monday is the first day
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        
        pending_days = self.get_pending_days_for_month(year, month)
        today = date.today()
        
        # Build message
        month_name = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
                      "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"][month-1]
        
        header = f"📅 *{month_name} {year}*\n"
        header += "`LU MA MI JU VI SA DO` \n"
        
        body = ""
        for week in month_days:
            week_str = ""
            for day in week:
                if day == 0:
                    week_str += "   "
                elif day == today.day and month == today.month and year == today.year:
                    week_str += "🔵 " # Today
                elif day in pending_days:
                    week_str += "🟡 " # Pending
                else:
                    week_str += f"{day:02d} "
            body += f"`{week_str}`\n"
        
        footer = "\n🟡 = Pendiente | 🔵 = Hoy"
        return header + body + footer

    def format_message(self, taxes: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        if not taxes:
            return "✅ No hay vencimientos pendientes para los próximos 2 días.", None
        
        msg = "🔔 *RECORDATORIO DE IMPUESTOS*\n\n"
        keyboard = []
        
        for tax in sorted(taxes, key=lambda x: x['days_until']):
            when = "HOY" if tax['days_until'] == 0 else ("MAÑANA" if tax['days_until'] == 1 else f"en {tax['days_until']} días")
            date_str = tax['date_obj'].strftime('%d/%m/%Y')
            
            # Message text
            msg += f"📌 *{tax['table_description']}*\n"
            msg += f"📅 Fecha: {date_str} ({when})\n"
            if tax.get('description'):
                msg += f"📝 Detalle: {tax['description']}\n"
            msg += "\n" # Spacing
            
            # Button - Updated Terminology "Confirmar"
            btn_text = f"Confirmar {tax['table_description']} ({date_str})"
            if len(btn_text) > 60:
                btn_text = btn_text[:57] + "..."
                
            keyboard.append([{"text": f"✅ {btn_text}", "callback_data": f"pago_{tax['id']}_{tax['year']}"}])

        reply_markup = {"inline_keyboard": keyboard}
        return msg, reply_markup

    def get_main_menu_markup(self):
        """Standard keyboard at bottom of screen"""
        return {
            "keyboard": [
                [{"text": "🔄 Consultar Vencimientos"}, {"text": "📅 Ver Calendario"}],
                [{"text": "📂 Exportar CSV"}, {"text": "❓ Ayuda / Menú"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

    def send_request(self, method: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            return {"ok": False, "error": "NOT_CONFIGURED"}
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
        try:
            # We use a 45s timeout because getUpdates uses a 30s long polling timeout
            response = requests.post(url, json=payload, timeout=45)
            return response.json()
        except Exception as e:
            logger.error(f"Telegram API Error ({method}): {e}")
            return {"ok": False}

    def listen(self):
        """Poll for updates and respond to commands"""
        logger.info("Bot started listening...")
        while True:
            updates = self.send_request("getUpdates", {"offset": self.last_update_id + 1, "timeout": 30})
            if updates.get("ok"):
                for update in updates.get("result", []):
                    self.last_update_id = update["update_id"]
                    try:
                        if "message" in update and "text" in update["message"]:
                            self.handle_command(update["message"])
                        elif "callback_query" in update:
                            self.handle_callback(update["callback_query"])
                    except Exception as e:
                        logger.error(f"Error handling update: {e}")
            time.sleep(1)

    def handle_callback(self, callback: Dict[str, Any]):
        cq_id = callback["id"]
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        # message_id = callback["message"]["message_id"] # useful if we want to edit the message

        # Basic Auth Check
        if not self.is_authorized(chat_id):
            self.send_request("answerCallbackQuery", {
                "callback_query_id": cq_id,
                "text": "⛔ No autorizado.",
                "show_alert": True
            })
            return

        if data == "check":
            taxes = self.get_upcoming_taxes()
            msg, markup = self.format_message(taxes)
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown",
                "reply_markup": markup
            })
            self.send_request("answerCallbackQuery", {"callback_query_id": cq_id})
        
        elif data.startswith("pago_"):
            # Step 1: Request Confirmation (Dynamic UI protection)
            payment_info = data.replace("pago_", "", 1)
            parts = payment_info.split('_')
            tax_id = int(parts[0])
            tax_year = int(parts[1])
            
            # Get details for the confirmation message
            tax_name = "Impuesto"
            with self.db.get_db() as session:
                tax_obj = session.query(TaxDate, TaxTable.description).join(
                    TaxTable, TaxDate.table_name == TaxTable.name
                ).filter(TaxDate.id == tax_id).first()
                if tax_obj:
                    tax_name = tax_obj[1]
            
            confirm_keyboard = [[
                {"text": "⚠️ Confirmar Pago", "callback_data": f"confirm_{payment_info}"},
                {"text": "❌ Cancelar", "callback_data": f"cancel_{payment_info}"}
            ]]
            
            self.send_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": callback["message"]["message_id"],
                "text": f"❓ ¿Confirmar pago de *{tax_name}* para el año {tax_year}?\n\nEsta acción registrará el pago en la base de datos.",
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": confirm_keyboard}
            })
            self.send_request("answerCallbackQuery", {"callback_query_id": cq_id})

        elif data.startswith("confirm_"):
            # Step 2: Actually Pay
            payment_info = data.replace("confirm_", "", 1)
            parts = payment_info.split('_')
            
            if len(parts) == 2:
                tax_id = int(parts[0])
                year = int(parts[1])
                self.acknowledge_tax(tax_id, year)
                
                self.send_request("answerCallbackQuery", {
                    "callback_query_id": cq_id,
                    "text": "✅ Pago confirmado"
                })
                self.send_request("editMessageText", {
                    "chat_id": chat_id,
                    "message_id": callback["message"]["message_id"],
                    "text": f"✅ Pago confirmado exitosamente.",
                    "parse_mode": "Markdown",
                    "reply_markup": None
                })
            else:
                self.send_request("answerCallbackQuery", {
                    "callback_query_id": cq_id,
                    "text": "❌ Error parsing payment info"
                })

        elif data.startswith("cancel_"):
            # Step 3: Cancel and Restore view
            self.send_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": callback["message"]["message_id"],
                "text": "❌ Acción cancelada. Usa /check para ver la lista de nuevo.",
                "reply_markup": None
            })
            self.send_request("answerCallbackQuery", {"callback_query_id": cq_id, "text": "Cancelado"})
            
        else:
            self.send_request("answerCallbackQuery", {"callback_query_id": cq_id})


    def handle_command(self, message: Dict[str, Any]):
        text = message["text"].strip()
        chat_id = message["chat"]["id"]
        
        # Unauthorized users can only attempt /login
        if not self.is_authorized(chat_id):
            if text.startswith("/login"):
                parts = text.split(maxsplit=1)
                if len(parts) > 1 and parts[1] == SECRET_PASSWORD:
                    self.authorize_user(chat_id)
                    self.send_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": "🔓 Acceso concedido. Ahora recibirás recordatorios y podrás usar los comandos.",
                        "parse_mode": "Markdown"
                    })
                    logger.info(f"User authorized: {chat_id}")
                else:
                    self.send_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": "❌ Contraseña incorrecta o comando inválido. Uso: `/login [password]`"
                    })
            else:
                logger.warning(f"Ignored message from unauthorized chat: {chat_id}")
                # Optional: Send a hint to unauthorized users
                self.send_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": "🔒 No tienes acceso. Por favor usa `/login [contraseña]` para entrar."
                })
            return

        # Commands for authorized users
        if text == "/start" or text == "/help" or text == "/menu" or text == "❓ Ayuda / Menú":
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": "👋 *Bienvenido al menú de TaxReminder*\n\n"
                        "Usa los botones de abajo o los comandos:\n\n"
                        "🔄 `/check` - Ver vencimientos próximos\n"
                        "📅 `/calendario` - Ver mapa visual del mes\n"
                        "📂 `/export` - Recibir historial en CSV (Excel)\n"
                        "✅ `/pago [ID] [AÑO]` - Confirmar pago manual\n"
                        "📝 `/menu` - Mostrar este mensaje",
                "parse_mode": "Markdown",
                "reply_markup": self.get_main_menu_markup()
            })
        elif text == "/check" or text == "🔄 Consultar Vencimientos":
            taxes = self.get_upcoming_taxes()
            msg, markup = self.format_message(taxes)
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown",
                "reply_markup": markup if markup else self.get_main_menu_markup()
            })
        elif text == "/calendario" or text == "📅 Ver Calendario":
            today = date.today()
            cal_msg = self.get_text_calendar(today.year, today.month)
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": cal_msg,
                "parse_mode": "Markdown",
                "reply_markup": self.get_main_menu_markup()
            })
        elif text == "/export" or text == "📂 Exportar CSV":
            self.handle_export(chat_id)
        elif text.startswith("/pago"):
            parts = text.split(maxsplit=2)
            if len(parts) == 3:
                try:
                    tax_id = int(parts[1])
                    year = int(parts[2])
                    self.acknowledge_tax(tax_id, year)
                    self.send_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": f"✅ Impuesto ID {tax_id} marcado como pagado para el año {year}.",
                        "parse_mode": "Markdown"
                    })
                except ValueError:
                    self.send_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": "❌ Formato incorrecto. Uso: `/pago [tax_id] [year]`"
                    })
            else:
                self.send_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ Faltan parámetros. Uso: `/pago [tax_id] [year]`"
                })

    def handle_export(self, chat_id: int):
        """Generate and send CSV history to user"""
        import csv
        import io
        
        try:
            current_year = date.today().year
            history = self.db.get_payment_history(current_year)
            
            output = io.StringIO()
            # BOM for Excel
            output.write('\ufeff')
            writer = csv.writer(output)
            writer.writerow(["Impuesto", "Vencimiento", "Año", "Fecha de Pago", "Estado"])
            
            for p in history:
                vencimiento = f"{p['day']:02d}/{p['month']:02d}"
                writer.writerow([p['table_description'], vencimiento, p['year'], p['payment_date'], "✅ Pagado"])
                
            # Send as file
            file_data = output.getvalue().encode('utf-8')
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            files = {'document': (f'Historial_Pagos_{current_year}.csv', file_data)}
            data = {'chat_id': chat_id, 'caption': f'📂 Historial de impuestos para el año {current_year}'}
            
            requests.post(url, data=data, files=files)
            
        except Exception as e:
            logger.error(f"Error in handle_export: {e}")
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": f"❌ Error al generar el reporte: {e}"
            })

def main():
    parser = argparse.ArgumentParser(description="Tax Reminder Telegram Bot")
    parser.add_argument("--notify-only", action="store_true", help="Send upcoming notifications and exit immediately.")
    parser.add_argument("--listen", action="store_true", default=True, help="Run as a persistent listener (default).")
    parser.add_argument("--developer", action="store_true", help="Run in developer mode (restricted notifications).")
    args = parser.parse_args()

    db_manager = DatabaseManager(DATABASE_URL)
    bot = TaxBot(db_manager, AUTH_FILE, DEV_FILE)
    bot.developer_mode = args.developer
    
    if bot.developer_mode:
        logger.info("DEVELOPER MODE ACTIVE: Messages will only be sent to active developers.")

    # Run initial check and notify authorized users
    upcoming = bot.get_upcoming_taxes()
    if upcoming:
        logger.info(f"Found {len(upcoming)} initial taxes. Sending reminders...")
        
        # Ensure we have the latest user lists before broadcasting
        bot.reload_configs()
        
        # Determine recipients
        recipients = []
        if bot.developer_mode:
            # Only active developers
            recipients = [uid for uid, info in bot.dev_users.items() if info.get("active")]
        else:
            # Owner + all authorized users
            recipients = [CHAT_ID] + list(bot.authorized_users.keys())

        for user_id in set(recipients):
            msg, markup = bot.format_message(upcoming)
            bot.send_request("sendMessage", {
                "chat_id": user_id,
                "text": msg,
                "parse_mode": "Markdown",
                "reply_markup": markup if markup else {}
            })
    else:
        logger.info("No upcoming taxes found.")

    # If notify-only is set, exit here
    if args.notify_only:
        logger.info("Notify-only mode complete. Exiting.")
        return

    # Start the interactive loop
    try:
        bot.listen()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")

if __name__ == "__main__":
    main()
