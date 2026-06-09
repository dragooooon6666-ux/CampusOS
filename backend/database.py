"""
SQLite 数据库：连接 + 建表 + 默认数据
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campusos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '📋',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    original_path TEXT,
    stored_path TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER,
    doc_type TEXT,
    title TEXT,
    doc_date TEXT,
    author TEXT,
    content_hash TEXT,
    ai_provider TEXT,
    ai_analyzed INTEGER DEFAULT 0,
    folder_id INTEGER REFERENCES folders(id),
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    leader TEXT,
    icon TEXT DEFAULT '📋',
    start_date TEXT,
    end_date TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    match_method TEXT DEFAULT 'ai',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    doc_type TEXT NOT NULL,
    title TEXT,
    content TEXT,
    ai_provider TEXT,
    template_id INTEGER REFERENCES templates(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    style TEXT DEFAULT '通用',
    sections TEXT NOT NULL,
    formatting TEXT,
    is_builtin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monitor_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    label TEXT,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DEFAULT_ORGS = [
    ("学生会", "📋", 0),
    ("团委", "🏛️", 1),
    ("大学生自律委员会", "🛡️", 2),
]

# 每个组织下的默认子部门（folders）
DEFAULT_FOLDERS = {
    "学生会": ["学习部", "文艺部", "体育部", "社会实践部", "科技创新部", "学生权益部"],
    "团委": ["办公室", "组织部", "综素部", "宣传部", "新闻部", "采编部", "网信部", "就业服务部"],
    "大学生自律委员会": ["督察部", "宿管部", "学生资助服务部"],
}

DEFAULT_TEMPLATES = [
    (
        "学院标准新闻稿", "新闻稿", "正式",
        '[{"key":"title","label":"标题","ai_role":"提炼核心事件，15字以内"},{"key":"lead","label":"导语","ai_role":"5W1H概括，2-3句"},{"key":"process","label":"过程","ai_role":"按时间线展开，突出关键环节"},{"key":"outcome","label":"成果","ai_role":"提炼关键成果和数据"},{"key":"outlook","label":"展望","ai_role":"1-2句致谢或展望"}]',
        '{"title_align":"center","title_bold":true}',
        1,
    ),
    (
        "活动总结模板", "活动总结", "正式",
        '[{"key":"background","label":"活动背景","ai_role":"简述活动目的和背景"},{"key":"process","label":"活动开展","ai_role":"描述活动过程和亮点"},{"key":"outcome","label":"活动成果","ai_role":"总结成果和数据"},{"key":"issues","label":"存在问题","ai_role":"客观分析不足"},{"key":"improve","label":"改进方向","ai_role":"提出改进建议"}]',
        '{"title_align":"left","title_bold":true}',
        1,
    ),
    (
        "会议纪要模板", "会议纪要", "正式",
        '[{"key":"info","label":"基本信息","ai_role":"时间地点参会人员"},{"key":"agenda","label":"会议议题","ai_role":"列出讨论议题"},{"key":"discussion","label":"讨论内容","ai_role":"记录主要发言和讨论"},{"key":"decisions","label":"决议事项","ai_role":"列出达成的决议"},{"key":"tasks","label":"待办事项","ai_role":"列出后续工作和责任人"}]',
        '{"title_align":"left","title_bold":true}',
        1,
    ),
    (
        "通知模板", "通知", "正式",
        '[{"key":"title","label":"标题","ai_role":"关于xxx的通知"},{"key":"body","label":"正文","ai_role":"通知的具体内容"},{"key":"requirements","label":"具体要求","ai_role":"列出需要执行的事项"},{"key":"deadline","label":"截止时间","ai_role":"明确时间节点"},{"key":"contact","label":"联系方式","ai_role":"联系人信息"}]',
        '{"title_align":"center","title_bold":true}',
        1,
    ),
]


def get_db() -> sqlite3.Connection:
    """获取数据库连接（每请求新建，FastAPI 依赖注入用）。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """建表 + 插入默认数据（幂等）。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row

    # 默认组织 + 子部门
    existing_orgs = conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
    if existing_orgs == 0:
        for name, icon, sort_order in DEFAULT_ORGS:
            conn.execute(
                "INSERT INTO organizations (name, icon, sort_order) VALUES (?, ?, ?)",
                (name, icon, sort_order),
            )
        # 插入默认子部门
        for org_name, folder_names in DEFAULT_FOLDERS.items():
            org_row = conn.execute(
                "SELECT id FROM organizations WHERE name = ?", (org_name,)
            ).fetchone()
            if org_row:
                for j, folder_name in enumerate(folder_names):
                    conn.execute(
                        "INSERT INTO folders (organization_id, name, sort_order) VALUES (?, ?, ?)",
                        (org_row["id"], folder_name, j),
                    )

    # 默认模板
    existing_tmpl = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
    if existing_tmpl == 0:
        for args in DEFAULT_TEMPLATES:
            conn.execute(
                "INSERT INTO templates (name, doc_type, style, sections, formatting, is_builtin) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                args,
            )

    # 默认监控源
    existing_sources = conn.execute("SELECT COUNT(*) FROM monitor_sources").fetchone()[0]
    if existing_sources == 0:
        input_dir = str(BASE_DIR / "input")
        conn.execute(
            "INSERT INTO monitor_sources (path, label, enabled) VALUES (?, ?, 1)",
            (input_dir, "项目 input 文件夹"),
        )

    conn.commit()
    conn.close()
