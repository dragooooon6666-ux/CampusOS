# CampusOS — 校园事务智能操作系统

AI 驱动的高校学生组织事务管理系统。让每个学生干部都有一个数字办公室。

## 三大核心功能

### 📁 智能文件中心
拖拽上传，AI 自动识别 22 种文档类型，按 6 大分类归档。

- 支持 Word、PDF、Excel、PPT、图片、视频
- 压缩包自动解压，文件夹递归扫描
- 按 **活动全流程 / 办公文书 / 个人信息 / 数据与表单 / 媒体文件 / 其他** 六大类自动整理
- 手动改分类、打开文件位置、关联到项目

### ✍️ AI 公文写作中心
不是通用聊天机器人。选择文档类型、填写关键信息，一键生成符合学院规范的公文。

- 11 种公文类型：新闻稿、活动总结、会议纪要、通知、请示、申请书、发言稿、工作汇报、述职报告、评优材料、项目申报书
- 引导式填写 + 模板驱动，两种模式切换
- 生成后可逐段编辑、逐段重新生成
- 一键导出 Word 文档

### 🗂️ 项目管理中心
以项目为中心组织文件。策划书、新闻稿、总结、照片自动关联。

- 创建项目，设置状态、负责人、日期
- AI 自动匹配文件到项目
- 项目档案一键预览
- 导出项目 zip 包（含全部关联文件和文档）

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python · FastAPI · SQLite · uvicorn |
| 前端 | 原生 ES Modules（无框架）· OKLCH 色彩系统 |
| AI | DeepSeek / Kimi 双模型 · 后端代理（前端不持 Key） |
| 打包 | PyInstaller · NSIS 安装向导 |

## 安装使用

### 方式一：安装包（推荐）

从 [Releases](https://github.com/dragooooon6666-ux/CampusOS/releases) 下载最新版安装程序：

- `CampusOS-Setup-vX.X.X.exe` — 安装向导，选路径 + 桌面快捷方式 + 开始菜单
- 安装后双击桌面图标启动，浏览器自动打开 `http://localhost:8000`

### 方式二：免安装版

下载 `CampusOS-vX.X.X.zip`，解压后双击 `CampusOS.exe`。

### 首次配置

1. 打开后进入**设置页**
2. 填入 DeepSeek API Key（去 [platform.deepseek.com](https://platform.deepseek.com/api_keys) 免费获取）
3. 点击「测试连接」确认可用
4. 开始使用

## 开发环境

```bash
# 安装依赖
pip install fastapi uvicorn[standard] watchdog python-docx PyPDF2 openpyxl python-pptx

# 配置 API Key
# 编辑 config/settings.json，填入 deepseek key

# 启动
python -m uvicorn backend.main:app --reload
# 或双击 start.bat
```

浏览器访问 `http://localhost:8000`。

## 项目结构

```
CampusOS/
├── backend/               # FastAPI 后端
│   ├── routes/            # API 路由
│   ├── services/          # 核心服务（分析/归档/写作/监控）
│   └── utils/             # 工具（内容提取/命名）
├── frontend/              # 原生 JS 前端
│   ├── js/pages/          # 页面模块
│   └── css/               # 样式
├── landing/               # 宣传页（GitHub Pages）
├── launcher.py            # PyInstaller 启动入口
├── PRODUCT.md             # 产品战略文档
└── start.bat              # 开发环境一键启动
```

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.2 | 2026-06-14 | 修复启动崩溃 + 端口冲突 + 写作中心兼容性 |
| v0.1.1 | 2026-06-10 | 紧急修复 isatty 崩溃（不完全） |
| v0.1.0 | 2026-06-10 | 初始内测版 |

## 联系

QQ：840984487

---

*CampusOS — 文件不再散落，经验不再归零。*
