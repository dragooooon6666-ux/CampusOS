# CampusOS 设计文档

> 校园事务智能操作系统 — AI 驱动的高校学生组织事务管理
>
> 日期：2026-06-07 | 版本：v1.0 | 阶段：设计确认

---

## 一、产品定位

CampusOS 不是网盘、不是知识库、不是 AI 聊天工具。它让一个普通学生干部拥有一个"数字办公室"，帮助完成文件管理、材料归档、公文写作、活动管理、资料沉淀和历史项目复用。

最终形态：**高校组织记忆系统（Organizational Memory）**。

### MVP 范围

| 包含 | 排除 |
|------|------|
| 文件自动整理 | 用户系统 |
| AI 文件理解 | 多人协作 |
| 项目归档 | 云同步 |
| 写作中心 | 在线部署 |
| 模板系统 | 权限管理 |
| 本地数据库 | — |
| 项目档案页 | — |

---

## 二、系统架构

### 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端框架 | **FastAPI** | Python，REST API，自带 Swagger 文档 |
| 数据库 | **SQLite** | 本地单文件，零配置 |
| 前端 | **原生 JS ES 模块** | 无框架，无构建步骤，hash 路由 |
| AI | **DeepSeek API** | 兼容 OpenAI 接口，文件分析 + 公文生成 |
| 文件监控 | **watchdog** | 多源目录监控 |
| 内容提取 | python-docx, PyPDF2, openpyxl, python-pptx | 文档内容提取 |

### 项目结构

```
CampusOS/
├── backend/
│   ├── main.py               FastAPI 入口 + 静态文件挂载
│   ├── database.py            SQLite 连接 + 表初始化
│   ├── config.py              配置管理（复用+扩展）
│   ├── models/                Pydantic 模型
│   ├── services/              业务逻辑（不依赖 Web）
│   ├── routes/                API 路由（薄层）
│   └── utils/                 工具（复用现有 extractor/naming/dedupe）
├── frontend/
│   ├── index.html             SPA 外壳
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js             API 封装
│   │   ├── router.js          Hash 路由
│   │   ├── pages/             页面模块
│   │   └── components/        可复用组件
│   └── assets/
├── data/campusos.db           SQLite 数据库
├── input/                     默认监控源
├── output/                    归档输出
├── templates/                 文档模板 (.json)
└── requirements.txt
```

### 设计原则

1. **文件只是素材，成果才是目标** — 系统以项目为中心组织信息
2. **模块隔离** — 每个模块可独立理解、测试、替换
3. **AI 增强而非替代** — AI 辅助决策，用户最终确认
4. **渐进复杂度** — 默认简单，高级功能可选

---

## 三、数据库设计

### 表结构

```sql
-- 组织/部门
organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,           -- 团委/学生会/就业服务部...
    icon TEXT DEFAULT '📋',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 组织下的子分类（二级树形）
folders (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,           -- 迎新晚会/春季招聘会...
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 文件记录
files (
    id INTEGER PRIMARY KEY,
    original_name TEXT NOT NULL,  -- 原始文件名
    stored_name TEXT NOT NULL,    -- 归档后的文件名
    original_path TEXT,           -- 原始路径
    stored_path TEXT NOT NULL,    -- 归档路径
    extension TEXT,
    size_bytes INTEGER,
    doc_type TEXT,                -- AI 识别的文档类型
    title TEXT,                   -- AI 提取的标题
    doc_date TEXT,                -- AI 提取的日期
    author TEXT,                  -- AI 提取的作者/组织
    content_hash TEXT,            -- MD5 去重用
    ai_analyzed BOOLEAN DEFAULT 0,
    folder_id INTEGER REFERENCES folders(id),
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 项目（手动创建）
projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active', -- active/completed/archived
    leader TEXT,                  -- 负责人
    start_date TEXT,
    end_date TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 项目↔文件关联
project_files (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    match_method TEXT DEFAULT 'ai',  -- ai/manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_id)
)

-- 生成的文档
documents (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    doc_type TEXT NOT NULL,       -- 新闻稿/总结/纪要...
    title TEXT,
    content TEXT,                 -- Markdown
    template_id INTEGER REFERENCES templates(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 文档模板
templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    style TEXT DEFAULT '通用',
    sections JSON NOT NULL,       -- [{key, label, ai_role}]
    formatting JSON,              -- {title_align, title_bold...}
    is_builtin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 监控源
monitor_sources (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    label TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- 系统设置 (KV)
settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
```

---

## 四、模块详细设计

### 模块 1：智能文件中心（Phase 1，第 1-2 周）

#### 4.1.1 多源文件监控

- 默认监控源：`input/`（始终启用）、桌面、下载文件夹
- 用户可添加自定义文件夹路径
- 每个监控源独立 watchdog Observer，支持热添加/移除
- 检测到新文件 → 等待稳定（3 秒大小无变化）→ 加入处理队列

#### 4.1.2 AI 文件分析

**支持内容提取的类型：**

| 类型 | 扩展名 | 库 |
|------|--------|-----|
| Word 文稿 | .docx .doc | python-docx |
| PDF | .pdf | PyPDF2 |
| Excel 表格 | .xlsx .xls .csv | openpyxl |
| PowerPoint | .pptx | python-pptx |
| 纯文本 | .txt .md .log | 直接读取 |

**不送 AI 的类型**（走规则分类）：图片、视频、音频、压缩包、可执行文件。

**文档类型分类（21 类）：**

```
简历、作业、论文、策划案、方案、议程、会议纪要、活动总结、
报告、申请书、通知、证明、笔记、
签到表、预算表、物资清单、统计表、通讯录、排班表、其他表格、
其他文档
```

**AI 分析策略优化：**
- Temperature：0.5（分类任务最佳平衡点）
- 取消 `response_format: json_object`，改用自然推理 + 标记格式
- 硬规则："文件名包含明确类型关键词时，以文件名为准"
- 内容提取：前 500-800 字（标题区）+ 末尾 4 行（落款区）

#### 4.1.3 归档引擎

```
归档路径格式：
  output/{组织名}/{子分类}/{日期}-{文档类型}-{标题}.{扩展名}

  示例：
  output/学生会/春季招聘会/2026年3月15日-活动总结-春季招聘会圆满举行.docx
```

#### 4.1.4 前端页面

- **文件中心页**：左侧组织树（可折叠，右键编辑）+ 右侧文件网格/列表
- **设置页**：监控源管理 + 组织层级管理 + AI 配置

---

### 模块 2：AI 公文写作中心（Phase 2，第 3 周）

#### 4.2.1 交互模式

默认**引导式**，高级可切换**模板驱动**，共享同一模板引擎。

```
引导式流程：
  选择文档类型 → 填写关键信息 → 选择模板 → AI 生成 → 编辑确认 → 保存归档

文档类型支持：
  新闻稿、活动总结、会议纪要、通知、请示、申请书、
  发言稿、工作汇报、评优材料、述职报告、项目申报书
```

#### 4.2.2 模板系统

模板存储为 JSON：

```json
{
  "name": "学院标准新闻稿",
  "doc_type": "新闻稿",
  "style": "正式",
  "sections": [
    {"key": "title", "label": "标题", "ai_role": "提炼核心事件"},
    {"key": "lead", "label": "导语", "ai_role": "5W1H概括"},
    {"key": "process", "label": "过程", "ai_role": "按时间线展开"},
    {"key": "outcome", "label": "成果", "ai_role": "提炼关键成果"},
    {"key": "outlook", "label": "展望", "ai_role": "1-2句致谢或展望"}
  ]
}
```

- 内置 4 套通用模板
- 支持从已有文档导入模板（上传 → AI 提取结构 → 存为模板）
- 模板可增删改

#### 4.2.3 写作引擎

```
services/writing_engine.py
├── get_form_fields(doc_type)       → 返回动态表单字段定义
├── generate_document(params)       → 组装 prompt → 调用 AI → 返回全文
├── regenerate_section(...)         → 逐段重新生成
├── import_template(file)           → 从文档提取模板结构
└── render_document(content, tmpl)  → 按模板格式化输出 Markdown
```

---

### 模块 3：项目管理中心（Phase 3，第 4 周）

#### 4.3.1 项目首页（系统主页）

打开 `localhost` 的第一屏，卡片式展示所有项目。包含：状态标签、负责人、时间范围、关联文件数。

#### 4.3.2 项目详情页

- 关联文件列表（支持手动添加/解除关联）
- 生成文档列表（可从此页面直接打开写作中心）
- 项目档案预览（一键导出）

#### 4.3.3 AI 自动文件匹配

```
新文件归档 → 提取关键词 → 计算与现有项目的相似度
  > 70%：自动关联
  40-70%：标记"待归类"
  < 40%：不关联
```

用户可在文件中心手动归类。

#### 4.3.4 项目档案

一键生成项目总结，包含：项目名称、负责人、起止时间、成果摘要（AI 从关联文件自动提取）、材料清单。

---

## 五、API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/files` | 文件列表（筛选：org_id, folder_id, doc_type, search） |
| GET | `/api/files/{id}` | 文件详情 |
| POST | `/api/files/scan` | 手动触发全量扫描 |
| DELETE | `/api/files/{id}` | 删除文件 |
| GET/POST/PUT/DELETE | `/api/orgs` | 组织 CRUD |
| GET/POST/PUT/DELETE | `/api/orgs/{id}/folders` | 子分类 CRUD |
| GET/POST/PUT/DELETE | `/api/projects` | 项目 CRUD |
| GET | `/api/projects/{id}` | 项目详情（含关联文件+文档） |
| POST | `/api/projects/{id}/link-file` | 手动关联文件到项目 |
| DELETE | `/api/projects/{id}/link-file/{file_id}` | 解除关联 |
| POST | `/api/writing/generate` | AI 生成文档 |
| POST | `/api/writing/regenerate` | 重新生成某段落 |
| POST | `/api/templates/import` | 从文件导入模板 |
| GET/POST/PUT/DELETE | `/api/templates` | 模板 CRUD |
| GET/POST/DELETE | `/api/monitor-sources` | 监控源管理 |
| GET/PUT | `/api/settings` | 系统设置 |
| GET | `/api/stats` | 首页统计数据 |

---

## 六、视觉设计

### 风格方向

**极简专业风**（蓝白灰基调，大留白），支持一键切换浅色/深色模式。

### 布局

- 左侧固定侧边栏（导航：项目看板、文件中心、写作中心、设置）
- 右侧内容区（自适应宽度，最大 1200px 居中）
- 卡片式组件，8px 圆角，浅阴影

### 色彩

| 用途 | 浅色模式 | 深色模式 |
|------|----------|----------|
| 背景 | `#ffffff` | `#0f172a` |
| 卡片 | `#f9fafb` | `#1e293b` |
| 主色 | `#3b82f6` | `#6366f1` |
| 文字 | `#1f2937` | `#f1f5f9` |
| 辅助文字 | `#6b7280` | `#94a3b8` |
| 成功 | `#10b981` | `#34d399` |
| 警告 | `#f59e0b` | `#fbbf24` |

---

## 七、开发策略

### 阶段划分

| 阶段 | 周期 | 内容 |
|------|------|------|
| Phase 1 | 第 1-2 周 | 智能文件中心（多源监控 + AI 分析 + 组织归档） |
| Phase 2 | 第 3 周 | AI 公文写作中心（引导式写作 + 模板系统） |
| Phase 3 | 第 4 周 | 项目管理中心（项目看板 + AI 关联 + 项目档案） |

### 可用复用资产

| 现有代码 | 复用方式 |
|----------|----------|
| `content_extractor.py` | 扩展 + pptx 支持，移入 `backend/utils/` |
| `ai_naming.py` | 重构为 `file_analyzer.py`，增强 prompt + 表格分类 |
| `naming.py` | 拆分为 `backend/utils/naming.py`（规则命名）+ 归档路径生成 |
| `organizer.py` | 拆分为 `file_watcher.py` + `archiver.py` |
| `config.py` | 扩展为 `backend/config.py`，增加新配置项 |
| `dedupe.py` | 直接移入 `backend/utils/` |

### 新增依赖

```
fastapi
uvicorn[standard]
watchdog
python-pptx          ← 新增：PPT 内容提取
```

---

## 八、风险与注意事项

1. **AI 分类精度**：表格类文档内容稀疏，21 类分类增加了 AI 负担。需持续调优 prompt，必要时对表格类使用独立分类 prompt。
2. **文件重名处理**：多源监控下不同来源可能产生重名文件，沿用现有 `(1)(2)(3)` 策略。
3. **大文件处理**：超过 50MB 的文件跳过内容提取，仅按文件名+扩展名规则处理。
4. **模板兼容性**：用户导入模板时，docx/pdf 格式多样，AI 提取结构可能不准，需提供手动编辑入口。
