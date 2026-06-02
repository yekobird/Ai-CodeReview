"""
Git 提交代码审查 Agent
触发方式：git post-commit hook 自动调用
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rules import match_rules, get_level_emoji, RULES

# ============================================
# 配置
# ============================================
PROJECT_ROOT = os.getcwd()
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")
CONFIG_FILE = os.path.join(Path(__file__).parent, "config.json")


def load_config() -> dict:
    """加载配置"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"enabled": True}


def is_review_enabled() -> bool:
    """检查审查是否开启"""
    config = load_config()
    return config.get("enabled", True)


def get_git_diff() -> str:
    """获取最近一次提交的 diff"""
    try:
        # 获取 HEAD 的 diff
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--unified=3"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            # 可能是首次提交，只获取本次变更
            result = subprocess.run(
                ["git", "diff", "--cached", "--unified=3"],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
        return result.stdout
    except Exception as e:
        print(f"获取 diff 失败: {e}")
        return ""


def get_changed_files() -> list:
    """获取变更的文件列表"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
    return [f for f in result.stdout.strip().split('\n') if f]


def extract_added_lines(diff: str) -> list:
    """提取新增的代码行"""
    lines = diff.split('\n')
    added = []
    line_num = 0
    for line in lines:
        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                line_num = int(match.group(1)) - 1
        elif line.startswith('+') and not line.startswith('+++'):
            line_num += 1
            added.append((line_num, line[1:]))
        elif not line.startswith('-'):
            line_num += 1
    return added


import re


def review_diff(diff: str) -> dict:
    """审查 diff，返回结构化结果"""
    issues = []
    files = get_changed_files()
    added_lines = extract_added_lines(diff)

    # 只审查新增的代码行
    code_lines = '\n'.join([line for _, line in added_lines])
    line_map = {i+1: num for i, (num, _) in enumerate(added_lines)}

    # 规则匹配
    raw_issues = match_rules(code_lines)
    for issue in raw_issues:
        actual_line = line_map.get(issue["line"], issue["line"])
        issues.append({
            **issue,
            "line": actual_line
        })

    # 统计
    stats = {
        "total": len(issues),
        "blocker": sum(1 for i in issues if i["level"] == "blocker"),
        "major": sum(1 for i in issues if i["level"] == "major"),
        "minor": sum(1 for i in issues if i["level"] == "minor"),
        "info": sum(1 for i in issues if i["level"] == "info"),
    }

    # 评分（blocker 每个扣 2 分，major 扣 1 分）
    score = max(1, 10 - stats["blocker"] * 2 - stats["major"])
    stats["score"] = score

    return {
        "issues": issues,
        "stats": stats,
        "files": files,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_report(result: dict) -> str:
    """生成 Markdown 报告"""
    stats = result["stats"]
    issues = result["issues"]
    files = result["files"]

    # 按级别分组
    groups = {"blocker": [], "major": [], "minor": [], "info": []}
    for issue in issues:
        groups[issue["level"]].append(issue)

    report = f"""# 🔍 代码审查报告

**审查时间：** {result['timestamp']}
**变更文件：** {len(files)} 个
**问题总数：** {stats['total']} 个

## 📊 总评分：{stats['score']}/10

| 级别 | 数量 |
|------|:--:|
| 🔴 阻断 | {stats['blocker']} |
| 🟠 严重 | {stats['major']} |
| 🟡 警告 | {stats['minor']} |
| 🟢 建议 | {stats['info']} |

## 📁 变更文件

"""
    for f in files:
        report += f"- `{f}`\n"

    if not issues:
        report += "\n## ✅ 恭喜！未发现问题\n"
        return report

    # 按级别输出问题
    level_names = [
        ("blocker", "🔴 阻断问题（必须修复）"),
        ("major", "🟠 严重问题（强烈建议修复）"),
        ("minor", "🟡 警告（建议优化）"),
        ("info", "🟢 建议（可后续改进）"),
    ]

    for level, title in level_names:
        if groups[level]:
            report += f"\n## {title}\n\n"
            report += "| 规则 | 行 | 问题 | 建议 |\n"
            report += "|------|:--:|------|------|\n"
            for issue in groups[level]:
                report += f"| {issue['rule_id']} | {issue['line']} | {issue['description']} | {issue['suggestion']} |\n"

    report += f"\n---\n*自动生成于 {result['timestamp']} | 审查规则: {len(RULES)} 条*"
    return report


def save_report(report: str):
    """保存报告到文件"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    filename = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(REPORT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📄 报告已保存: {filepath}")
    return filepath


def run_review():
    """执行审查（主入口）"""
    # 检查是否开启
    if not is_review_enabled():
        print("⏸️  代码审查已关闭")
        return

    print("🔍 正在审查代码...")

    # 获取 diff
    diff = get_git_diff()
    if not diff:
        print("⚠️  未检测到代码变更")
        return

    # 执行审查
    result = review_diff(diff)

    # 生成报告
    report = generate_report(result)
    print(report)

    # 保存
    save_report(report)

    # 输出摘要
    stats = result["stats"]
    if stats["blocker"] > 0:
        print(f"\n⚠️  发现 {stats['blocker']} 个阻断问题，建议修复后再提交")
    elif stats["major"] > 0:
        print(f"\n💡 发现 {stats['major']} 个严重问题，建议优化")
    else:
        print(f"\n✅ 代码审查通过！")


if __name__ == "__main__":
    run_review()