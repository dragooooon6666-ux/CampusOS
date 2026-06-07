# FileOrganizer 开发日志

> 最后更新：2026-06-07
> 当前阶段：P0 完成，待进入真实用户测试

---

## 一、项目概述

**FileOrganizer（文件自动归档助手）** 是一个 Windows 桌面工具，帮助大学生（学生会/团委/班委/社团负责人）自动整理文件。

**核心能力**：
- 监控 `input` 文件夹，按内容类型自动归档到 `output`
- AI 智能识别文档类型（简历/作业/论文/策划案…共 14 类）并提取标题/日期/作者
- Windows 系统托盘运行，支持静默启动和快捷方式
- 支持 DeepSeek / OpenAI / Kimi 三家 AI 模型
- MD5 内容去重

---

## 二、项目文件清单

```
FileOrganizer/
│
├── main.py                 # 入口（托盘模式），用 pythonw 启动无窗口
├── cli.py                  # 命令行模式入口
├── organizer.py            # 核心：监控 input、归档、暂停/恢复
├── naming.py               # V1 规则命名 + V2 调度，返回 (filename, category)
├── ai_naming.py            # V2 AI 命名：提取内容→调 API→解析 JSON→组装文件名
├── content_extractor.py    # 文件内容提取（docx/pdf/xlsx/txt）
├── dedupe.py               # MD5 去重（output 目录）
├── config.py               # 配置管理：AI_MODE、AI_PROVIDER、AI_API_KEYS
├── tray_app.py             # 系统托盘 UI + 首次引导 + 通知注入
├── settings_ui.py          # tkinter AI 配置窗口
├── notify.py               # 【本次新增】用户通知：错误弹窗 + 气泡通知 + 欢迎窗口
│
├── FileOrganizer.spec      # 【本次新增】PyInstaller 打包配置
├── setup.bat               # 【本次新增】首次安装向导（装依赖+创快捷方式）
├── 启动助手.vbs             # 【本次新增】静默启动器
├── 启动助手.bat             # 【本次新增】控制台启动器（环境检查）
├── requirements.txt         # 依赖：pystray, Pillow, python-docx, PyPDF2, openpyxl
├── .gitignore               # 排除 config/settings.json, logs/, output/, input/
├── README.md                # 用户文档
│
├── input/                   # 待归档文件（用户放入）
├── output/                  # 归档输出（21 个子文件夹）
├── config/                  # settings.json（含 API Key，不提交 git）
├── logs/                    # 运行日志（按天）
├── dist/                    # PyInstaller 输出 (FileOrganizer.exe)
└── release/                 # 【本次新增】可分发测试包
    ├── FileOrganizer.exe
    ├── setup.bat
    ├── 启动助手.vbs
    ├── 启动助手.bat
    └── FileOrganizer-测试版.zip
```

---

## 三、本次会话完成的工作（2026-06-07）

### 阶段一：AI 识别优化

**问题**：AI 命名只知道文件名，不知道文件内容

**改动**：
- 新建 `content_extractor.py`：从 docx/pdf/xlsx/txt 提取文本（前 800 字）
- 重写 `ai_naming.py`：
  - Prompt 改为结构化 JSON 输出（doc_type / title / doc_date / author）
  - 定义 14 种大学生文档类型
  - 强制 `response_format: json_object`
  - 文件名格式：`2026年6月7日-简历-贺龙个人简历.docx`
  - 日期优先级：落款时间 > 文件修改时间
- 改进 `naming.py` V1 关键词提取：英文保留完整、中文前 6 字、剥离后为空回退原文

### 阶段二：输出分类改版

**问题**：按文件扩展名分类（Word/PDF/Excel）对学生没意义

**改动**：
- `organizer.py` 新增 21 个分类文件夹（14 内容 + 7 扩展名兜底）
- `naming.py` 的 `generate_new_filename` 返回 `(filename, category)` 元组
- `ai_naming.py` 的 `generate_ai_filename` 返回 `{"filename", "doc_type", "doc_date"}`
- 非文本文件（图片/视频/音频/压缩包 30 种扩展名）跳过 AI，直接走 V1

### 阶段三：快捷启动

**问题**：用户必须用命令行启动

**改动**：
- 新建 `启动助手.vbs`：静默启动，多路径查找 pythonw，失败弹对话框
- 新建 `启动助手.bat`：三步环境检查（Python→依赖→配置），中文错误提示
- 新建 `setup.bat`：安装依赖 + 检测 exe/开发模式 + 创建桌面和开始菜单快捷方式
- 更新 `README.md`：新增普通用户使用指南

### 阶段四：P0 收尾（打包+通知+错误提示）

**问题**：没有 exe 无法分发；用户不知道程序在做什么；出错只写日志不弹窗

**改动**：
- 新建 `FileOrganizer.spec`：PyInstaller 配置，处理 hidden imports
- 构建 `dist/FileOrganizer.exe`（36MB，单文件，windowed 模式）
- 新建 `notify.py`：
  - `show_error` / `show_warning`：线程安全 messagebox + 日志 + 会话去重
  - `show_archive_notification`：托盘气泡，2 秒聚合窗口，最多显示 5 条
  - `show_welcome_window`：首次使用引导，AI 配置入口按钮
  - `should_show_welcome`：config 不存在或 API Key 为空时触发
- `tray_app.py`：注入托盘图标引用 + 首次引导检查 + 归档回调绑定
- `organizer.py`：`set_archive_callback` 方法 + 启动和归档错误弹窗
- `ai_naming.py`：API 401/403/429/网络 分别弹窗提示

---

## 四、当前架构关键接口

### 函数签名一览

```python
# naming.py
generate_new_filename(file_path: Path, category_hint: str = "") -> tuple[str, str]
# 返回 (filename, category)，AI 模式下 category 为内容类型，V1 为扩展名类型

# ai_naming.py
generate_ai_filename(file_path: Path, category_hint: str = "其他") -> dict | None
# 返回 {"filename": str, "doc_type": str, "doc_date": str} 或 None

# organizer.py
OrganizerService.set_archive_callback(callback)  # 注入通知回调
# callback 签名: (original_name: str, new_name: str, category: str) -> None

# notify.py
show_error(title, message, error_key="", once_per_session=True)
show_warning(title, message, error_key="", once_per_session=True)
show_archive_notification(original_name, new_name, category)
show_welcome_window(configure_callback=None)
should_show_welcome() -> bool
set_tray_icon(icon)  # 注入托盘图标引用
```

### 分类体系

```python
# 14 个 AI 内容类型
CONTENT_CATEGORIES = ["简历","作业","论文","策划案","方案","议程",
                      "会议纪要","活动总结","报告","申请书","通知",
                      "证明","笔记","其他文档"]

# 7 个 V1 扩展名类型（兜底）
FILE_TYPE_CATEGORIES = ["Word","Excel","PDF","图片","视频","压缩包","其他"]

# 30 种非文本扩展名（跳过 AI，直接 V1）
NON_TEXT_EXTENSIONS = {".jpg", ".mp4", ".zip", ...}
```

---

## 五、当前配置文件状态

`config/settings.json`：
```json
{
  "AI_MODE": true,
  "AI_PROVIDER": "deepseek",
  "AI_MODEL": "",
  "AI_API_KEYS": {
    "openai": "",
    "deepseek": "sk-e8e6a37f137d41cbadcc29ebe45c5b64",
    "kimi": ""
  }
}
```

⚠️ 该文件已加入 `.gitignore`。测试用 Key 在本次会话中暴露过，建议正式发布前更换。

---

## 六、下一步开发（按路线图顺序）

### P1（P0 完成 + 用户反馈后）

| # | 任务 | 改动范围 |
|---|---|---|
| 5 | 一键整理桌面 + 下载文件夹 | `tray_app.py` 加菜单项 + `organizer.py` 加扫描逻辑 |
| 6 | 分类层级化（组→类） | `organizer.py` 加 `CATEGORY_GROUPS` 映射，output 改为 `{group}/{type}/` |

### P2（数据基础，不建功能）

| # | 任务 | 改动范围 |
|---|---|---|
| 7 | metadata.jsonl | `organizer.py` 归档后追加一行 JSON Lines |

### 明确不做的（当前阶段）

- 多模型切换 UI 复杂化
- 统计面板
- 搜索系统
- 云同步/SaaS
- 数据库
- 新增文件格式支持
- 复杂启动器逻辑

---

## 七、如何继续开发

### 下次打开的方式

1. 启动 Claude Code，工作目录 `D:\ai-workspace\test-project\FileOrganizer`
2. 把这个文件的内容告诉 Claude（或让它读 `DEVELOPMENT_LOG.md`）
3. 根据用户反馈或路线图选择下一个任务

### 测试发版

```powershell
# 打包
cd D:\ai-workspace\test-project\FileOrganizer
pyinstaller FileOrganizer.spec --noconfirm

# 准备发布
cp dist/FileOrganizer.exe release/
cp setup.bat release/
powershell -Command "Compress-Archive -Path release\* -DestinationPath release\FileOrganizer-测试版.zip -Force"

# 发布文件：release/FileOrganizer-测试版.zip（35MB）
```

### 本地测试

```powershell
# 源代码运行
pythonw main.py          # 托盘模式
python cli.py            # 命令行模式

# EXE 测试
dist/FileOrganizer.exe   # 双击或命令行启动
```
