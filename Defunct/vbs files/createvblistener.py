import os

def create_vbs_listener():
    vbs_filename = "run_bot_listener.vbs"
    # We use the default behavior (which is --listen)
    script_to_run = "telegram_bot.py"
    
    # Content of the VBScript that runs the python script silently
    # pythonw.exe is used to run without a console window
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe {script_to_run}", 0
Set WshShell = Nothing
'''

    try:
        with open(vbs_filename, "w") as vbs_file:
            vbs_file.write(vbs_content)
        
        print(f"✅ Successfully created {vbs_filename}")
        print(f"🚀 Double-click {vbs_filename} to start the bot in the background (Listen mode).")
        print("💡 Use Task Manager to stop 'pythonw.exe' if you need to turn it off.")
    except Exception as e:
        print(f"❌ Error creating VBS listener: {e}")

if __name__ == "__main__":
    create_vbs_listener()
