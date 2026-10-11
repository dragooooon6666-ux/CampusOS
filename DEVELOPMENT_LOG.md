# CampusOS 开发日志

## v0.1.3 (2026-10-11)

### 修复（P0 数据安全）

- **打包版用户数据每次重启清零**：PyInstaller onefile 把程序解压到 `%TEMP%\_MEIxxxx`，而 `database.py` / `archiver.py` / `routes/files.py` / `config.py` 用 `Path(__file__)` 定位用户数据，导致归档文件和数据库都写进临时目录，程序退出即丢。
  修复：新增 `backend/paths.py` 的 `get_base_dir()`，打包后返回 exe 所在目录、开发时返回项目根目录；上述文件统一改走该函数。
- **`CampusOS.spec` 误把 `input/`、`data/` 打进 exe**（原本含 963MB 测试文件）。现只打包程序自带资源。
- **`scripts/pre_build_check.py` 新增第 5 项检查**：防止再次把用户数据打进 exe。
- 实测：包体 **981MB → 41MB**；上传 → 关闭 → 重启后数据与文件均保留。

### 新增（无 Key 也能用）

- **规则分类引擎** `backend/utils/rule_classifier.py`：不依赖 AI Key 完成基础分类。四层判定：文件族（按扩展名）→ 文种结尾 → 关键词包含 → 按扩展名兜底并标记 `needs_ai=True`。
- `archiver` 在 `analyze_file` 返回 None 时自动走规则分类，因此**没配 Key 也能正常归档**。
- **降级/升级闭环**：`archiver.reanalyze_file()` + `POST /api/files/reanalyze` + `GET /api/files/stats/pending`；数据库 `ai_analyzed` 列标记是否经过 AI；设置页新增「用 AI 重新分类」按钮，配好 Key 后可一键把粗分类升级成精分类。
- **隐私过滤** `file_analyzer._is_sensitive()`：通讯录/简历/收集表/签到表/统计表，或文件名含电话/手机/身份证/学号/联系方式/花名册的，只把文件名发给 AI，不读内容。

### 修复（分类准确度）

- 文件族把「内容类型」与「文件格式」混为一谈，导致 Word 做的表格分不出来。已把 `统计表/签到表/预算表/排班表/物资清单` 等词移到 `COMMON_RULES`，删除 `SHEET_RULES`。
- 文件名结尾的括号标注（如 `XX策划案（就业服务部）`）挡住文种匹配。已在 `_clean_stem()` 里剥掉结尾括号。
- 新增防误判的 `_is_descriptive()`：以「说明/指南/规范/制度/办法/流程」结尾的文件是在描述某件事，不做全文关键词匹配。

### 工程

- **版本号统一为单一来源** `backend/version.py` 的 `__version__`，`main.py` 与 `/api/health` 均从此读取。
  （此前源码自报 `0.1.0`、NSIS 里写 `0.1.2`、setup.bat 写 `0.1.0`，三处不一致。）
- **`release/CampusOS/setup.bat` 行尾修复**：原为 UTF-8 + LF，cmd.exe 解析时会吃掉含中文行的行首，报「不是内部或外部命令」（实测 5 处报错）。改为 **UTF-8 + CRLF** 后 0 报错。
  新增 `scripts/normalize_setup_bat.py` 做规范化（幂等，可重复运行）。
  ⚠️ **注意：元凶是 LF 换行，不是编码。切勿转成 GBK——实测 GBK + CRLF 报错更多（8 处）。**
- **`CampusOS.spec` 补充 hiddenimports**：`backend.version`、`backend.utils.rule_classifier`（后者在函数内部 import，显式列出避免漏打包）。

### 验证数据

- 规则引擎单测：**47/47 通过**
- 端到端归档：**14/14 通过**
- 真实文件实测（桌面「工作留痕」1269 个文件）：**规则能给出具体分类 752 个 = 59%**（确定 711 / 较确定 41 / 仍需 AI 517 = 41%）
  ⚠️ **47/47 的自建用例通过率不能当验收依据**——修 bug 前拿真实数据跑只有 37%。

---

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
