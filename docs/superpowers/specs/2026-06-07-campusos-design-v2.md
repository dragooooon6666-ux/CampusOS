# CampusOS 设计文档 v2

> 校园事务智能操作系统
>
> 日期：2026-06-07 | 基于 impeccable 设计框架 | 阶段：设计确认

---

## 一、产品概述

### 定位

CampusOS 不是网盘，不是 AI 聊天工具，不是知识库产品。它让一个普通学生干部拥有一个"数字办公室"。

最终形态：**高校组织记忆系统（Organizational Memory）**。

### 用户画像

学生会成员、团委干事、社团负责人、党支部委员、学院办公室助理。不是专业文秘，手上同时处理多个活动，文件散落在微信/QQ/桌面/U盘各处。

### 核心任务

1. **找到文件** — 自动整理散落的文档，按组织和项目归档
2. **写出公文** — 引导式生成符合学院规范的新闻稿、总结、纪要
3. **传承经验** — 形成组织记忆，换届后不需要从零开始

---

## 二、设计系统

### 2.1 色彩

**策略**：Restrained（产品默认）— 调性中性 + 单色调强调 ≤10%。

**场景句**：学生在办公室日光灯下、或宿舍台灯前，需要快速完成文书工作。界面应当安静、不喧哗，让用户专注于内容而非工具。

| 角色 | 色值（OKLCH） | 用途 |
|------|---------------|------|
| `--bg` | `oklch(1 0 0)` | 页面背景 — 纯白，不加热度 |
| `--surface` | `oklch(0.97 0.005 250)` | 卡片、面板 — 微弱蓝灰 |
| `--primary` | `oklch(0.55 0.18 255)` | 主操作按钮、选中态、链接 |
| `--primary-hover` | `oklch(0.48 0.18 255)` | 主按钮悬停 |
| `--ink` | `oklch(0.15 0.01 255)` | 正文 — 与 bg 对比度 ≥7:1 |
| `--muted` | `oklch(0.55 0.01 255)` | 辅助文字 — 对比度 ≥3.5:1 |
| `--accent` | `oklch(0.62 0.16 170)` | 成功、确认、积极状态 |
| `--warning` | `oklch(0.72 0.14 85)` | 警告状态 |
| `--error` | `oklch(0.50 0.20 25)` | 错误、危险操作 |
| `--border` | `oklch(0.90 0.005 250)` | 分割线、边框 |

深色模式：
| 角色 | 色值（OKLCH） |
|------|---------------|
| `--bg-dark` | `oklch(0.12 0 0)` |
| `--surface-dark` | `oklch(0.18 0.008 250)` |
| `--ink-dark` | `oklch(0.92 0 0)` |
| `--muted-dark` | `oklch(0.60 0.01 250)` |

### 2.2 字体

**单字体系统**（产品 UI 不需要 display/body 配对）：

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
             "Microsoft YaHei", "Helvetica Neue", sans-serif;
```

层级（固定 rem，不 clamp）：

| 用途 | 大小 | 字重 |
|------|------|------|
| 页面标题 | 1.5rem | 600 |
| 区块标题 | 1.125rem | 600 |
| 正文 | 0.9375rem | 400 |
| 辅助文字 | 0.8125rem | 400 |
| 标签/徽章 | 0.75rem | 500 |

正文行宽上限 65-75ch。表格和密集数据可到 120ch+。

### 2.3 间距

基于 4px 网格，使用 `gap` + `padding` 而非固定 margin：

| 级别 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 紧密关联元素间 |
| sm | 8px | 组件内部元素间 |
| md | 16px | 卡片内边距、列表项间距 |
| lg | 24px | 区块间距 |
| xl | 32px | 页面级分区 |

### 2.4 动效

- 过渡时长 150-250ms，缓出曲线 `cubic-bezier(0.16, 1, 0.3, 1)`
- 动效仅传达状态变化（hover、focus、选中、加载、通知），不装饰
- 不编排页面加载序列
- 默认遵守 `prefers-reduced-motion: reduce`

### 2.5 圆角与阴影

```
--radius-sm: 4px;    /* 输入框、按钮 */
--radius-md: 8px;    /* 卡片 */
--radius-lg: 12px;   /* 模态框 */

--shadow-card: 0 1px 3px oklch(0 0 0 / 0.06), 0 1px 2px oklch(0 0 0 / 0.04);
--shadow-modal: 0 20px 60px oklch(0 0 0 / 0.15);
```

### 2.6 绝对禁令（impeccable）

- ❌ 侧边栏彩色竖线装饰（border-left > 1px）
- ❌ 渐变文字（background-clip: text）
- ❌ 玻璃态卡片作为默认风格
- ❌ 大数字 + 小标签 + 渐变的 hero-metric 模板
- ❌ 完全相同的图标+标题+文字卡片网格
- ❌ 每个区块上方的全大写小字 eyebrow（"ABOUT""FEATURES"）
- ❌ 编号分区标记（01/02/03）作为默认脚手架
- ❌ 展示字体用于 UI 标签、按钮、数据
- ❌ 跨页面不一致的组件词汇
- ❌ 装饰性动画

---

## 三、系统架构

### 3.1 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | **FastAPI** (Python 3.11+) | REST API，Swagger 文档 |
| 数据库 | **SQLite** | 单文件零配置 |
| 前端 | **原生 JS ES 模块** | 无框架无构建，hash 路由 |
| 文件监控 | **watchdog** | 多源目录监控 |
| 内容提取 | python-docx, PyPDF2, openpyxl, python-pptx | 文档解析 |
| AI 服务 | **双模型架构** | DeepSeek + Kimi |

### 3.2 AI 双模型架构

系统同时支持 DeepSeek 和 Kimi（均兼容 OpenAI Chat Completions 接口）。

#### 模型配置

```json
{
  "ai": {
    "active_provider": "deepseek",
    "providers": {
      "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "sk-...",
        "key_source": "config"
      },
      "kimi": {
        "label": "Kimi (月之暗面)",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "api_key": "",
        "key_source": "env"
      }
    }
  }
}
```

#### API Key 管理

| 来源 | 优先级 | 说明 |
|------|--------|------|
| 环境变量 | 高 | `DEEPSEEK_API_KEY` / `MOONSHOT_API_KEY` / `AI_API_KEY` |
| 配置文件 | 中 | `config/settings.json`，通过设置 UI 填写 |
| 运行时输入 | 低 | 设置页面临时填入，不持久化 |

#### 模型切换

- 设置页面一键切换活跃模型
- 切换后所有 AI 功能（文件分析、公文写作）自动使用新模型
- 每个模型独立保存 API Key，互不干扰
- 模型调用失败时提示用户检查 Key 或切换模型

#### API 调用策略（两个模型通用）

| 参数 | 文件分析 | 公文写作 |
|------|----------|----------|
| temperature | 0.5 | 0.7 |
| max_tokens | 300 | 2000 |
| 超时 | 30s | 60s |
| 重试 | 3 次指数退避 | 2 次 |

#### 安全性

- API Key 存储在本地配置文件，不上传任何远程服务
- 前端仅通过后端代理调用 AI（浏览器不直接持有 Key）
- 配置页面 Key 字段脱敏显示（仅显示后 4 位）

### 3.3 项目目录

```
CampusOS/
├── backend/
│   ├── main.py               FastAPI 入口 + 静态文件
│   ├── database.py            SQLite
│   ├── config.py              配置 + AI 多模型管理
│   ├── models/                Pydantic schemas
│   ├── services/              业务逻辑
│   │   ├── file_watcher.py    多源监控
│   │   ├── file_analyzer.py   AI 文件分析
│   │   ├── writing_engine.py  AI 公文写作
│   │   ├── archiver.py        归档引擎
│   │   ├── project_service.py 项目管理 + AI 匹配
│   │   └── template_service.py 模板管理
│   ├── routes/                API 路由
│   │   ├── files.py
│   │   ├── projects.py
│   │   ├── writing.py
│   │   ├── organizations.py
│   │   ├── templates.py
│   │   └── settings.py
│   └── utils/
│       ├── content_extractor.py  （复用+扩展）
│       ├── naming.py             （复用+扩展）
│       └── dedupe.py             （复用）
├── frontend/
│   ├── index.html             SPA 外壳
│   ├── css/
│   │   ├── tokens.css         设计令牌（OKLCH 变量）
│   │   ├── base.css           重置 + 基础排版
│   │   └── components.css     组件样式
│   ├── js/
│   │   ├── app.js             入口 + 状态
│   │   ├── api.js             API 封装
│   │   ├── router.js          Hash 路由
│   │   ├── pages/             页面模块
│   │   └── components/        可复用组件
│   └── assets/
├── data/campusos.db
├── input/
├── output/
├── templates/                 文档模板 .json
└── requirements.txt
```

---

## 四、数据库设计

```sql
organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '📋',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

folders (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

files (
    id INTEGER PRIMARY KEY,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    original_path TEXT,
    stored_path TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER,
    doc_type TEXT,              -- 21类文档类型
    title TEXT,
    doc_date TEXT,
    author TEXT,
    content_hash TEXT,
    ai_provider TEXT,           -- 分析所用的 AI 模型
    ai_analyzed BOOLEAN DEFAULT 0,
    folder_id INTEGER REFERENCES folders(id),
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',  -- active/completed/archived
    leader TEXT,
    start_date TEXT,
    end_date TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

project_files (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    match_method TEXT DEFAULT 'ai',  -- ai/manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_id)
)

documents (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    doc_type TEXT NOT NULL,
    title TEXT,
    content TEXT,               -- Markdown
    ai_provider TEXT,           -- 生成所用的 AI 模型
    template_id INTEGER REFERENCES templates(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    style TEXT DEFAULT '通用',
    sections JSON NOT NULL,     -- [{key, label, ai_role}]
    formatting JSON,
    is_builtin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

monitor_sources (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    label TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
```

---

## 五、模块详细设计

### 模块 1：智能文件中心（Phase 1，第 1-2 周）

#### 5.1.1 多源文件监控

- 默认源：`input/`（始终启用）、桌面、下载文件夹
- 用户可添加/移除/启停自定义路径
- 每源独立 watchdog Observer，支持热变更
- 新文件检测 → 3 秒稳定等待 → 加入处理队列

#### 5.1.2 AI 文件分析

**内容提取覆盖**：

| 类型 | 扩展名 | 库 |
|------|--------|-----|
| Word | .docx .doc | python-docx |
| PDF | .pdf | PyPDF2 |
| Excel | .xlsx .xls .csv | openpyxl |
| PowerPoint | .pptx | python-pptx |
| 纯文本 | .txt .md .log | 直接读取 |

**不送 AI 的类型**：图片、视频、音频、压缩包 → 规则分类。

**21 类文档分类**：

```
简历、作业、论文、策划案、方案、议程、会议纪要、活动总结、
报告、申请书、通知、证明、笔记、
签到表、预算表、物资清单、统计表、通讯录、排班表、其他表格、
其他文档
```

**分析策略**：

| 参数 | 值 |
|------|-----|
| Temperature | 0.5 |
| 内容截取 | 前 500-800 字 + 末尾 4 行 |
| 硬规则 | 文件名含明确关键词时以文件名为准 |
| 格式 | 自然推理 + 标记分隔（不强制 JSON mode） |

**后端 API 代理**：前端不直接持有 API Key，所有 AI 调用通过 `/api/ai/analyze` 代理。Key 仅在后端 `config/settings.json` 中存储。

#### 5.1.3 归档引擎

```
路径：output/{组织}/{子分类}/{日期}-{文档类型}-{标题}.{扩展名}

示例：
  output/学生会/春季招聘会/2026年3月15日-活动总结-春季招聘会圆满举行.docx
```

#### 5.1.4 前端 — 文件中心页面

**布局**：左侧组织树（240px 固定宽度，可折叠） + 右侧文件列表

**组织树**：右键菜单编辑（添加/重命名/删除组织、添加子分类）

**文件列表**：
- 网格视图（默认）或列表视图
- 按组织、子分类、文档类型筛选
- 搜索栏（文件名、内容关键词）
- 手动扫描按钮
- 每个文件卡片：类型图标 + 标题 + 日期 + 组织标签

**状态覆盖**：
| 状态 | 设计 |
|------|------|
| 空（首次使用） | 引导文字 + 快速设置监控源 CTA |
| 加载中 | 骨架卡片（3×2 网格灰色脉冲） |
| 扫描中 | 顶部进度条 + "正在分析 N 个文件..." |
| 错误 | 文件处理失败列表 + 重试/跳过按钮 |
| 大量文件 | 分页加载，每页 50 条 |

### 模块 2：AI 公文写作中心（Phase 2，第 3 周）

#### 5.2.1 引导式写作流程

```
选择文档类型
  → 填写关键信息（动态表单）
  → （可选）关联已有项目 → 自动拉入项目信息
  → 选择模板风格
  → 点击"生成"
  → 右侧编辑区展示初稿
  → 可逐段编辑、重新生成某段、整体重写
  → 保存 → 自动归档到对应项目/组织
```

**支持类型**：新闻稿、活动总结、会议纪要、通知、请示、申请书、发言稿、工作汇报、评优材料、述职报告、项目申报书。

**动态表单示例**（新闻稿）：

| 字段 | 类型 | 说明 |
|------|------|------|
| 活动名称 | text | 必填 |
| 时间 | date | 必填 |
| 地点 | text | 必填 |
| 参与单位 | textarea | 必填 |
| 主要内容 | textarea | 选填，越详细越好 |
| 关联项目 | select | 选填，选后自动填充以上字段 |

#### 5.2.2 模板系统

模板存储为 JSON：

```json
{
  "name": "学院标准新闻稿",
  "doc_type": "新闻稿",
  "style": "正式",
  "sections": [
    {"key": "title", "label": "标题", "ai_role": "提炼核心事件，15字以内"},
    {"key": "lead", "label": "导语", "ai_role": "5W1H概括，2-3句"},
    {"key": "process", "label": "过程", "ai_role": "按时间线展开，突出关键环节"},
    {"key": "outcome", "label": "成果", "ai_role": "提炼关键成果和数据"},
    {"key": "outlook", "label": "展望", "ai_role": "1-2句致谢或展望"}
  ]
}
```

- 内置 4 套模板：新闻稿、活动总结、会议纪要、通知
- 用户从文档导入模板（上传 docx → AI 提取结构 → 存为模板）
- 支持增删改

#### 5.2.3 前端 — 写作中心页面

**布局**：三栏 —
1. 左侧（280px）：文档类型选择 + 表单
2. 中间（flex-1）：Markdown 编辑区
3. 右侧（320px）：模板选择 + 段落操作面板

**状态覆盖**：
| 状态 | 设计 |
|------|------|
| 初始 | 左侧表单就绪，中间显示"选择文档类型开始写作" |
| 生成中 | 编辑区骨架脉冲动画 + "正在生成..." |
| 生成完成 | 内容展示，可编辑 |
| 保存成功 | 轻量 toast "已保存到 {项目名}" |
| 生成失败 | 编辑区内联错误 + 重试按钮 + "切换模型试试"提示 |

### 模块 3：项目管理中心（Phase 3，第 4 周）

#### 5.3.1 首页 — 项目看板

打开 `localhost` 第一屏。卡片网格展示所有项目。

**卡片内容**：项目名 + 状态标签 + 负责人 + 时间范围 + 关联文件/文档计数

**状态标签语义色**：
- 进行中 → `--primary` 浅底色 + `--primary` 文字
- 已完成 → `--accent` 浅底色 + `--accent` 文字
- 筹备中 → `--muted` 浅底色 + `--muted` 文字

**空状态**（0 个项目）：
> "还没有项目
> 创建第一个项目来开始管理你的活动资料。项目会自动关联相关文件，
> 帮你生成新闻稿、总结和汇报材料。"
> [+ 新建项目]

#### 5.3.2 项目详情页

**布局**：
- 顶部：项目信息栏（名称、状态、负责人、时间）
- 标签切换：关联文件 | 生成文档 | 项目档案
- 每个标签下支持搜索和排序

#### 5.3.3 AI 文件自动匹配

```
新文件归档
  → 提取关键词（从标题 + AI 摘要）
  → 查 projects 表，计算余弦相似度
  → >70%：自动关联
  → 40-70%：标记"待归类"
  → <40%：不关联
```

手动归入方式：
- 文件卡片拖拽到侧边栏项目名
- 文件详情页选择"关联到项目"
- 项目详情页"添加文件"

#### 5.3.4 项目档案

一键生成汇总文档，AI 从关联文件中自动摘要：

> 项目名称 / 负责人 / 起止时间 / 成果摘要 / 材料清单

支持导出为 docx。

#### 5.3.5 前端 — 状态覆盖

| 状态 | 设计 |
|------|------|
| 加载 | 骨架卡片（2×N 网格） |
| 空项目列表 | 引导提示 + CTA |
| 空文件关联 | "还没有关联文件" + 快捷操作入口 |
| 匹配待确认 | 通知徽章 + 待归类列表 |
| 错误 | 项目加载失败 + 重试 |

---

## 六、API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/files` | 文件列表（筛选：org, folder, type, search） |
| `GET` | `/api/files/{id}` | 文件详情 |
| `POST` | `/api/files/scan` | 手动触发扫描 |
| `DELETE` | `/api/files/{id}` | 删除文件 |
| `GET/POST/PUT/DELETE` | `/api/orgs` | 组织 CRUD |
| `GET/POST/PUT/DELETE` | `/api/orgs/{id}/folders` | 子分类 CRUD |
| `GET/POST/PUT/DELETE` | `/api/projects` | 项目 CRUD |
| `GET` | `/api/projects/{id}` | 项目详情（含关联文件+文档） |
| `POST` | `/api/projects/{id}/link-file` | 关联文件 |
| `DELETE` | `/api/projects/{id}/link-file/{fid}` | 解除关联 |
| `POST` | `/api/writing/generate` | AI 生成文档 |
| `POST` | `/api/writing/regenerate` | 重新生成段落 |
| `GET/POST/PUT/DELETE` | `/api/templates` | 模板 CRUD |
| `POST` | `/api/templates/import` | 从文件导入模板 |
| `GET/POST/DELETE` | `/api/monitor-sources` | 监控源管理 |
| `GET/PUT` | `/api/settings` | 系统设置 |
| `GET/PUT` | `/api/settings/ai` | AI 模型配置（含 Key 管理） |
| `POST` | `/api/settings/ai/test` | 测试 AI 连接 |
| `GET` | `/api/stats` | 首页统计 |

---

## 七、组件状态规范

每个交互组件必须覆盖以下状态：

| 组件 | 状态 |
|------|------|
| 按钮 | default / hover / focus-visible / active / disabled / loading |
| 输入框 | default / focus / disabled / error / readonly |
| 卡片 | default / hover（文件/项目卡片） |
| 模态框 | 打开动画 / 关闭动画 / 焦点陷阱 / Escape 关闭 / 背景点击关闭 |
| Toast | 信息 / 成功 / 警告 / 错误 + 自动消失（3s）/ 手动关闭 |
| 文件列表 | 空 / 加载 / 有数据 / 错误 |

---

## 八、开发策略

### 阶段

| Phase | 周期 | 内容 |
|-------|------|------|
| 1 | 第 1-2 周 | 智能文件中心（多源监控 + 21类AI分析 + 双模型 + 组织归档） |
| 2 | 第 3 周 | AI 公文写作中心（引导式 + 模板 + 双模型写作） |
| 3 | 第 4 周 | 项目管理中心（看板 + AI 匹配 + 档案生成） |

### 复用资产

| 现有代码 | 改造方向 |
|----------|----------|
| `content_extractor.py` | 加 pptx 支持，移入 `backend/utils/` |
| `ai_naming.py` | 重构为 `file_analyzer.py`，21 类 + 双模型 |
| `naming.py` | 拆为规则命名 + 路径生成工具 |
| `organizer.py` | 拆为 `file_watcher.py` + `archiver.py` |
| `config.py` | 扩展为多模型配置 + API Key 管理 |
| `dedupe.py` | 直接移入 `backend/utils/` |

### 新增依赖

```
fastapi
uvicorn[standard]
watchdog
python-pptx
```

---

## 九、风险与对策

| 风险 | 对策 |
|------|------|
| 21 类分类增加 AI 负担 | 表格类用独立 prompt，非表格类保持原 prompt |
| 双模型 API 格式差异 | 统一 OpenAI 兼容层，差异仅在 base_url + model 名 |
| Key 泄露风险 | 前端不持有 Key，代理调用；配置文件不提交 git |
| 大文件（>50MB）耗时长 | 跳过内容提取，仅规则处理 |
| 模板导入格式多样 | AI 提取 + 手动编辑入口兜底 |
