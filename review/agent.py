"""
Git 提交代码审查 Agent
"""
import os
import sys
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rules import match_rules, RULES

PROJECT_ROOT = os.getcwd()
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")
CONFIG_FILE = os.path.join(Path(__file__).parent, "config.json")


def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"enabled": True}


def is_review_enabled():
    return load_config().get("enabled", True)


def get_git_diff():
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--unified=3"],
            capture_output=True, cwd=PROJECT_ROOT
        )
        stdout = result.stdout.decode('utf-8', errors='ignore')
        if result.returncode == 0 and stdout.strip():
            return stdout

        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=3"],
            capture_output=True, cwd=PROJECT_ROOT
        )
        stdout = result.stdout.decode('utf-8', errors='ignore')
        if stdout.strip():
            return stdout

        result = subprocess.run(
            ["git", "diff", "HEAD", "--unified=3"],
            capture_output=True, cwd=PROJECT_ROOT
        )
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"获取 diff 失败: {e}")
        return ""


def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, cwd=PROJECT_ROOT
    )
    stdout = result.stdout.decode('utf-8', errors='ignore')
    if result.returncode != 0 or not stdout.strip():
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, cwd=PROJECT_ROOT
        )
        stdout = result.stdout.decode('utf-8', errors='ignore')
    if not stdout.strip():
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, cwd=PROJECT_ROOT
        )
        stdout = result.stdout.decode('utf-8', errors='ignore')
    return [f for f in stdout.strip().split('\n') if f]


def extract_added_lines(diff):
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


def review_diff(diff):
    issues = []
    files = get_changed_files()
    added_lines = extract_added_lines(diff)

    if not added_lines:
        return {
            "issues": [],
            "stats": {"total": 0, "blocker": 0, "major": 0, "minor": 0, "info": 0, "score": 10},
            "files": files,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "empty": True
        }

    code_lines = '\n'.join([line for _, line in added_lines])
    line_map = {i+1: num for i, (num, _) in enumerate(added_lines)}

    raw_issues = match_rules(code_lines)
    for issue in raw_issues:
        actual_line = line_map.get(issue["line"], issue["line"])
        issues.append({**issue, "line": actual_line})

    stats = {
        "total": len(issues),
        "blocker": sum(1 for i in issues if i["level"] == "blocker"),
        "major": sum(1 for i in issues if i["level"] == "major"),
        "minor": sum(1 for i in issues if i["level"] == "minor"),
        "info": sum(1 for i in issues if i["level"] == "info"),
    }
    score = max(1, 10 - stats["blocker"] * 2 - stats["major"])
    stats["score"] = score

    return {
        "issues": issues,
        "stats": stats,
        "files": files,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_report(result):
    stats = result["stats"]
    issues = result["issues"]
    files = result["files"]

    groups = {"blocker": [], "major": [], "minor": [], "info": []}
    for issue in issues:
        groups[issue["level"]].append(issue)

    report = f"""# 代码审查报告

**时间：** {result['timestamp']}
**文件：** {len(files)} 个
**问题：** {stats['total']} 个

## 评分：{stats['score']}/10

| 级别 | 数量 |
|------|:--:|
| 阻断 | {stats['blocker']} |
| 严重 | {stats['major']} |
| 警告 | {stats['minor']} |
| 建议 | {stats['info']} |

"""
    for f in files:
        report += f"- `{f}`\n"

    if not issues:
        if result.get("empty"):
            report += "\n## 本次提交无代码变更\n"
        else:
            report += "\n## 未发现问题\n"
        report += f"\n---\n*审查规则: {len(RULES)} 条*"
        return report

    level_names = [
        ("blocker", "阻断问题"),
        ("major", "严重问题"),
        ("minor", "警告"),
        ("info", "建议"),
    ]

    for level, title in level_names:
        if groups[level]:
            report += f"\n## {title}\n\n"
            report += "| 规则 | 行 | 问题 | 建议 |\n"
            report += "|------|:--:|------|------|\n"
            for issue in groups[level]:
                report += f"| {issue['rule_id']} | {issue['line']} | {issue['description']} | {issue['suggestion']} |\n"

    report += f"\n---\n*审查规则: {len(RULES)} 条*"
    return report


def save_report(report):
    os.makedirs(REPORT_DIR, exist_ok=True)
    filename = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {filepath}")
    return filepath


if __name__ == "__main__":
    if not is_review_enabled():
        print("审查已关闭")
    else:
        print("开始审查...")
        diff = get_git_diff()
        print(f"Diff长度: {len(diff)}")
        result = review_diff(diff)
        report = generate_report(result)
        print(report)
        save_report(report)