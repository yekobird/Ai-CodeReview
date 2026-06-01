"""
代码审查规则库 - 6大类 25+ 条规则
"""
import re

class Rule:
    def __init__(self, rule_id, category, level, description, pattern, suggestion):
        self.rule_id = rule_id
        self.category = category
        self.level = level        # blocker / major / minor / info
        self.description = description
        self.pattern = pattern    # 正则表达式
        self.suggestion = suggestion

# ============================================
# 规则定义
# ============================================
RULES = [
    # ========== 安全规则 ==========
    Rule("S01", "安全", "blocker",
         "SQL注入风险 - 字符串拼接SQL",
         r'(?:SELECT|INSERT|UPDATE|DELETE)\s.*\+',
         "使用 PreparedStatement 或参数化查询"),

    Rule("S02", "安全", "blocker",
         "硬编码密码/密钥",
         r'(?:password|passwd|secret|api_key|apikey)\s*[=:]\s*["\'](?!\$|\{)[^"\']+["\']',
         "使用环境变量或配置中心管理敏感信息"),

    Rule("S03", "安全", "major",
         "日志中打印敏感信息",
         r'(?:log|logger|System\.out)\.(?:info|debug|error)\(.*(?:password|token|secret)',
         "禁止在日志中输出敏感信息，应脱敏处理"),

    Rule("S04", "安全", "major",
         "路径遍历风险",
         r'(?:File|Path|FileReader).*\(.*\+',
         "用户输入拼入文件路径存在目录穿越风险，使用 Path.normalize()"),

    # ========== 质量规则 ==========
    Rule("Q01", "质量", "major",
         "空指针风险 - 未判空直接调用",
         r'(?!.*if\s*\(.*!=\s*null)(?!.*Objects\.requireNonNull)\w+\.\w+\(.*\)',
         "调用前进行 null 判断或使用 Optional"),

    Rule("Q02", "质量", "major",
         "异常吞没 - 空 catch 块",
         r'catch\s*\(.*\)\s*\{\s*\}',
         "至少记录日志或向上抛出，不应吞没异常"),

    Rule("Q03", "质量", "major",
         "资源未关闭",
         r'(?:Connection|Statement|ResultSet|InputStream|OutputStream)\s+\w+\s*=',
         "使用 try-with-resources 自动关闭资源"),

    Rule("Q04", "质量", "major",
         "宽泛异常捕获",
         r'catch\s*\(\s*Exception\s+',
         "捕获具体异常类型，如 IOException、SQLException"),

    Rule("Q05", "质量", "minor",
         "魔法数字",
         r'(?<![\w"])\.(?:equals|compareTo|get|set)\s*\([^"\']*\b\d{2,}\b[^"\']*\)',
         "将数字提取为有意义的常量"),

    # ========== 性能规则 ==========
    Rule("P01", "性能", "major",
         "循环内数据库/网络调用",
         r'for\s*\(.*\)\s*\{[^}]*?(?:query|execute|http|fetch)',
         "将数据库调用移到循环外，使用批量查询"),

    Rule("P02", "性能", "minor",
         "字符串循环拼接",
         r'for\s*\(.*\)\s*\{[^}]*?\w+\s*\+=',
         "使用 StringBuilder 替代 +="),

    Rule("P03", "性能", "minor",
         "循环内创建对象",
         r'for\s*\(.*\)\s*\{[^}]*?new\s+\w+\(',
         "考虑将对象创建移到循环外或使用对象池"),

    # ========== 规范规则 ==========
    Rule("N01", "规范", "info",
         "类名不符合大驼峰",
         r'(?:class|interface|enum)\s+([a-z]\w*)',
         "类名应使用大驼峰命名，如 UserService"),

    Rule("N02", "规范", "info",
         "方法名不符合小驼峰",
         r'(?:public|private|protected)\s+\w+\s+([A-Z]\w*)\s*\(',
         "方法名应使用小驼峰命名，如 getUserById"),

    Rule("N03", "规范", "info",
         "方法过长",
         None,  # 由代码分析工具检测
         "方法超过50行建议拆分"),

    Rule("N04", "规范", "info",
         "参数过多",
         r'\((?:[^)]*,){5,}[^)]*\)',
         "参数超过5个，考虑封装为对象"),

    # ========== 设计规则 ==========
    Rule("D01", "设计", "info",
         "类职责过多",
         None,
         "考虑单一职责原则，拆分类"),

    Rule("D02", "设计", "info",
         "使用废弃 API",
         r'@Deprecated',
         "避免使用已标记为废弃的方法"),

    # ========== 兼容性规则 ==========
    Rule("C01", "兼容性", "major",
         "硬编码文件路径",
         r'["\'][A-Za-z]:[/\\]|["\']/home/|["\']/Users/',
         "使用配置或相对路径，确保跨平台兼容"),
]


def match_rules(code: str) -> list:
    """对代码执行所有规则匹配，返回问题列表"""
    issues = []
    lines = code.split('\n')

    for rule in RULES:
        if rule.pattern is None:
            continue
        for i, line in enumerate(lines, 1):
            if re.search(rule.pattern, line, re.IGNORECASE):
                issues.append({
                    "rule_id": rule.rule_id,
                    "category": rule.category,
                    "level": rule.level,
                    "description": rule.description,
                    "line": i,
                    "code": line.strip()[:80],
                    "suggestion": rule.suggestion
                })
    return issues


def get_level_emoji(level: str) -> str:
    return {"blocker": "🔴", "major": "🟠", "minor": "🟡", "info": "🟢"}.get(level, "⚪")