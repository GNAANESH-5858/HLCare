Set objShell = CreateObject("Wscript.Shell")

' Path to backend
backendPath = "D:\HLCare\project\backend"
objShell.CurrentDirectory = backendPath

' Run Flask silently (hidden terminal)
objShell.Run "cmd /c python app.py", 0, False

' Wait 5 seconds for server to start
WScript.Sleep 5000

' Open frontend in browser via Flask
objShell.Run "http://127.0.0.1:5000"
