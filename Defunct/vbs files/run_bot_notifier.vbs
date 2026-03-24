Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe telegram_bot.py --notify-only", 0
Set WshShell = Nothing
