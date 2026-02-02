import os
import sys
import time
import logging
from telegram_bot import main

if __name__ == "__main__":
    print("=" * 40)
    print(" TAX REMINDER - INSTANT NOTIFIER ")
    print("=" * 40)
    print("Sending notifications for upcoming taxes...\n")

    try:
        # Trigger notify-only mode
        sys.argv = [sys.argv[0], "--notify-only"]
        main()
        
        print("\n" + "=" * 40)
        print("Done! Notifications have been sent.")
        print("This window will close in 10 seconds...")
        print("=" * 40)
        
        # Keep open for a bit so the user can read the output
        for i in range(10, 0, -1):
            sys.stdout.write(f"\rClosing in {i} seconds... ")
            sys.stdout.flush()
            time.sleep(1)
            
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        input("\nPress Enter to close this window...")
