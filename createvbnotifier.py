import os

def create_vbs_notifier():
    vbs_filename = "run_bot_notifier.vbs"
    # We use the --notify-only flag
    script_to_run = "telegram_bot.py --notify-only"
    
    # Content of the VBScript that runs the python script silently
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe {script_to_run}", 0
Set WshShell = Nothing
'''

    try:
        with open(vbs_filename, "w") as vbs_file:
            vbs_file.write(vbs_content)
        
        print(f"✅ Successfully created {vbs_filename}")
        print(f"🔔 You can now use {vbs_filename} in Windows Task Scheduler for daily alerts.")
    except Exception as e:
        print(f"❌ Error creating VBS notifier: {e}")

if __name__ == "__main__":
    create_vbs_notifier()
