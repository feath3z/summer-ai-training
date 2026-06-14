# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python main.py
```

No dependencies beyond the Python standard library (tkinter is included with standard CPython distributions).

## Architecture

This is a tkinter-based scientific calculator organized as a Python package under `calculator/`.

**Module responsibilities:**
- `main.py` — Entry point; instantiates `Calculator` which auto-launches the GUI
- `calculator/calculator.py` — `Calculator` class: state management (display value, token list, memory, angle mode) and all business logic methods
- `calculator/expression.py` — Safe math expression evaluator using a recursive descent parser (replaces `eval()`). Exposes `evaluate(str) -> float` and `ExpressionError`
- `calculator/history.py` — `HistoryManager`: persists calculation history to `calculator_history.json` (max 50 entries)
- `calculator/ui.py` — Pure UI layout functions (`build_menu`, `build_main_layout`, `build_history_window`, `build_date_window`). Contains zero business logic

**Key design pattern — callback decoupling:**
`Calculator.__init__` builds a `callbacks` dict mapping string keys (e.g. `'press_num'`, `'press_operator'`) to bound methods. The `ui` module receives this dict and never imports or references `Calculator` directly. To add a new button: add the method to `Calculator`, register it in `callbacks`, then reference the key in `ui.py`.

**Expression evaluation flow:**
User input accumulates in `self.tokens` (a `list[str]`). On `=`, tokens are joined into a string and passed to `expression.evaluate()`, which runs a two-phase process: tokenization → recursive descent parsing. The parser grammar (`expression → term → unary → atom`) naturally handles operator precedence without explicit priority tables.

**State variables in Calculator:**
- `self.result` (`StringVar`) — bound to the display label
- `self.tokens` (`list[str]`) — accumulated expression tokens
- `self.ispresssign` (`bool`) — last keypress was an operator (controls clear-on-next-digit and operator replacement)
- `self.memory` (`float`) — M-series memory storage
- `self.is_radian` (`bool`) — angle mode for trig functions
- `self.pending_power` / `self.temp_value` — two-step power operation state (x^y requires pressing `=`, not immediate evaluation)
