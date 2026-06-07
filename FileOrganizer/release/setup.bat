@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: 文件归档助手 - 首次使用安装向导
:: 功能：安装依赖 → 检测运行模式 → 创建桌面/开始菜单快捷方式
:: ============================================================

title 文件归档助手 - 安装向导

cd /d "%~dp0"
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   文件归档助手 - 首次使用安装向导       ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ── 步骤 0：检测 Python ───────────────────────────────
echo  [步骤 1/4] 检查 Python 环境...

set PYTHON_EXE=
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    set PIP_EXE=pip
    goto :found_python
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=py
    set PIP_EXE=py -m pip
    goto :found_python
)

echo  [✗] 未找到 Python！
echo.
echo  请先安装 Python 3.11+ ：https://www.python.org/downloads/
echo  安装时务必勾选 "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
for /f "tokens=*" %%i in ('%PYTHON_EXE% --version 2^>^&1') do set PY_VER=%%i
echo  [✓] 找到 %PY_VER%

:: ── 步骤 1：安装依赖 ──────────────────────────────────
echo.
echo  [步骤 2/4] 安装项目依赖...

echo  正在安装，请稍候...
%PIP_EXE% install -r "requirements.txt" --quiet 2>&1
if %errorlevel% neq 0 (
    echo  [✗] 依赖安装失败！
    echo  请尝试手动执行：pip install -r requirements.txt
    pause
    exit /b 1
)
echo  [✓] 依赖安装完成

:: ── 步骤 2：检测运行模式 ──────────────────────────────
echo.
echo  [步骤 3/4] 检测运行模式...

:: 未来打包后：如果 exe 存在，优先使用 exe
set "LAUNCHER_PATH="
set "LAUNCHER_MODE="

if exist "%PROJECT_DIR%\FileOrganizer.exe" (
    set "LAUNCHER_PATH=%PROJECT_DIR%\FileOrganizer.exe"
    set "LAUNCHER_MODE=exe 模式（已打包）"
    echo  [✓] 检测到 FileOrganizer.exe，使用已打包模式
) else if exist "%PROJECT_DIR%\启动助手.vbs" (
    set "LAUNCHER_PATH=%PROJECT_DIR%\启动助手.vbs"
    set "LAUNCHER_MODE=开发模式（Python 脚本）"
    echo  [✓] 开发模式 - 通过 Python 运行
) else (
    echo  [✗] 未找到可启动的程序入口！
    echo  请确保 启动助手.vbs 或 FileOrganizer.exe 在同一目录
    pause
    exit /b 1
)

:: ── 步骤 3：创建快捷方式 ──────────────────────────────
echo.
echo  [步骤 4/4] 创建快捷方式...

set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT_NAME=文件归档助手"

:: 创建桌面快捷方式
echo  正在创建桌面快捷方式...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut('%DESKTOP_DIR%\%SHORTCUT_NAME%.lnk'); " ^
    "$s.TargetPath = '%LAUNCHER_PATH%'; " ^
    "$s.WorkingDirectory = '%PROJECT_DIR%'; " ^
    "$s.Description = '自动监控 input 文件夹并按类型归档文件'; " ^
    "$s.Save(); " ^
    "Write-Host '  [✓] 桌面快捷方式已创建'"

if %errorlevel% neq 0 (
    echo  [!] 桌面快捷方式创建失败，请手动创建
) else (
    :: 如果使用 vbs 启动，设置快捷方式运行方式为最小化（避免闪烁）
    if "!LAUNCHER_MODE!"=="开发模式（Python 脚本）" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "$ws = New-Object -ComObject WScript.Shell; " ^
            "$s = $ws.CreateShortcut('%DESKTOP_DIR%\%SHORTCUT_NAME%.lnk'); " ^
            "$s.WindowStyle = 7; " ^
            "rem 7 = 最小化窗口"; " ^
            "$s.Save()" >nul 2>&1
    )
)

:: 创建开始菜单快捷方式
echo  正在创建开始菜单快捷方式...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut('%STARTMENU_DIR%\%SHORTCUT_NAME%.lnk'); " ^
    "$s.TargetPath = '%LAUNCHER_PATH%'; " ^
    "$s.WorkingDirectory = '%PROJECT_DIR%'; " ^
    "$s.Description = '自动监控 input 文件夹并按类型归档文件'; " ^
    "$s.Save(); " ^
    "Write-Host '  [✓] 开始菜单快捷方式已创建'"

if %errorlevel% neq 0 (
    echo  [!] 开始菜单快捷方式创建失败，可能需要管理员权限
)

:: ── 完成 ──────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         安装完成！                      ║
echo  ╠══════════════════════════════════════════╣
echo  ║  运行模式：!LAUNCHER_MODE!              ║

if "!LAUNCHER_MODE!"=="开发模式（Python 脚本）" (
    echo  ║                                          ║
    echo  ║  AI 智能命名（可选）：                    ║
    echo  ║  启动后右键托盘图标 → 配置 AI            ║
    echo  ║  支持 DeepSeek / OpenAI / Kimi            ║
)

echo  ║                                          ║
echo  ║  启动方式：                              ║
echo  ║  • 桌面图标「文件归档助手」双击启动      ║
echo  ║  • 开始菜单搜索「文件归档助手」          ║
echo  ║                                          ║
echo  ║  程序在任务栏右下角托盘运行              ║
echo  ║  将文件放入 input 文件夹即可自动归档     ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  现在可以关闭此窗口，双击桌面图标启动程序。
echo.
pause
exit /b 0
