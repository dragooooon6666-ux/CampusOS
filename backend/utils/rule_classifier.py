"""
规则分类引擎 —— 不依赖 AI 完成基础文件分类

设计目标：未配置 AI Key 时也能把文件分到合理位置。

四层判定：
1. 文件族 —— 先按扩展名确定范围（文稿 / 表格 / 演示 / 媒体 / 压缩包）
2. 文种结尾 —— 公文命名习惯是文种在末尾（「关于XX的通知」「XX活动总结」），可信度最高
3. 关键词包含 —— 长词优先，避免「总结」误吃「工作总结」
4. 兜底 —— 按扩展名给大类标签，并标记 needs_ai，等配置 Key 后再精分类

与 AI 的关系：
- 规则高置信度判定 → 直接定型（ai_analyzed=0，用户可随时改）
- 规则判不出具体类型 → needs_ai=True，可在配置 Key 后批量精分类
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Classification:
    """规则分类结果"""
    doc_type: str
    confidence: str          # high / medium / low
    reason: str              # 判定依据（给用户看的说明）
    needs_ai: bool = False   # 是否需要 AI 进一步精分类

    def __bool__(self) -> bool:
        return bool(self.doc_type)


# ── 文件族：按扩展名划定候选范围 ────────────────────────────

FAMILY_BY_EXTENSION = {
    # 文稿族
    ".doc": "doc", ".docx": "doc", ".wps": "doc", ".rtf": "doc",
    ".pdf": "doc", ".ofd": "doc",
    ".txt": "doc", ".md": "doc", ".markdown": "doc", ".log": "doc",
    # 表格族
    ".xls": "sheet", ".xlsx": "sheet", ".csv": "sheet", ".et": "sheet",
    # 演示族
    ".ppt": "slide", ".pptx": "slide", ".dps": "slide",
    # 媒体族
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image",
    ".bmp": "image", ".webp": "image", ".heic": "image",
    ".tif": "image", ".tiff": "image",
    ".mp4": "video", ".mov": "video", ".avi": "video", ".mkv": "video",
    ".wmv": "video", ".flv": "video", ".webm": "video", ".m4v": "video",
    # 压缩包
    ".zip": "archive", ".rar": "archive", ".7z": "archive",
    ".tar": "archive", ".gz": "archive",
}

# 兜底标签（规则判不出具体类型时用）
FALLBACK_LABEL = {
    "doc": {".pdf": "PDF文档", ".txt": "纯文本", ".md": "纯文本", ".log": "纯文本"},
    "sheet": "Excel表格",
    "slide": "PPT演示",
    "archive": "压缩包",
    "image": "图片",
    "video": "视频",
}
_DEFAULT_FALLBACK = "其他文件"


# ── 规则表 ──────────────────────────────────────────────────
#
# 每项：(关键词元组, 文档类型)
# 元组内长词在前；引擎还会自动按长度排序，避免短词抢匹配。

# 通用规则：这些词描述的是「内容类型」，不是「文件格式」，任何格式都可能出现。
# 真实场景：学生会用 Word 做签到表、用 Word 做经费预算、用 Excel 写策划，
# 所以不能按扩展名把它们锁死在表格族里。
COMMON_RULES = [
    # 表单类（报名表.docx / 登记表.pdf / 汇总表.xlsx）
    (("信息采集表", "汇总表", "收集表", "报名表", "登记表", "反馈表",
      "申报表", "异动表", "申请表", "调查表", "问卷"), "收集表"),
    (("通讯录", "联络表", "花名册", "联系表", "联系名单"), "通讯录"),
    # 台账类：Word 里做的表格最常落在这里
    (("签到表", "考勤表", "考勤", "签到", "出勤", "点名"), "签到表"),
    (("排班表", "值班表", "值日表", "轮值表", "排班", "值班", "值日"), "排班表"),
    (("预算表", "经费预算", "预算", "决算", "经费", "开支", "报销", "账单"), "预算表"),
    (("物资清单", "物资表", "采购清单", "物品清单", "物资", "采购", "库存", "借用"), "物资清单"),
    # 名单 / 统计类：产品规则是「名单 → 统计表」，不是签到表
    (("统计表", "人员名单", "参赛名单", "获奖名单", "名单", "情况表",
      "综素表", "综测", "统计", "汇总", "成绩表", "分数"), "统计表"),
]

# 文稿族（.docx / .doc / .pdf / .txt）
DOC_RULES = [
    (("策划书", "策划案", "策划方案", "活动策划", "项目策划", "策划"), "策划案"),
    (("实施方案", "工作方案", "活动方案", "应急预案", "方案"), "方案"),
    (("新闻稿", "通讯稿", "宣传稿", "新闻通稿", "通稿", "推文"), "新闻稿"),
    (("活动总结", "工作总结", "学期总结", "学年总结", "项目总结",
      "总结报告", "总结", "小结", "复盘", "回顾"), "活动总结"),
    (("会议纪要", "例会纪要", "座谈纪要", "会议记录", "例会记录",
      "会议实录", "谈话记录", "谈话纪要", "纪要"), "会议纪要"),
    (("议程", "日程", "活动流程", "流程安排", "会议流程"), "议程"),
    (("请示", "批示"), "请示"),
    (("申报书", "申请书", "个人申请", "困难申请", "入团申请", "入党申请"), "申请书"),
    (("证明", "证明材料", "在读证明", "学籍证明", "获奖证明"), "证明"),
    (("发言稿", "讲话稿", "致辞", "主持稿", "演讲稿", "宣讲稿", "发言材料"), "发言稿"),
    (("述职报告", "述职"), "述职报告"),
    (("工作汇报", "汇报材料", "进展情况", "汇报", "报告"), "报告"),
    (("个人简历", "求职简历", "简历", "求职信"), "简历"),
    (("毕业论文", "课程论文", "学术论文", "调研报告", "论文"), "论文"),
    (("观后感", "读后感", "心得体会", "作业", "习题"), "作业"),
    (("读书笔记", "学习笔记", "笔记", "摘录"), "笔记"),
    (("通知", "公告", "公示", "通告", "告示", "须知", "温馨提示"), "通知"),
    # 以下来自真实文件的词频统计（不是拍脑袋想的）
    (("工作计划", "学期计划", "学年计划", "年度计划", "访谈提纲"), "方案"),
    (("事迹材料", "评估材料", "整改材料"), "报告"),
]

# 演示族（.pptx / .ppt）
SLIDE_RULES = [
    (("述职",), "述职报告"),
    (("汇报", "报告"), "报告"),
    (("策划", "方案"), "策划案"),
    (("总结",), "活动总结"),
    (("班会", "宣讲", "培训", "分享"), "方案"),
]


# ── 文件名清理 ──────────────────────────────────────────────

_NOISE_PATTERNS = [
    r"[（(]\s*\d+\s*[)）]",              # (1) （2）
    r"[（(]\s*副本\s*[)）]",             # （副本）
    r"[-_ ]*(最终版|修改版|定稿|初稿|最新版|修订版|副本|备份)\s*$",
    r"\s*-\s*副本\s*$",
    # 结尾的括号标注：「XX策划案（就业服务部）」「XX证明（24社工贺龙）」
    # 这类署名挡在末尾会让「文种在结尾」的规则失配，先剥掉再匹配
    r"(?:[（(][^（()）]*[)）]\s*)+$",
]

# 常见无信息文件名（Office/WPS 默认名、微信保存名）
_MEANINGLESS = (
    "新建", "文档", "工作簿", "演示文稿", "未命名", "无标题",
    "扫描全能王", "微信图片", "微信截图", "屏幕截图", "截图",
    "img_", "dsc_", "image", "untitled", "document",
)


def _clean_stem(stem: str) -> str:
    """剥离文件名里的噪音，便于文种匹配。"""
    s = stem
    for pat in _NOISE_PATTERNS:
        s = re.sub(pat, "", s)
    return s.strip()


def _is_meaningless(stem: str) -> bool:
    """文件名是否不含任何有效信息（纯日期、纯编号、默认名）。"""
    low = stem.lower().strip()
    if not low:
        return True
    for kw in _MEANINGLESS:
        if low.startswith(kw):
            return True
    # 纯数字/日期/编号：20250901、1、IMG_001 之类
    if re.fullmatch(r"[\d\s\-_.]+", low):
        return True
    return False


# ── 匹配逻辑 ────────────────────────────────────────────────

def _flatten(rules: list) -> list[tuple[str, str]]:
    """展开为 (关键词, 类型) 并按键长降序，保证长词优先。"""
    pairs = [(kw, doc_type) for keywords, doc_type in rules for kw in keywords]
    return sorted(pairs, key=lambda x: len(x[0]), reverse=True)


def _match_tail(stem: str, pairs: list[tuple[str, str]]) -> tuple[str, str] | None:
    """文种出现在文件名末尾 → 命中（公文命名习惯，可信度最高）。"""
    tail = stem[-8:]
    for kw, doc_type in pairs:
        if tail.endswith(kw):
            return doc_type, kw
    return None


def _match_contains(stem: str, pairs: list[tuple[str, str]]) -> tuple[str, str] | None:
    """关键词出现在文件名任意位置（已按键长降序，长词优先）。"""
    for kw, doc_type in pairs:
        if kw in stem:
            return doc_type, kw
    return None


# 以这些词结尾的文件，是在「描述」某件事，不是在「做」那张表本身。
# 例：「签到流程说明.docx」讲的是怎么签到，不是签到表 → 不参与全文匹配
_DESCRIPTIVE_SUFFIXES = ("说明", "指南", "规范", "制度", "办法", "流程", "注意事项")


def _is_descriptive(stem: str) -> bool:
    return stem.endswith(_DESCRIPTIVE_SUFFIXES)


# ── 主入口 ──────────────────────────────────────────────────

def classify(filename: str) -> Classification:
    """按规则分类一个文件名，返回 Classification。"""
    path = Path(filename)
    ext = path.suffix.lower()
    stem = _clean_stem(path.stem)
    family = FAMILY_BY_EXTENSION.get(ext)

    # 媒体 / 压缩包：按格式归类，不看内容
    if family in ("image", "video", "archive"):
        label = FALLBACK_LABEL[family]
        return Classification(label, "high", "按文件格式归类", needs_ai=False)

    # 组装规则：通用规则优先，再按文件族追加
    rules = list(COMMON_RULES)
    if family == "doc":
        rules += DOC_RULES
    elif family == "slide":
        rules += SLIDE_RULES
    elif family != "sheet":
        # 未知扩展名：文稿和演示规则都试一遍
        # （表格族没有专属规则，内容类型词都归在 COMMON_RULES 里）
        rules += DOC_RULES + SLIDE_RULES

    pairs = _flatten(rules)

    # 无信息文件名（新建文档.docx / 20250901.pdf）直接走兜底
    if not _is_meaningless(stem):
        hit = _match_tail(stem, pairs)
        if hit:
            return Classification(hit[0], "high", f"文件名以「{hit[1]}」结尾", needs_ai=False)

        # 「XX流程说明」这类描述性文件不做全文匹配：
        # ─ 结尾匹配已经试过了，再全文匹配会把「签到」误吃成签到表
        if not _is_descriptive(stem):
            hit = _match_contains(stem, pairs)
            if hit:
                return Classification(hit[0], "medium", f"文件名含「{hit[1]}」", needs_ai=False)

    # 兜底：按扩展名给大类，标记待精分类
    return _fallback(ext, family)


def _fallback(ext: str, family: str | None) -> Classification:
    """规则判不出具体类型时的兜底标签。"""
    if family == "doc":
        label = FALLBACK_LABEL["doc"].get(ext, "Word文档")
    elif family in ("sheet", "slide", "archive"):
        label = FALLBACK_LABEL[family]
    elif family in ("image", "video"):
        label = FALLBACK_LABEL[family]
    else:
        label = _DEFAULT_FALLBACK

    return Classification(label, "low", "文件名无法判断具体类型", needs_ai=True)
