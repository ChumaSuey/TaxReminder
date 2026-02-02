import os
import sys
import logging
from telegram_bot import main

if __name__ == "__main__":
    print("=" * 40)
    print(" TAX REMINDER - DEVELOPER MODE ")
    print("=" * 40)
    print("Running in developer mode. Messages sent only to active developers.")
    print("Press Ctrl+C to stop the bot.\n")

    try:
        sys.argv = [sys.argv[0], "--developer"]
        main()
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user (Ctrl+C).")
        input("\nPress Enter to close this window...")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        input("\nPress Enter to close this window...")
