' ============================================================
' 文件归档助手 - 静默启动器
' 双击此文件即可启动程序，不会弹出命令行窗口
' ============================================================

Option Explicit

Dim objShell, objFSO, strScriptDir, strPython, strMain, strCmd, objExec, strOutput
Dim strErrorTitle, strErrorMsg

strErrorTitle = "文件归档助手 - 启动失败"

' 获取脚本所在目录
Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 尝试查找 pythonw.exe
strPython = ""
On Error Resume Next
Set objShell = CreateObject("WScript.Shell")

' 先尝试直接调用 pythonw（依赖 PATH 环境变量）
objShell.Run "pythonw --version", 0, True
If Err.Number = 0 Then
    strPython = "pythonw"
End If
Err.Clear

' 如果 PATH 中没有，尝试常见安装路径
If strPython = "" Then
    Dim arrPaths, strPath
    arrPaths = Array( _
        objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python314\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python313\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%ProgramFiles%") & "\Python314\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%ProgramFiles%") & "\Python313\pythonw.exe", _
        objShell.ExpandEnvironmentStrings("%ProgramFiles%") & "\Python312\pythonw.exe", _
        "C:\Python314\pythonw.exe", _
        "C:\Python313\pythonw.exe", _
        "C:\Python312\pythonw.exe" _
    )
    Dim eachPath
    For Each eachPath In arrPaths
        If objFSO.FileExists(eachPath) Then
            strPython = eachPath
            Exit For
        End If
    Next
End If

If strPython = "" Then
    strErrorMsg = "未找到 Python 运行环境。" & vbCrLf & vbCrLf & _
                  "请先运行项目目录下的 setup.bat 进行安装。" & vbCrLf & vbCrLf & _
                  "如果已安装 Python，请确认 pythonw.exe 在系统 PATH 中。"
    MsgBox strErrorMsg, vbCritical + vbSystemModal, strErrorTitle
    WScript.Quit 1
End If

' 检查 main.py 是否存在
strMain = strScriptDir & "\main.py"
If Not objFSO.FileExists(strMain) Then
    strErrorMsg = "未找到程序入口文件：" & vbCrLf & strMain & vbCrLf & vbCrLf & _
                  "请确保启动助手与 main.py 在同一目录下。"
    MsgBox strErrorMsg, vbCritical + vbSystemModal, strErrorTitle
    WScript.Quit 1
End If

' 静默启动
strCmd = """" & strPython & """ """ & strMain & """"
objShell.Run strCmd, 0, False

Set objShell = Nothing
Set objFSO = Nothing
