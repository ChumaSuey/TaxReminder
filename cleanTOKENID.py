import re
import os

def clean_credentials():
    target_file = 'telegram_bot.py'
    
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found.")
        return

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the replacements
    token_pattern = r'BOT_TOKEN = os\.getenv\("TELEGRAM_BOT_TOKEN", ".*?"\)'
    chat_id_pattern = r'CHAT_ID = os\.getenv\("TELEGRAM_CHAT_ID", ".*?"\)'
    pass_pattern = r'SECRET_PASSWORD = os\.getenv\("TELEGRAM_BOT_PASSWORD", ".*?"\)'
    
    new_content = re.sub(token_pattern, 'BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "INSERT_HERE_TOKEN")', content)
    new_content = re.sub(chat_id_pattern, 'CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "INSERT_TELEGRAM_CHAT_ID")', new_content)
    new_content = re.sub(pass_pattern, 'SECRET_PASSWORD = os.getenv("TELEGRAM_BOT_PASSWORD", "INSERT_PASSWORD_HERE")', new_content)

    if content == new_content:
        print("No credentials found to clean or already cleaned.")
    else:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully sanitized {target_file}.")

if __name__ == "__main__":
    clean_credentials()
