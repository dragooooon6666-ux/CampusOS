# CampusOS 开发日志

## v0.1.2 (2026-06-14)

### 修复

- **isatty 启动崩溃**：PyInstaller `console=False` 打包后 `sys.stdout`/`sys.stderr` 为 `None`，uvicorn 日志初始化调用 `.isatty()` 崩溃。修复：`launcher.py` 在 `import uvicorn` 前检查并重定向到 `data/campusos.log`
- **端口冲突静默失败**：8000 端口已被占用时 exe 无任何提示。修复：启动前检测已有实例，有则直接打开浏览器
- **写作中心兼容性**：旧版浏览器访问写作中心报 `SyntaxError: Unexpected reserved word`。修复：将 `async function loadForm()` / `async function loadTemplates()` 改为箭头函数形式

### 仓库整理

- 删除旧原型 `FileOrganizer/`
- 删除开发配置 `.claude/` `.superpowers/`
- 添加项目说明书 `README.md`
- 添加 `.gitignore` 排除规则

---

## v0.1.1 (2026-06-10)

### 修复

- isatty 启动崩溃（同 v0.1.2 第一条，此版本仅含部分修复）

---

## v0.1.0 (2026-06-10)

### 初始内测版

- 智能文件中心：22 种文档类型 AI 识别，6 大分类归档，压缩包解压，文件夹递归
- AI 公文写作中心：11 种公文类型，引导式表单 + 模板驱动，逐段编辑/重生成，导出 Word
- 项目管理中心：看板 + 创建 + 文件关联 + AI 自动匹配 + 导出 zip
- 设置页：AI 双模型配置（DeepSeek/Kimi）、监控源管理、组织架构管理
- PyInstaller 打包 + NSIS 安装向导
- 宣传页 v2：8 页 scroll-snap，GitHub Pages 部署

### 技术栈

- FastAPI + SQLite + 原生 ES Modules
- OKLCH 色彩系统（Restrained 策略）
- DeepSeek / Kimi 双模型后端代理
