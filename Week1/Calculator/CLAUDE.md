# CLAUDE.md

本文件为 Claude Code 在此仓库中工作时提供指引。

## 项目简介

Python tkinter 桌面计算器（"小餅餅丶的简易计算器2.0 增强版"）。采用 `calculator/` 包的模块化架构，共 4 个模块，无第三方依赖。

## 运行方式

```bash
python main.py
```

需要 Python 3，tkinter 随标准 CPython 发行版内置。

## 常用命令

```bash
# 启动应用
python main.py

# 运行全部单元测试
python -m pytest tests/ -v

# 运行单个测试文件
python -m pytest tests/test_expression.py -v

# 按关键词筛选测试
python -m pytest tests/ -k "tokenize" -v

# 仅显示失败用例
python -m pytest tests/ --tb=short

# 安装测试依赖（仅 pytest，项目本身无第三方依赖）
pip install pytest
```

## 目录结构

```
calculator/
├── __init__.py
├── expression.py   # 表达式词法分析 + 递归下降解析器（替代 eval）
├── history.py      # HistoryManager：基于 JSON 的持久化计算历史
├── ui.py           # 纯布局函数，通过 callbacks 字典绑定回调，不含业务逻辑
└── calculator.py   # Calculator 类：状态管理、回调实现，组合其余三个模块
main.py             # 程序入口
tests/
├── test_expression.py       # expression.py 单元测试
├── test_history.py          # history.py 单元测试
└── test_calculator_logic.py # calculator.py 纯逻辑单元测试
```

- **expression.py** — `evaluate(expr: str) -> float`，递归下降解析，支持正确的运算符优先级（`*`/`/` 优先于 `+`/`-`），输入非法时抛出 `ExpressionError`
- **history.py** — `HistoryManager` 类，负责加载 / 保存 / 添加 / 清空历史记录，文件存于包同级目录的绝对路径下，上限 50 条
- **ui.py** — 布局函数：`build_menu()`、`build_main_layout()`（含科学计算按钮）、`build_history_window()`、`build_date_window()`；通过 `callbacks` 字典接收回调，不含业务逻辑
- **calculator.py** — `Calculator` 类拥有状态（`result`、`tokens`、`memory`、`is_radian`、`pending_power`），组合 expression、history、ui 三个模块，所有回调方法定义于此

## 编码规范

### 命名规则

- 类名：PascalCase — `Calculator`、`HistoryManager`、`ExpressionError`
- 函数/方法：snake_case — `press_equal`、`build_main_layout`、`_format_result`
- 私有成员：单下划线前缀 — `_tokenize`、`_Parser`、`_load`、`_filepath`
- 常量：UPPER_SNAKE_CASE — `BTN_W`、`BTN_H`、`GAP`
- 布尔变量：`is_` 前缀 — `is_radian`、`ispresssign`

### 注释与文档

- 所有 UI 文本和注释使用**简体中文**
- 模块级：文件顶部用 `"""` 模块文档字符串，说明模块职责
- 类级：`"""` 文档字符串说明类的用途和核心设计
- 公开方法：`"""` 文档字符串，说明功能、参数、返回值、异常
- 内部方法（`_` 前缀）：至少一行 docstring 说明用途
- 行内注释：解释 *为什么*，而非 *做了什么*（代码本身应自解释）
- 分节注释用 `# ── 标题 ──` 格式（如 `# ── 第1行：记忆键 ──`）

### 类型标注

- 公开函数/方法的参数和返回值添加类型标注
- 内部辅助函数酌情添加
- 容器类型使用 `typing` 模块：`Dict[str, Callable]`、`List[Dict[str, str]]`

### 数值与格式化

- 结果格式化统一使用 `_format_result()`，格式为 `f'{value:.12g}'`（12 位有效数字）
- 整数值（如 `3.0`）显示为 `"3"`，去掉小数点
- 绝对值 ≥ 10¹⁵ 的整数走浮点格式，避免 int 转换精度问题

### 安全约束

- **禁止 `eval()` / `exec()`** — 所有表达式求值必须通过 `expression.evaluate()` 的递归下降解析器
- **禁止裸 `except`** — 捕获具体异常类型（`ExpressionError`、`ValueError`、`OSError`、`json.JSONDecodeError`）
- 历史文件路径基于 `__file__` 计算绝对路径，不依赖当前工作目录

### UI 与逻辑分离

- `ui.py` 只负责控件创建和布局，通过 `callbacks: Dict[str, Callable]` 接收回调
- `calculator.py` 拥有全部状态和业务逻辑
- UI 模块不得导入 `calculator` 模块，保持单向依赖

### 测试规范

- 测试文件放在 `tests/` 目录，命名 `test_<模块名>.py`
- 测试类按功能分组：`TestEvaluateBasic`、`TestTokenize`、`TestMaxEntries`
- 使用 `pytest` 框架，`pytest.raises` 断言异常，`pytest.approx` 比较浮点数
- 纯逻辑测试不依赖 tkinter — 通过 `types.SimpleNamespace` 构造最小 self
- 文件 I/O 测试使用 `tmp_path` fixture 隔离，不污染真实数据

### 文件结构约定

- 每个模块顶部包含中文模块文档字符串，说明模块职责和设计思路
- `calculator_history.json` 存于 `calculator/` 包同级目录（绝对路径）
- 测试文件中的注释使用中文，与主代码保持一致
