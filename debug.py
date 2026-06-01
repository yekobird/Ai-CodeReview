import subprocess
import sys
import os
import re

print("1. 当前目录:", os.getcwd())
print("2. Python版本:", sys.version)

# 测试 git
r = subprocess.run(["git", "log", "--oneline", "-2"], capture_output=True)
print("3. Git提交:", r.stdout.decode('utf-8', errors='ignore').strip())

# 测试 diff
r = subprocess.run(["git", "diff", "HEAD~1", "HEAD", "--unified=3"], capture_output=True)
stdout = r.stdout.decode('utf-8', errors='ignore')
print("4. Diff长度:", len(stdout))

# 测试导入
sys.path.insert(0, os.path.join(os.getcwd(), 'review'))
try:
    from rules import match_rules
    print("5. rules导入成功")
except Exception as e:
    print("5. rules导入失败:", e)

# 提取新增行
lines = stdout.split('\n')
added = []
line_num = 0
for line in lines:
    if line.startswith('@@'):
        match = re.search(r'\+(\d+)', line)
        if match:
            line_num = int(match.group(1)) - 1
    elif line.startswith('+') and not line.startswith('+++'):
        line_num += 1
        added.append(line[1:])
    elif not line.startswith('-'):
        line_num += 1

code = '\n'.join(added)
print("6. 新增代码行数:", len(added))
print("7. 代码前500字符:")
print(code[:500])

# 审查
issues = match_rules(code)
print("\n8. 发现问题数:", len(issues))
for i in issues:
    print(f"   {i['level']} | {i['rule_id']} | 行{i['line']} | {i['description']}")