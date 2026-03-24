# 📅 Telegram Tax Reminder Bot

An interactive Telegram bot that queries the Tax Reminder database and sends proactive alerts for upcoming tax deadlines.

## ✨ Key Features

- **Real-time Integration**: Queries `tax_reminder.db` directly.
- **Nagging Alerts**: Reminds you 2 days before, 1 day before, and on the day of the tax.
- **Interactive Buttons**: Click buttons to mark taxes as paid with confirmation workflow.
- **Acknowledgement System**: Stop alerts for specific periods by acknowledging payments.
- **Multi-User**: Secure password-based system for multiple authorized users.
- **Developer Mode**: Test mode that sends notifications only to active developers.
- **Background Mode**: Run silently on Windows without a terminal window.

## 🤖 Commands

- `/start` or `/help` - Show welcome message and quick action button.
- `/check` - Display taxes due in the next 3 days with interactive payment buttons.
- `/pago [key]` - Mark a specific tax as paid (alternative to buttons).
- `/login [password]` - Authorize yourself to use the bot (for new users).

## 🔘 Interactive Features

The bot provides **inline keyboard buttons** for:

- **Quick Check**: Button to instantly view upcoming taxes.
- **Payment Buttons**: Each tax has a "Pagar" (Pay) button.
- **Confirmation Flow**: Two-step confirmation (Confirm/Cancel) to prevent accidental marking.

## 🛠️ Setup & Usage

### 1. Configuration

Edit `telegram_bot.py` and provide:

- `BOT_TOKEN` (from @BotFather)
- `CHAT_ID` (your personal ID)
- `SECRET_PASSWORD` (your chosen password)

Or set environment variables:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_BOT_PASSWORD`

### 2. Running the Bot

**Basic modes:**

- `python telegram_bot.py` - Standard listener mode
- `python telegram_bot.py --notify-only` - Send notifications once and exit
- `python telegram_bot.py --developer` - Developer mode (restricted recipients)

**Convenience wrappers:**

- `python developer_cmd.py` - Launches bot in developer mode
- `python listener_cmd.py` - Launches bot in listener mode

**Background (Windows)**: Run `python createvbshost.py` once, then double-click the resulting `start_bot.vbs`.

### 3. Developer Mode

When running with `--developer` flag, notifications are sent only to users listed in `dev_users.json` with `"active": true`. Useful for testing without spamming all users.

### 4. Security

When sharing this code, run `python cleanTOKENID.py` to automatically remove all sensitive credentials (Tokens, IDs, and Passwords) from the source code.

---
*Created for the TaxReminder Project*
