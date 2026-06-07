# CampusOS 实施计划

> 基于 [设计文档 v2](docs/superpowers/specs/2026-06-07-campusos-design-v2.md)
>
> 周期：4 周 | 策略：先骨架后血肉，每个 Phase 结束时交付可运行版本

---

## Phase 0：项目骨架（2-3 天，穿插在 Phase 1 前期）

### 0.1 目录结构初始化

- 创建 `backend/` 和 `frontend/` 完整目录树
- 从现有 FileOrganizer 迁移可复用代码到 `backend/utils/`

### 0.2 依赖安装

```bash
pip install fastapi uvicorn[standard] watchdog python-docx PyPDF2 openpyxl python-pptx
```

### 0.3 数据库初始化

- [x] `backend/database.py` — SQLite 连接 + 10 张表建表
- [x] 插入默认数据（5 个组织 + 内置 4 个模板 + 默认监控源）

### 0.4 FastAPI 骨架

- [x] `backend/main.py` — FastAPI app + CORS + 静态文件挂载
- [x] 启动脚本：`python -m uvicorn backend.main:app --reload`

### 0.5 前端骨架

- [x] `frontend/index.html` — SPA 外壳（侧边栏 + 内容区）
- [x] `frontend/css/tokens.css` — OKLCH 设计令牌 + 浅色/深色变量
- [x] `frontend/css/base.css` — 重置 + 排版
- [x] `frontend/js/router.js` — hash 路由
- [x] `frontend/js/api.js` — fetch 封装 + 错误处理

---

## Phase 1：智能文件中心（第 1-2 周）

### 第一周：后端核心

#### 1.1 组织管理（day 1）

- [ ] `backend/models/organization.py` — Pydantic schemas
- [ ] `backend/routes/organizations.py` — CRUD API
- [ ] 测试：curl 验证增删改查

#### 1.2 内容提取器扩展（day 1-2）

- [ ] 从现有 `content_extractor.py` 迁移到 `backend/utils/content_extractor.py`
- [ ] 新增 `_extract_pptx()` — python-pptx 读幻灯片文本
- [ ] 新增 `ContentPreview.from_filename()` — 文件名作为强信号

#### 1.3 AI 文件分析引擎（day 2-3）

- [ ] `backend/config.py` — 双模型配置（DeepSeek + Kimi）
  - [ ] `AI_PROVIDERS` 字典
  - [ ] `get_active_provider()` / `switch_provider()`
  - [ ] API Key 管理（env > config > runtime）
- [ ] `backend/services/file_analyzer.py` — 核心分析服务
  - [ ] 21 类文档类型常量
  - [ ] Prompt 模板（system + user，含硬规则）
  - [ ] `_call_ai()` — 统一的 AI 代理调用
  - [ ] `_parse_response()` — 解析 AI 返回
  - [ ] `analyze(file_path)` — 主入口，返回 doc_type/title/date/author
  - [ ] 非文本文件直接返回扩展名分类
  - [ ] 失败回退 V1 规则命名

#### 1.4 多源文件监控（day 3-4）

- [ ] `backend/services/file_watcher.py`
  - [ ] `MonitorManager` 类 — 管理多个 watchdog Observer
  - [ ] `add_source(path, label)` / `remove_source(id)` / `toggle_source(id)`
  - [ ] 启动时从 `monitor_sources` 表加载所有活跃源
  - [ ] 新文件检测 → 3 秒稳定等待 → 入队
- [ ] `backend/models/monitor.py` — Pydantic schemas
- [ ] `backend/routes/monitor.py` — 监控源 CRUD API

#### 1.5 归档引擎（day 4-5）

- [ ] `backend/services/archiver.py`
  - [ ] `archive(file_path)` — 完整归档流程
  - [ ] 路径生成：`output/{org}/{folder}/{date}-{type}-{title}.{ext}`
  - [ ] 写入 `files` 表
  - [ ] 触发项目匹配（暂为占位，Phase 3 激活）
- [ ] `backend/routes/files.py` — 文件列表/详情/删除 API

### 第二周：前端 + 集成

#### 1.6 文件中心前端（day 1-3）

- [ ] `frontend/js/pages/file-center.js`
  - [ ] 组织树组件（递归渲染，展开/折叠，右键菜单）
  - [ ] 文件网格组件（卡片视图）
  - [ ] 筛选栏（组织、子分类、文档类型下拉）
  - [ ] 搜索输入（防抖 300ms）
  - [ ] 空状态、加载骨架、错误状态
- [ ] `frontend/css/components.css`
  - [ ] 组织树样式
  - [ ] 文件卡片样式
  - [ ] 骨架脉冲动画
  - [ ] Toast 通知样式

#### 1.7 设置页面前端（day 3-4）

- [ ] `frontend/js/pages/settings.js`
  - [ ] 监控源管理面板（列表 + 开关 + 添加 + 删除）
  - [ ] 组织层级管理面板（添加/编辑/删除组织 + 子分类）
  - [ ] AI 配置面板（模型选择下拉 + Key 输入框 + 测试连接按钮 + 状态指示）
- [ ] `backend/routes/settings.py` — 设置 CRUD + AI 配置 + 测试连接

#### 1.8 集成 + 调试（day 4-5）

- [ ] 端到端测试：放文件 → 监控 → AI 分析 → 归档 → 前端展示
- [ ] 双模型切换测试（DeepSeek ↔ Kimi）
- [ ] 错误处理验证（网络断开、API Key 无效、大文件、非文本文件）
- [ ] 打包验证（可选：pyinstaller）

---

## Phase 2：AI 公文写作中心（第 3 周）

### 2.1 模板系统（day 1-2）

- [ ] `backend/services/template_service.py`
  - [ ] 内置 4 套模板（新闻稿、活动总结、会议纪要、通知）
  - [ ] CRUD 操作
  - [ ] `import_from_document(file)` — 从 docx 提取模板结构
  - [ ] `get_form_fields(doc_type)` — 返回文档类型对应的表单字段
- [ ] `backend/routes/templates.py`

### 2.2 写作引擎（day 2-3）

- [ ] `backend/services/writing_engine.py`
  - [ ] `generate(params)` — 组装 prompt → 调 AI → 返回 Markdown
  - [ ] `regenerate_section(doc_id, section_key, feedback)` — 重新生成段落
  - [ ] Prompt 模板：文档类型 system prompt + 用户输入 + 模板 sections
  - [ ] 双模型支持（使用当前活跃模型）

### 2.3 写作路由（day 3）

- [ ] `backend/routes/writing.py`
  - [ ] `POST /api/writing/generate`
  - [ ] `POST /api/writing/regenerate`
  - [ ] `GET /api/writing/form-fields/{doc_type}`

### 2.4 写作中心前端（day 3-5）

- [ ] `frontend/js/pages/writing-center.js`
  - [ ] 三栏布局（表单 | 编辑区 | 模板面板）
  - [ ] 文档类型选择器（chips）
  - [ ] 动态表单（根据 doc_type 切换字段）
  - [ ] 项目关联选择器（可选，自动填充）
  - [ ] Markdown 编辑区（contenteditable + 工具栏）
  - [ ] 段落操作面板（逐段重新生成、删除、编辑）
  - [ ] 模板切换 + 预览
  - [ ] 保存按钮 → 写入 documents 表 + 关联项目
- [ ] 状态覆盖：初始引导 / 生成中骨架 / 错误 + 模型切换提示 / 保存成功 toast

---

## Phase 3：项目管理中心（第 4 周）

### 3.1 项目管理后端（day 1-2）

- [ ] `backend/services/project_service.py`
  - [ ] CRUD 操作
  - [ ] `match_file_to_project(file_id)` — AI 关键词匹配
  - [ ] `generate_archive(project_id)` — 生成项目档案 Markdown
  - [ ] `export_archive(project_id)` — 导出 docx
- [ ] `backend/routes/projects.py` — 完整 CRUD + 关联 + 匹配 + 档案

### 3.2 首页看板前端（day 2-3）

- [ ] `frontend/js/pages/dashboard.js`
  - [ ] 统计概览栏（项目数、文件数、文档数）
  - [ ] 项目卡片网格（状态标签语义色）
  - [ ] 新建项目模态框
  - [ ] 搜索 + 状态筛选
  - [ ] 空状态引导
  - [ ] 加载骨架

### 3.3 项目详情页前端（day 3-4）

- [ ] `frontend/js/pages/project-detail.js`
  - [ ] 项目信息栏（可编辑）
  - [ ] 标签切换：关联文件 / 生成文档 / 项目档案
  - [ ] 关联文件列表（拖拽排序 + 解除关联）
  - [ ] 文档列表（点击跳转写作中心编辑）
  - [ ] 项目档案预览 + 导出按钮
  - [ ] "待归类"徽章 + 确认对话框

### 3.4 AI 匹配集成 + 测试（day 4-5）

- [ ] 归档流程集成：文件归档时自动触发项目匹配
- [ ] 前端通知：匹配成功 toast / 待归类 badge
- [ ] 手动归入：文件卡片拖拽（简化版：按钮触发）
- [ ] 端到端流程测试：创建项目 → 放文件 → AI 分析+匹配 → 写文档 → 导出档案

---

## 关键决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 后端框架 | FastAPI | 前后端分离、Swagger、类型安全 |
| 前端框架 | 无（原生 ES 模块） | 轻量、无构建步骤、学习成本零 |
| 数据库 | SQLite | 本地单文件、零运维 |
| AI 架构 | 双模型 + 后端代理 | 安全（前端不持 Key）、灵活切换 |
| 色彩系统 | OKLCH Restrained | 专业不花哨、可访问对比度 |
| 文档模板格式 | JSON | 结构化、可编辑、AI 可操作 |

---

## 每一天结束时应该有的状态

- Day 1: `GET /api/orgs` 返回 JSON，curl 可验证
- Day 2: 放一个 Word 文件到 input，控制台打印 AI 分析结果
- Day 3: 文件在 output 里按组织归档好了
- Day 4: 打开 localhost，侧边栏显示组织树
- Day 5: 文件中心页面可以浏览、筛选、搜索文件
- Week 2: 监控源、设置页面完整可用
- Week 3: 能生成一篇新闻稿并保存
- Week 4: 首页显示项目看板，点击进入详情

---

## 不要做的事（防 scope creep）

- ❌ 用户登录/注册/权限
- ❌ 多设备同步 / 云存储
- ❌ 在线部署 / Docker
- ❌ 移动端适配（桌面优先）
- ❌ 全文搜索（Phase 4）
- ❌ 多人协作
- ❌ 版本历史
- ❌ 邮件/微信通知
