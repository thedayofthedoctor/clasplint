# CLASPLint

[![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](./LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.2.0-orange)](https://pypi.org/project/CLASPLint/)

> **CLASP 3.0 / PEP 2606** static analysis tool. Enforces naming and comment conventions **beyond PEP 8** — checks variables, dictionary keys, functions, classes, comments, and log messages for standards compliance.

---

## Features

- **Variable names** — `group1_group2` format, all lowercase, no abbreviations, type/boolean prefixes, ≤30 chars
- **Dictionary keys** — PascalCase, full spelling, acronyms kept uppercase
- **Function & class names** — snake_case for functions, PascalCase for classes, private methods `_init_X_function_`
- **Comment format** — every physical code line requires `# Capitalized sentence.` comment (import/class/def exempt)
- **Log messages** — pre-defined string variables, proper `try-except` chains, `exc_info=True` on errors
- **Docstrings** — presence check for all functions and classes; Sphinx `:param/:type/:return` format enforcement for methods with detailed description requirement

## Installation

```bash
pip install CLASPLint
```

Or from source:

```bash
git clone https://github.com/thedayofthedoctor/clasplint.git
cd clasplint
pip install -e .
```

## Quick Start

```bash
# Check a single file
CLASPLint path/to/file.py

# Check all Python files in a directory (recursive)
CLASPLint src/

# Show only summary, no per-violation output
CLASPLint --quiet src/

# Filter by violation category
CLASPLint --category variable src/
```

## Usage

```
usage: CLASPLint [-h] [--version] [--no-recursive] [--quiet] [-c CATEGORY] [paths ...]

positional arguments:
  paths                 Python files or directories to check (default: current directory)

options:
  --version             show version number and exit
  --no-recursive        do not recursively check subdirectories
  --quiet, -q           suppress individual violation output; show only summary
  --category, -c {variable,dict_key,function,comment,log,docstring}
                        only report violations of a specific category
```

## Example Output

```
$ CLASPLint tests/test_violations.py

CLASPLint: 30 violation(s) in 1 of 1 file(s).
  comment: 8
  dict_key: 4
  function: 3
  log: 4
  variable: 11

  tests/test_violations.py:8  [variable] Variable 'badvar' must have exactly one underscore ...
  tests/test_violations.py:11 [variable] Variable 'Bad_Var' contains uppercase letters ...
  ...
```

## CLASP 3.0 / PEP 2606 Rules Summary

| Category   | Rule |
|------------|------|
| Variable   | `group1_group2`, one underscore, all lowercase, no abbreviations, ≤30 chars |
| Boolean    | `is_` or `has_` prefix |
| Dict Key   | PascalCase, full spelling, acronyms uppercase (GPS, UTM, XML, etc.) |
| Class      | PascalCase |
| Function   | snake_case, specific verb, ≤30 chars |
| Method     | Public: short snake_case; Private: `_init_X_function_` ≤30 chars |
| Comment    | Every physical line: `# Capitalized sentence ending with period.` (import/class/def exempt) |
| Log        | Messages as variables, proper `try-except` logging chain, `exc_info=True` |
| Docstring  | Presence required; Sphinx `:param/:type/:return` format for methods with detail section |

## Python Version Support

CLASPLint supports **Python 3.8 through 3.13+**. The minimum version is 3.8 due to `ast.Constant`, `ast.NamedExpr`, and `ast.get_docstring()` usage.

## License

[GPL-3.0-only](./LICENSE) — Copyright (C) 2026 Matt Belfast Brown

---

<!-- TODO: add badges, CI status, coverage, etc. -->

---

# CLASPLint（中文）

[![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPLv3+-green)](./LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.2.0-orange)](https://pypi.org/project/CLASPLint/)

> **CLASP 3.0 / PEP 2606** 静态分析工具。在 PEP 8 **之上**强制执行命名与注释规范 —— 检查变量、字典键、函数、类、注释和日志消息是否符合标准。

---

## 功能特性

- **变量名** —— `group1_group2` 两段下划线格式，全部小写，禁止缩写，支持类型/布尔前缀，≤30 字符
- **字典键名** —— PascalCase 驼峰式，完整拼写，专有缩写保持大写
- **函数与类名** —— 函数 snake_case，类 PascalCase，私有方法 `_init_X_function_`
- **注释格式** —— 每条物理代码行前必须有 `# 首字母大写英文句子并以句号结尾。`（import/class/def 豁免）
- **日志消息** —— 必须预定义为字符串变量，完整的 `try-except` 链条，错误日志带 `exc_info=True`
- **文档字符串** —— 函数和类必须存在；方法需遵循 Sphinx `:param/:type/:return` 格式，并包含详细逻辑描述段落

## 安装

```bash
pip install CLASPLint
```

或从源码安装：

```bash
git clone https://github.com/thedayofthedoctor/clasplint.git
cd clasplint
pip install -e .
```

## 快速开始

```bash
# 检查单个文件
CLASPLint path/to/file.py

# 递归检查目录下所有 Python 文件
CLASPLint src/

# 仅显示摘要，不输出逐条违规
CLASPLint --quiet src/

# 按类别过滤
CLASPLint --category variable src/
```

## 命令行用法

```
usage: CLASPLint [-h] [--version] [--no-recursive] [--quiet] [-c CATEGORY] [paths ...]

位置参数:
  paths                 要检查的 Python 文件或目录（默认：当前目录）

可选参数:
  --version             显示版本号并退出
  --no-recursive        不递归检查子目录
  --quiet, -q           仅显示摘要，抑制逐条违规输出
  --category, -c {variable,dict_key,function,comment,log,docstring}
                        仅报告指定类别的违规
```

## 输出示例

```
$ CLASPLint tests/test_violations.py

CLASPLint: 30 violation(s) in 1 of 1 file(s).
  comment: 8
  dict_key: 4
  function: 3
  log: 4
  variable: 11

  tests/test_violations.py:8  [variable] Variable 'badvar' must have exactly one underscore ...
  tests/test_violations.py:11 [variable] Variable 'Bad_Var' contains uppercase letters ...
  ...
```

## CLASP 3.0 / PEP 2606 规则速查

| 类别       | 规则 |
|------------|------|
| 变量       | `group1_group2`，有且仅有一个下划线，全部小写，禁止缩写，≤30 字符 |
| 布尔值     | `is_` 或 `has_` 前缀 |
| 字典键     | PascalCase 驼峰式，完整拼写，专有缩写大写（GPS、UTM、XML 等） |
| 类名       | PascalCase |
| 函数名     | snake_case，使用具体动词，≤30 字符 |
| 方法       | 公共：简短 snake_case；私有：`_init_X_function_` ≤30 字符 |
| 注释       | 每条物理行：`# Capitalized sentence ending with period.`（import/class/def 豁免） |
| 日志       | 消息预定义为变量，完整 `try-except` 日志链，`exc_info=True` |
| 文档字符串 | 必须存在；方法需 Sphinx `:param/:type/:return` 格式并包含详细段落 |

## Python 版本支持

CLASPLint 支持 **Python 3.8 至 3.14+**。最低版本为 3.8，原因在于使用了 `ast.Constant`、`ast.NamedExpr` 和 `ast.get_docstring()`。

## 许可证

[GPL-3.0-only](./LICENSE) — Copyright (C) 2026 Matt Belfast Brown
