# 📅 Telegram Tax Reminder Bot (v2.0)

An interactive, secure, and modern Telegram bot that synchronizes with the TaxReminder Desktop application. It provides proactive alerts, visual calendars, and easy document export directly from your chat.

## ✨ Modern Features

- **Interactive Main Menu**: Persistent bottom menu for quick access to status, calendar, and reports.
- **Text-Based Visual Calendar**: An emoji-based month grid (`🟡` Pending, `🔵` Today) for a quick fiscal overview.
- **Smart Reminders**: Synchronizes with `config.json` to remind you according to your custom anticipation settings.
- **Double-Confirmation Workspace**: Advanced confirmation flow (`Confirm` / `Cancel`) to prevent accidental payment entries on mobile.
- **CSV Export**: Request and receive Excel-compatible payment history reports directly in the chat.
- **Multi-User Security**: Robust password-based `/login` system for multiple authorized users.
- **Developer Mode**: Specialized test mode for safe debugging without notifying real users.

## 🤖 Commands & Interaction

- `🔄 Consultar Vencimientos` / `/check`: Shows pending taxes for upcoming days (defined in settings).
- `📅 Ver Calendario` / `/calendario`: Displays the visual month grid with emoji highlights.
- `📂 Exportar CSV` / `/export`: Generates and sends a `.csv` report of the current year's history.
- `❓ Ayuda / Menú` / `/menu`: Displays the main welcome message and all available commands.
- `✅ Confirmar Pago`: Interactive workflow to mark taxes as paid in the database.
- `/login [password]`: Authorize a new device/user.

## 🛠️ Setup & Security

### 1. Configuration (Public/Template)
For public repositories or code sharing, use **`telegram_bot_template.py`**. 
It includes all the logic but requires you to provide your credentials:

- `BOT_TOKEN`: From Telegram's @BotFather.
- `CHAT_ID`: Your personal Telegram Numeric ID.
- `SECRET_PASSWORD`: Your custom access password for the `/login` command.

### 2. Private Setup
The actual production script is **`telegram_bot.py`**. 
> [!WARNING]
> This file is listed in `.gitignore` to prevent sensitive credentials from being pushed to public version control. **Never remove it from .gitignore if it contains your real Token.**

### 3. Running the Bot
- **Standard Linker**: `python telegram_bot.py --listen`
- **Notify Only**: `python telegram_bot.py --notify-only` (Ideal for CRON jobs)
- **Developer Mode**: `python developer_cmd.py`

### 4. Background (Windows)
To run the bot in the background (hidden terminal):
1. Ensure the `.exe` versions in the `dist/` folder are used, or:
2. Use a `.vbs` wrapper to launch the Python script silently.

---
*Created for the TaxReminder Project. Modernized in Phase 2.*
