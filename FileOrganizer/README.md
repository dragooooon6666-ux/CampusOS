# FileOrganizer - 文件自动归档助手

自动监控 `input` 文件夹，按**文档内容类型**归档到 `output`，支持 AI 智能命名。

---

## 普通用户使用方式

### 首次安装

1. 安装 Python 3.11+：[python.org](https://www.python.org/downloads/)（勾选「Add Python to PATH」）
2. 双击项目目录下的 `setup.bat`
3. 等待依赖安装和快捷方式创建完成
4. **桌面上会出现「文件归档助手」图标**，开始菜单也可以搜索到

### 启动程序

- **桌面图标**：双击桌面的「文件归档助手」
- **开始菜单**：按 Win 键搜索「文件归档助手」
- **手动启动**：双击项目目录下的 `启动助手.vbs`（静默）或 `启动助手.bat`（显示检查信息）

> 程序启动后无窗口，会在任务栏**右下角托盘区**显示一个黄色文件夹图标。

### 日常使用

1. 把需要整理的文件放入 `input` 文件夹
2. 程序自动检测并归档到 `output` 下对应的分类文件夹
3. 归档后的文件保留原名，output 中生成规范命名的副本

### 托盘图标说明

右键点击任务栏右下角的黄色文件夹图标：

| 菜单项 | 功能 |
|---|---|
| 开启/暂停监控 | 临时停止自动归档 |
| 开启/关闭 AI 智能命名 | 切换 AI 命名（需先配置 API Key） |
| 配置 AI | 填写 DeepSeek / OpenAI / Kimi 的 API Key |
| 打开 input 文件夹 | 快速打开待整理文件目录 |
| 打开 output 文件夹 | 快速打开归档输出目录 |
| 一键清理重复文件 | 按内容比对删除 output 中的重复文件 |
| 查看日志文件 | 打开今天的运行日志 |
| 退出程序 | 停止监控并退出 |

### 退出程序

右键托盘图标 → 退出程序，或直接关闭计算机（程序会自动退出）。

---

## 输出文件夹说明

### AI 模式（默认，需配置 API Key）

文件按**文档内容类型**分类：

```
output/
├── 简历/       ← 个人简历
├── 作业/       ← 课程作业
├── 论文/       ← 学术论文
├── 策划案/     ← 活动策划
├── 方案/       ← 实施方案
├── 议程/       ← 会议议程
├── 会议纪要/   ← 会议记录
├── 活动总结/   ← 活动复盘
├── 报告/       ← 实验/调研报告
├── 申请书/     ← 各类申请
├── 通知/       ← 通知公告
├── 证明/       ← 证明文件
├── 笔记/       ← 学习笔记
├── 其他文档/   ← 无法归类的文档
├── 图片/       ← 照片、截图等（不消耗 AI）
├── 视频/       ← 视频文件（不消耗 AI）
├── 压缩包/     ← zip/rar 等（不消耗 AI）
└── 其他/       ← 其他文件
```

### V1 模式（未配置 AI 或 AI 关闭时）

文件按**扩展名**分类：`Word/` `Excel/` `PDF/` `图片/` `视频/` `压缩包/` `其他/`

---

## 开发环境

### 项目结构

```
FileOrganizer/
├── input/                  # 放入待整理文件
├── output/                 # 按类型归档的副本
├── config/                 # 配置文件
├── logs/                   # 运行日志
├── main.py                 # 默认入口（托盘模式）
├── cli.py                  # 命令行模式
├── organizer.py            # 核心监控+归档逻辑
├── naming.py               # V1 规则命名 + 调度
├── ai_naming.py            # V2 AI 智能命名
├── content_extractor.py    # 文件内容提取
├── dedupe.py               # 重复文件清理
├── config.py               # 配置管理
├── tray_app.py             # 系统托盘 UI
├── settings_ui.py          # 配置窗口（tkinter）
├── requirements.txt        # 依赖
├── 启动助手.vbs             # 静默启动器
├── 启动助手.bat             # 控制台启动器（环境检查）
└── setup.bat               # 首次使用安装向导
```

### 安装依赖

```powershell
pip install -r requirements.txt
```

### 运行方式

```powershell
pythonw main.py    # 托盘模式（推荐）
python cli.py      # 命令行模式（Ctrl+C 停止）
```

---

## 打包成 exe

1. 安装打包工具：

```powershell
pip install pyinstaller
```

2. 在项目目录执行：

```powershell
pyinstaller --onefile --windowed --name FileOrganizer main.py
```

3. 生成的 exe 位于 `dist\FileOrganizer.exe`。将其复制到项目根目录后，运行 `setup.bat` 会自动检测 exe 并创建指向它的快捷方式，不再依赖 Python 环境。

如需自定义图标：

```powershell
pyinstaller --onefile --windowed --icon=icon.ico --name FileOrganizer main.py
```
