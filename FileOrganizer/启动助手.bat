@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: 文件归档助手 - 控制台启动器（带详细环境检查）
:: 如果静默启动失败，请双击此文件查看具体错误原因
:: ============================================================

title 文件归档助手 - 启动中...

cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║     文件归档助手 - 环境检查             ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ── 检查 1：Python 是否存在 ──────────────────────────
echo  [1/3] 检查 Python 运行环境...

set PYTHON_EXE=
pythonw --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=pythonw
    goto :check_deps
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    goto :check_deps
)

:: pythonw/python 都不在 PATH 中，尝试常见路径
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
    "%ProgramFiles%\Python314\pythonw.exe"
    "%ProgramFiles%\Python313\pythonw.exe"
    "C:\Python314\pythonw.exe"
    "C:\Python313\pythonw.exe"
) do (
    if exist %%p (
        set PYTHON_EXE=%%p
        goto :check_deps
    )
)

echo  [✗] 未找到 Python！
echo.
echo  ┌─────────────────────────────────────────────┐
echo  │  请先安装 Python 3.11 或更高版本：          │
echo  │  https://www.python.org/downloads/          │
echo  │                                             │
echo  │  安装时请勾选 "Add Python to PATH"          │
echo  │                                             │
echo  │  安装完成后，运行 setup.bat 安装项目依赖    │
echo  └─────────────────────────────────────────────┘
echo.
pause
exit /b 1

:: ── 检查 2：依赖是否已安装 ──────────────────────────
:check_deps
echo  [✓] 找到 Python: !PYTHON_EXE!
echo  [2/3] 检查项目依赖...

"%PYTHON_EXE%" -c "import pystray, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [✗] 项目依赖未安装或不完整！
    echo.
    echo  ┌─────────────────────────────────────────────┐
    echo  │  请运行项目目录下的 setup.bat              │
    echo  │  它会自动安装所需依赖                        │
    echo  │                                             │
    echo  │  或者手动执行：                              │
    echo  │  pip install -r requirements.txt            │
    echo  └─────────────────────────────────────────────┘
    echo.
    pause
    exit /b 1
)
echo  [✓] 项目依赖已安装

:: ── 检查 3：配置文件是否存在 ────────────────────────
echo  [3/3] 检查配置文件...

if not exist "config\settings.json" (
    echo  [!] 配置文件不存在，将自动创建默认配置
    if not exist "config" mkdir "config"
    copy "config\settings.example.json" "config\settings.json" >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [✗] 无法创建配置文件，请检查目录权限
        pause
        exit /b 1
    )
    echo  [✓] 已创建默认配置文件（AI 命名功能需手动配置 API Key）
) else (
    echo  [✓] 配置文件已存在
)

:: ── 启动程序 ────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║     正在启动文件归档助手...              ║
echo  ║     程序将在系统托盘运行                  ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 用 pythonw 以无窗口模式启动（如果是 python 则会有窗口）
if "!PYTHON_EXE!"=="pythonw" (
    start "" pythonw "%~dp0main.py"
) else (
    start "" "!PYTHON_EXE!" "%~dp0main.py"
)

:: 短暂等待后关闭此窗口
timeout /t 2 /nobreak >nul
exit /b 0
