import os
import sys
import logging
from telegram_bot import main

if __name__ == "__main__":
    print("=" * 40)
    print(" TAX REMINDER - BOT LISTENER ")
    print("=" * 40)
    print("This window will stay open and listen for commands.")
    print("Press Ctrl+C to stop the bot.\n")

    # Ensure the listener mode is triggered
    # telegram_bot.main uses argparse and 'listen' defaults to True,
    # but we can pass it explicitly if needed or just call main().
    
    try:
        sys.argv = [sys.argv[0], "--listen"]
        main()
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user (Ctrl+C).")
        input("\nPress Enter to close this window...")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        input("\nPress Enter to close this window...")
