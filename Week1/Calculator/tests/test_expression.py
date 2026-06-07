"""
expression.py 单元测试

覆盖路径：
  - 基本四则运算与运算符优先级
  - 整除 (//) 与取模 (%)
  - 一元负号与多重负号
  - 小数 / 空白 / 空表达式
  - 除零与非法输入的 ExpressionError
"""

import pytest
from calculator.expression import evaluate, _tokenize, _read_number, ExpressionError


# ============================================================
# evaluate() — 基本运算
# ============================================================

class TestEvaluateBasic:
    """基本四则运算"""

    def test_addition(self):
        assert evaluate("1+2") == 3.0

    def test_subtraction(self):
        assert evaluate("10-3") == 7.0

    def test_multiplication(self):
        assert evaluate("4*5") == 20.0

    def test_division(self):
        assert evaluate("15/3") == 5.0

    def test_float_division(self):
        assert evaluate("10/3") == pytest.approx(3.3333333333333335)

    def test_floor_divide(self):
        assert evaluate("10//3") == 3.0

    def test_modulo(self):
        assert evaluate("10%3") == 1.0


# ============================================================
# evaluate() — 运算符优先级
# ============================================================

class TestEvaluatePrecedence:
    """确保 * / 优先于 + -"""

    def test_multiply_before_add(self):
        assert evaluate("3+5*2") == 13.0

    def test_divide_before_subtract(self):
        assert evaluate("10-6/3") == 8.0

    def test_mixed_precedence(self):
        # 2+3*4-6/2 = 2+12-3 = 11
        assert evaluate("2+3*4-6/2") == 11.0

    def test_left_associativity(self):
        # 10-3-2 = 5（左结合）
        assert evaluate("10-3-2") == 5.0

    def test_left_associativity_multiply(self):
        # 2*3*4 = 24
        assert evaluate("2*3*4") == 24.0


# ============================================================
# evaluate() — 一元负号
# ============================================================

class TestEvaluateUnary:
    """一元负号及其组合"""

    def test_unary_negative(self):
        assert evaluate("-3") == -3.0

    def test_unary_negative_in_expression(self):
        assert evaluate("-3+5") == 2.0

    def test_double_negative(self):
        assert evaluate("--3") == 3.0

    def test_triple_negative(self):
        assert evaluate("---3") == -3.0

    def test_negative_after_operator(self):
        assert evaluate("3*-2") == -6.0

    def test_negative_parentheses_like(self):
        # 表达式 "5+-3" 应为 2
        assert evaluate("5+-3") == 2.0


# ============================================================
# evaluate() — 小数与空白
# ============================================================

class TestEvaluateDecimal:
    """小数和空白字符"""

    def test_decimal_number(self):
        assert evaluate("3.14*2") == pytest.approx(6.28)

    def test_leading_dot(self):
        # ".5" 应被解析为 0.5
        assert evaluate(".5*2") == pytest.approx(1.0)

    def test_spaces_ignored(self):
        assert evaluate(" 3 + 5 * 2 ") == 13.0

    def test_single_number(self):
        assert evaluate("42") == 42.0

    def test_single_decimal(self):
        assert evaluate("3.14") == 3.14


# ============================================================
# evaluate() — 错误处理
# ============================================================

class TestEvaluateErrors:
    """非法表达式应抛出 ExpressionError"""

    def test_empty_expression(self):
        with pytest.raises(ExpressionError, match="不完整"):
            evaluate("")

    def test_plus_only(self):
        with pytest.raises(ExpressionError):
            evaluate("+")

    def test_incomplete_expression(self):
        with pytest.raises(ExpressionError):
            evaluate("3+")

    def test_double_operator(self):
        with pytest.raises(ExpressionError):
            evaluate("3+*5")

    def test_divide_by_zero(self):
        with pytest.raises(ExpressionError, match="除数不能为零"):
            evaluate("10/0")

    def test_floor_divide_by_zero(self):
        with pytest.raises(ExpressionError, match="除数不能为零"):
            evaluate("10//0")

    def test_modulo_by_zero(self):
        with pytest.raises(ExpressionError, match="除数不能为零"):
            evaluate("10%0")

    def test_unsupported_char_letter(self):
        with pytest.raises(ExpressionError, match="不支持的符号"):
            evaluate("3+a")

    def test_unsupported_char_paren(self):
        with pytest.raises(ExpressionError, match="不支持的符号"):
            evaluate("(3+5)")

    def test_extra_tokens_after_number(self):
        with pytest.raises(ExpressionError, match="意外的符号"):
            evaluate("3+5 7")


# ============================================================
# _tokenize() — 词法分析
# ============================================================

class TestTokenize:
    """词法分析器"""

    def test_simple_tokens(self):
        tokens = _tokenize("3+5")
        assert tokens == [('NUMBER', 3.0), ('PLUS', '+'), ('NUMBER', 5.0)]

    def test_all_operators(self):
        tokens = _tokenize("1+2-3*4/5")
        types = [t[0] for t in tokens]
        assert types == [
            'NUMBER', 'PLUS', 'NUMBER', 'MINUS', 'NUMBER',
            'MULTIPLY', 'NUMBER', 'DIVIDE', 'NUMBER'
        ]

    def test_floor_divide_token(self):
        tokens = _tokenize("10//3")
        assert tokens == [
            ('NUMBER', 10.0), ('FLOOR_DIVIDE', '//'), ('NUMBER', 3.0)
        ]

    def test_modulo_token(self):
        tokens = _tokenize("10%3")
        assert tokens == [
            ('NUMBER', 10.0), ('MODULO', '%'), ('NUMBER', 3.0)
        ]

    def test_decimal_token(self):
        tokens = _tokenize("3.14")
        assert tokens == [('NUMBER', 3.14)]

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_spaces_skipped(self):
        tokens = _tokenize(" 3 + 5 ")
        assert tokens == [('NUMBER', 3.0), ('PLUS', '+'), ('NUMBER', 5.0)]

    def test_unsupported_char_raises(self):
        with pytest.raises(ExpressionError, match="不支持的符号"):
            _tokenize("3&5")


# ============================================================
# _read_number() — 数字读取
# ============================================================

class TestReadNumber:
    """数字读取辅助函数"""

    def test_integer(self):
        assert _read_number("123+5", 0) == "123"

    def test_decimal(self):
        assert _read_number("3.14+5", 0) == "3.14"

    def test_leading_dot(self):
        assert _read_number(".5+2", 0) == ".5"

    def test_starts_at_offset(self):
        assert _read_number("10+3.14", 3) == "3.14"

    def test_stops_at_operator(self):
        assert _read_number("42*3", 0) == "42"

    def test_no_digit_at_start_raises(self):
        with pytest.raises(ExpressionError, match="期望数字"):
            _read_number("+5", 0)


# ============================================================
# ExpressionError
# ============================================================

class TestExpressionError:
    """ExpressionError 应为 ValueError 子类"""

    def test_is_value_error(self):
        assert issubclass(ExpressionError, ValueError)

    def test_can_be_caught_as_value_error(self):
        with pytest.raises(ValueError):
            raise ExpressionError("test")
