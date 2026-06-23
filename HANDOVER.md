# CampusOS 项目交接文档

## 项目简介

CampusOS（校园事务智能操作系统）— AI 驱动的高校学生组织事务管理系统。  
目标用户：学生会、团委、社团等学生组织干部。  
核心价值：文件不再散落，经验不再归零。

## 当前版本

**v0.1.2** — 内测修复版  
GitHub：https://github.com/dragooooon6666-ux/CampusOS  
Release：https://github.com/dragooooon6666-ux/CampusOS/releases  
宣传页：https://dragooooon6666-ux.github.io/CampusOS

## 架构

```
前端：原生 ES Modules（无框架）
后端：FastAPI + SQLite + uvicorn
AI：DeepSeek / Kimi 双模型，后端代理
打包：PyInstaller + NSIS 安装向导
色彩：OKLCH Restrained（专业蓝白灰 #2563eb）
```

## 三大功能模块（全部完成）

1. **智能文件中心** — 22 种文档 AI 分类，6 大组归档，压缩包解压，文件夹递归
2. **AI 公文写作中心** — 11 种公文类型，引导式表单 + 模板驱动，逐段编辑/重生成，导出 Word
3. **项目管理中心** — 看板 + 创建 + 文件关联 + AI 匹配 + 导出 zip

## 开发进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1 文件中心 | ✅ 完成 | 包含监控源、归档引擎、文件列表、详情面板 |
| Phase 2 写作中心 | ✅ 完成 | 11 种公文类型、模板系统、导出 docx |
| Phase 3 项目中心 | ✅ 完成 | 看板、关联、档案、导出 |
| 打包分发 | ✅ 完成 | PyInstaller + NSIS，v0.1.2 已发布 |
| 宣传页 v3 | ✅ 完成 | 飞书风格，8 页 scroll-snap |
| 宣传视频 | ✅ 完成 | 30 秒 1920×1080 MP4 |
| 内测 | 🔜 进行中 | 需收集 3-5 人反馈 |

## 关键文件路径

```
d:\ai-workspace\test-project\
├── backend/               # FastAPI 后端
│   ├── routes/            # API 路由（files, writing, projects, settings）
│   ├── services/          # 核心服务（analyzer, archiver, watcher, writing_engine）
│   ├── utils/             # 工具（content_extractor, naming）
│   ├── config.py          # 配置管理（AI 模型、API Key）
│   └── database.py        # SQLite 数据库
├── frontend/
│   ├── js/pages/          # 页面模块（ES modules）
│   │   ├── file-center.js
│   │   ├── writing-center.js
│   │   ├── projects-page.js
│   │   ├── project-detail.js
│   │   ├── settings-page.js
│   │   └── dashboard.js
│   ├── js/router.js       # Hash 路由
│   ├── js/api.js          # fetch 封装 + Toast
│   ├── css/base.css       # 基础样式 + 侧边栏
│   └── css/tokens.css     # OKLCH 设计令牌
├── landing/               # 宣传页源文件
│   └── index.html         # 修改改这个，然后 cp 到根目录
├── promo/                 # 宣传视频
│   ├── video-animation.html  # 动画源码
│   ├── record_video.py       # Playwright 录制脚本
│   └── campusos-promo.mp4    # 成品视频
├── release/               # 分发包（不提交 git）
│   ├── CampusOS/          # 免安装版内容
│   ├── CampusOS-Setup-vX.X.X.exe  # NSIS 安装向导
│   ├── CampusOS-vX.X.X.zip        # 免安装版
│   └── setup.nsi          # NSIS 安装脚本
├── scripts/
│   └── pre_build_check.py # 打包前密钥泄露检查
├── config/
│   ├── settings.json      # 开发用配置（已 gitignore，含 API Key）
│   └── settings.example.json  # 空白模板（随 exe 分发）
├── CampusOS.spec          # PyInstaller 打包配置
├── launcher.py            # exe 启动入口
├── start.bat              # 开发环境一键启动
├── README.md              # 项目说明书
├── DEVELOPMENT_LOG.md     # 开发日志
├── PRODUCT.md             # 产品战略
└── HANDOVER.md            # 本文件
```

## ⚠️ 开发注意事项

### 1. API Key 安全（最重要！）
- `config/settings.json` 含真实 Key，**已 gitignore，绝不能打包进 exe**
- 打包前必须运行：`python scripts/pre_build_check.py`
- PyInstaller spec 只打包 `settings.example.json`（空 Key 模板）
- 首次运行时 launcher.py 自动复制 example → settings.json

### 2. 打包流程
```bash
# 1. 安全检查
python scripts/pre_build_check.py

# 2. 构建 exe
rm -rf dist build
python -m PyInstaller CampusOS.spec --noconfirm --clean

# 3. 更新 release
cp dist/CampusOS.exe release/CampusOS/
cd release && makensis setup.nsi

# 4. 创建 GitHub Release
gh release create vX.X.X --title "..." --notes "..." release/CampusOS-Setup-vX.X.X.exe release/CampusOS-vX.X.X.zip
```

### 3. 写作中心语法问题
- 旧版浏览器不支持块级 `async function` 声明
- 所有 async 函数必须用箭头函数形式：`const fn = async () => {}`
- `renderEditor` 函数也必须是 async（其内部使用了 await）

### 4. 缓存问题
- 修改 JS 后需更新 `app.js` 和 `index.html` 中的版本号 `?v=N`
- 用无痕窗口测试避免缓存干扰

### 5. 宣传页
- 修改 `landing/index.html`，然后 `cp landing/index.html index.html` 同步到根目录
- 两个文件必须保持一致

## 已知 Bug 修复记录

| Bug | 修复 | 版本 |
|-----|------|------|
| isatty 启动崩溃 | launcher.py 中处理 stdout/stderr=None | v0.1.1 |
| 端口冲突静默失败 | 启动前检测已有实例 | v0.1.1 |
| 写作中心 SyntaxError | async function → 箭头函数 | v0.1.2 |
| API Key 打包泄露 | 分离 settings.json + 安全检查脚本 | v0.1.2 |

## 常用 Skills

| Skill | 用途 |
|-------|------|
| `impeccable` | 前端设计（已在项目中安装参考文件） |
| `brainstorming` | 需求澄清 + 方案设计 |
| `playwright-cli` | 浏览器自动化（视频录制、页面测试） |
| `markitdown` | 读取 Word/Excel/PPT 文件内容 |

## 项目必须遵守的规则

1. 不做用户系统、多人协作、云同步、权限管理
2. 不做移动端适配（桌面优先）
3. 不引入前端框架（保持原生 ES Modules）
4. AI Key 永远不打包进 exe
5. 修改前后端代码后必须测试
6. 打包前必须运行 pre_build_check.py
