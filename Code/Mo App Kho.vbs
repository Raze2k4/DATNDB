Option Explicit

' Launcher cho App Kho QR: chạy dịch vụ quét QR nền rồi mở cửa sổ ứng dụng riêng.
Dim shell, fso, root, edgePath, pythonCommand, command, checkCode, venvPython
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)

edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
If Not fso.FileExists(edgePath) Then
  edgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
End If

If Not fso.FileExists(root & "\MaQR_web.py") Then
  MsgBox "Không tìm thấy MaQR_web.py trong thư mục: " & root, vbCritical, "App Kho QR"
  WScript.Quit 1
End If

venvPython = "C:\Users\trand\PycharmProjects\PythonProject\.venv\Scripts\python.exe"
If fso.FileExists(venvPython) Then
  pythonCommand = """" & venvPython & """"
Else
  checkCode = shell.Run("cmd /c py -3 --version >nul 2>&1", 0, True)
  If checkCode <> 0 Then
    MsgBox "Không tìm thấy Python có OpenCV để chạy camera QR." & vbCrLf & vbCrLf & _
           "Hãy mở PyCharm, kiểm tra lại Interpreter, hoặc cài Python rồi chạy:" & vbCrLf & _
           "py -3 -m pip install opencv-python", vbCritical, "App Kho QR"
    WScript.Quit 1
  End If
  pythonCommand = "py -3"
End If
command = pythonCommand & " """ & root & "\MaQR_web.py"" --no-window"
shell.Run command, 0, False

' Cho dịch vụ camera khởi động trước khi mở cửa sổ app.
WScript.Sleep 1800
If fso.FileExists(edgePath) Then
  shell.Run """" & edgePath & """ --app=http://127.0.0.1:5000 --start-maximized", 1, False
Else
  shell.Run "http://127.0.0.1:5000", 1, False
End If
