# TaxReminder: Smart Fiscal Tracking

A complete suite for managing tax payments, consisting of a modern Desktop GUI and a fully-featured Telegram Bot. Never miss a tax deadline again.

## 🚀 Key Features

### 🖥️ Desktop Application (GUI)
- **Visual Fiscal Calendar:** Quick monthly view with icons for pending and today's taxes.
- **Configurable Anticipation:** Set how many days in advance you want to be reminded.
- **Quick Entry Generator:** Bulk-create recurring monthly tax dates in one click.
- **CSV Export:** Generate Excel-compatible reports for your accounting needs.
- **Dark Mode UI:** Modern, clean interface designed for efficiency.

### 🤖 Telegram Bot
- **Interactive Menu:** Unified menu for checking upcoming taxes, viewing the calendar, and exporting reports.
- **Double-Confirmation:** Secure payment registration with a "Are you sure?" confirmation step to prevent accidental clicks.
- **Text-Based Calendar:** An emoji-based month grid for quick visual checks via chat.
- **Syncing:** The bot automatically respects the settings (like anticipation days) configured in the Desktop App.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- SQLAlchemy

### Environment Setup
1. Clone the repository or download the source.
2. Install dependencies:
   ```bash
   pip install sqlalchemy requests python-dotenv
   ```
3. Set your environment variables:
   - Copy `.env.template` to `.env`.
   - Fill in your `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `TELEGRAM_BOT_PASSWORD`.

### Running the App
- **GUI:** Run `python gui_main.py` or use the `TaxRGUI.exe` in the `dist/` folder.
- **Bot:** Run `python telegram_bot.py --listen` or use the `TaxBotListener.exe` in the `dist/` folder.

## 📂 Project Structure
- `gui_main.py`: Main desktop interface logic.
- `telegram_bot.py`: Telegram bot core and interaction logic.
- `models.py`: Database schema and management.
- `config.json`: Persistent user settings.
- `tax_reminder.db`: Database file.
- `authorized_users.json`: Authorized users for the Telegram bot.
- `dist/`: Ready-to-use standalone executables for Windows.

## 📄 License
This project is for personal use and fiscal management.

---
*Created with ❤️ to simplify tax management.*
