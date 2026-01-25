import os
import json
import logging
import time
import requests
from datetime import date, timedelta
from typing import List, Dict, Any

from models import DatabaseManager, TaxDate, TaxTable
import argparse

# --- Configuration ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8518113467:AAGlL_BOvmv4oBh-KCvITVGnhf45LH1hkcc")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "226321594")
SECRET_PASSWORD = os.getenv("TELEGRAM_BOT_PASSWORD", "servifletesdeoccidente")

DATABASE_URL = "sqlite:///tax_reminder.db"
ACK_FILE = "acknowledgements.json"
AUTH_FILE = "authorized_users.json"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaxBot:
    def __init__(self, db_manager: DatabaseManager, ack_file: str, auth_file: str):
        self.db = db_manager
        self.ack_file = ack_file
        self.auth_file = auth_file
        self.acks = self._load_data(self.ack_file)
        self.authorized_users = self._load_data(self.auth_file)
        self.last_update_id = 0

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

    def _get_ack_key(self, tax: Dict[str, Any], check_date: date) -> str:
        return f"{check_date.year}_{tax['table']}_{tax['month']}_{tax['day']}"

    def acknowledge_tax(self, ack_key: str):
        self.acks[ack_key] = date.today().isoformat()
        self._save_data(self.ack_file, self.acks)

    def authorize_user(self, chat_id: int):
        self.authorized_users[str(chat_id)] = date.today().isoformat()
        self._save_data(self.auth_file, self.authorized_users)

    def is_authorized(self, chat_id: int) -> bool:
        # Owner is always authorized
        if str(chat_id) == str(CHAT_ID):
            return True
        return str(chat_id) in self.authorized_users

    def get_upcoming_taxes(self) -> List[Dict[str, Any]]:
        today = date.today()
        upcoming = []
        for days_ahead in range(0, 3):
            check_date = today + timedelta(days=days_ahead)
            results = self.db.get_dates_by_month_day(check_date.month, check_date.day)
            for tax in results:
                ack_key = self._get_ack_key(tax, check_date)
                if ack_key not in self.acks:
                    tax['days_until'] = days_ahead
                    tax['ack_key'] = ack_key
                    tax['date_obj'] = check_date
                    upcoming.append(tax)
        return upcoming

    def format_message(self, taxes: List[Dict[str, Any]]) -> str:
        if not taxes:
            return "✅ No hay vencimientos pendientes para los próximos 2 días."
        msg = "🔔 *RECORDATORIO DE IMPUESTOS*\n\n"
        for tax in sorted(taxes, key=lambda x: x['days_until']):
            when = "HOY" if tax['days_until'] == 0 else ("MAÑANA" if tax['days_until'] == 1 else "PASADO MAÑANA")
            date_str = tax['date_obj'].strftime('%d/%m/%Y')
            msg += f"📌 *{tax['table_description']}*\n"
            msg += f"📅 Fecha: {date_str} ({when})\n"
            if tax.get('description'):
                msg += f"📝 Detalle: {tax['description']}\n"
            msg += f"✅ Marcar pagado: `/pago {tax['ack_key']}`\n\n"
        return msg

    def send_request(self, method: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
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
                    if "message" in update and "text" in update["message"]:
                        self.handle_command(update["message"])
            time.sleep(1)

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
        if text == "/start" or text == "/help":
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": "👋 Hola! Soy tu bot de impuestos.\n\nComandos:\n/check - Ver vencimientos próximos\n/pago [key] - Marcar como pagado",
                "parse_mode": "Markdown"
            })
        elif text == "/check":
            taxes = self.get_upcoming_taxes()
            self.send_request("sendMessage", {
                "chat_id": chat_id,
                "text": self.format_message(taxes),
                "parse_mode": "Markdown"
            })
        elif text.startswith("/pago"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                ack_key = parts[1]
                self.acknowledge_tax(ack_key)
                self.send_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": f"✅ Registro `{ack_key}` marcado como pagado.",
                    "parse_mode": "Markdown"
                })
            else:
                self.send_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ Falta la clave. Uso: `/pago [key]`"
                })

def main():
    parser = argparse.ArgumentParser(description="Tax Reminder Telegram Bot")
    parser.add_argument("--notify-only", action="store_true", help="Send upcoming notifications and exit immediately.")
    parser.add_argument("--listen", action="store_true", default=True, help="Run as a persistent listener (default).")
    args = parser.parse_args()

    db_manager = DatabaseManager(DATABASE_URL)
    bot = TaxBot(db_manager, ACK_FILE, AUTH_FILE)
    
    # Run initial check and notify ALL authorized users
    upcoming = bot.get_upcoming_taxes()
    if upcoming:
        logger.info(f"Found {len(upcoming)} initial taxes. Sending reminders...")
        
        # Notify owner
        bot.send_request("sendMessage", {
            "chat_id": CHAT_ID,
            "text": bot.format_message(upcoming),
            "parse_mode": "Markdown"
        })
        
        # Notify other authorized users
        for user_id in bot.authorized_users:
            bot.send_request("sendMessage", {
                "chat_id": user_id,
                "text": bot.format_message(upcoming),
                "parse_mode": "Markdown"
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
