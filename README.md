# 🔍 AI Code Review

基于 Python 的 Git 提交自动代码审查工具，提交代码后自动触发审查并生成 Markdown 报告。

## 🎯 功能

- **自动触发**：`git commit` 后自动执行代码审查
- **多维度规则**：6 大类 25+ 条审查规则，覆盖安全、质量、性能、规范、设计、兼容性
- **分级报告**：阻断 / 严重 / 警告 / 建议 四级分类，清晰直观
- **本地运行**：无需网络，零依赖 AI 模型
- **可控开关**：修改配置文件随时开启/关闭审查
- **可视化评分**：0-10 分评分 + 问题分布条形图

## 📊 审查规则

| 类别 | 数量 | 级别 | 示例 |
|------|:--:|------|------|
| 安全 | 4 条 | 阻断/严重 | SQL注入、硬编码密码、日志泄密、路径遍历 |
| 质量 | 5 条 | 严重/警告 | 空指针、异常吞没、资源泄漏、宽泛异常捕获、魔法数字 |
| 性能 | 3 条 | 警告 | 循环内查库、字符串循环拼接、循环内创建对象 |
| 规范 | 4 条 | 建议 | 类名大驼峰、方法名小驼峰、方法过长、参数过多 |
| 设计 | 2 条 | 建议 | 单一职责、废弃API |
| 兼容性 | 1 条 | 严重 | 硬编码文件路径 |

## 📁 文件结构

```json
aiCodeReview/
├── review/
│ ├── init.py # 包初始化（空文件）
│ ├── config.json # 审查开关配置
│ ├── rules.py # 审查规则库
│ └── agent.py # 主审查程序
├── reports/ # 审查报告输出目录
├── .git/hooks/
│ └── post-commit # Git 钩子（提交后自动触发）
└── README.md
```

## 📝 核心文件说明

### review/agent.py
主审查程序，包含以下功能：
- **get_git_diff()** - 获取最近一次提交的代码变更
- **get_changed_files()** - 获取变更文件列表
- **extract_added_lines()** - 提取新增代码行
- **review_diff()** - 执行规则匹配
- **generate_report()** - 生成 Markdown 格式报告
- **save_report()** - 保存报告到 reports/ 目录

### review/rules.py
审查规则库，每条规则包含：
- `rule_id` - 规则编号
- `category` - 分类
- `level` - 严重级别（blocker/major/minor/info）
- `description` - 问题描述
- `pattern` - 正则匹配模式
- `suggestion` - 修复建议

### review/config.json
审查开关配置：
```json
{ "enabled": true }
```

### 🚀 快速开始

1. 部署
```json
# 在项目根目录创建目录
mkdir review reports

# 复制所有文件到对应位置
# review/__init__.py
# review/config.json
# review/rules.py
# review/agent.py
# .git/hooks/post-commit
```
2. 赋予钩子执行权限
```json
# Linux/Mac
chmod +x .git/hooks/post-commit
```
Windows 无需额外操作。

3. 提交代码
```json
git add .
git commit -m "feat: 新增功能"
# 提交后自动触发审查
```
4. 查看报告
```json
ls reports/
# review_20260602_103000.md
```

📊 报告示例

```json
# 🔍 代码审查报告

时间：2026-06-02 10:30
文件：2 个
问题：8 个

🟡 总评分：6/10

| 🔴 阻断 | 🟠 严重 | 🟡 警告 | 🟢 建议 |
|:--:|:--:|:--:|:--:|
| 2 | 3 | 2 | 1 |

## 🔴 阻断问题（必须修复）

| 规则ID | 行号 | 问题描述 | 修复建议 |
| `S01` | 24 | SQL注入风险 | 使用 PreparedStatement |
| `S02` | 16 | 硬编码密码 | 使用环境变量 |

## 📈 问题分布

阻断: ██░░░ 2
严重: ███░░ 3
警告: ██░░░ 2
建议: █░░░░ 1
```

###⚙️ 控制开关

关闭审查：
编辑 review/config.json：
```json
{ "enabled": false }
```

开启审查：
```json
{ "enabled": true }
```

临时跳过审查：
```json
git commit -m "fix" --no-verify
```


➕ 自定义规则

编辑 review/rules.py，
在 RULES 列表中添加：

```json
Rule("自定义ID", "分类", "级别",
     "问题描述",
     r'正则表达式',
     "修复建议"),
```

级别选项：
```json
blocker - 阻断，必须修复

major - 严重，强烈建议修复

minor - 警告，建议优化

info - 建议，可后续改进
```

示例 - 添加"禁止使用 System.out.println"规则：
```json
Rule("Q06", "规范", "minor",
     "使用了 System.out.println",
     r'System\.out\.println',
     "使用日志框架替代，如 SLF4J"),
```

📋 严重级别说明
```json
级别	图标	含义	行动
blocker	🔴	阻断	必须立即修复
major	🟠	严重	强烈建议修复
minor	🟡	警告	建议优化
info	🟢	建议	可后续改进
```
🛠️ 技术栈

Python 3.11+

Git Hooks

正则表达式


❓ 常见问题
```json
Q: 提交后没有生成报告？
A: 检查 review/config.json 中 enabled 是否为 true，确认 Python 已安装且可命令行调用。

Q: 首次提交没有触发审查？
A: 至少需要 2 次提交才能获取 diff，首次提交后再提交一次即可触发。

Q: 报告显示"无新增代码变更"？
A: 审查只检查新增的代码行（以 + 开头），只删除代码不产生新问题。

Q: 如何只审查指定文件？
A: 修改 extract_added_lines() 函数，添加文件类型过滤。
```