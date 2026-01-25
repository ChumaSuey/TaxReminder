# 📅 Telegram Tax Reminder Bot

An interactive Telegram bot that queries the Tax Reminder database and sends proactive alerts for upcoming tax deadlines.

## ✨ Key Features

- **Real-time Integration**: Queries `tax_reminder.db` directly.
- **Nagging Alerts**: Reminds you 2 days before, 1 day before, and on the day of the tax.
- **Acknowledgement**: Stop alerts for a specific period by marking them as paid.
- **Multi-User**: Secure password-based system for multiple authorized users.
- **Background Mode**: Run silently on Windows without a terminal window.

## 🤖 Commands

- `/check` - Manually show taxes due in the next 3 days.
- `/pago [key]` - Mark a specific tax as paid/acknowledged.
- `/login [password]` - Authorize yourself to use the bot (for new users).
- `/help` - Show available commands.

## 🛠️ Setup & Usage

### 1. Configuration

Edit `telegram_bot.py` and provide:

- `TELEGRAM_BOT_TOKEN` (from @BotFather)
- `TELEGRAM_CHAT_ID` (your personal ID)
- `SECRET_PASSWORD` (default: `servifletesdeoccidente`)

### 2. Running the Bot

- **Standard**: `python telegram_bot.py`
- **Background (Windows)**: Run `python createvbshost.py` once, then double-click the resulting `start_bot.vbs`.

### 3. Security

When sharing this code, run `python cleanTOKENID.py` to automatically remove all sensitive credentials (Tokens, IDs, and Passwords) from the source code.

---
*Created for the TaxReminder Project*
