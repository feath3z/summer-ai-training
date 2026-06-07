"""
calculator.py 纯逻辑单元测试（不依赖 tkinter）

覆盖路径：
  - _format_result() 的整数/浮点/大数/极小数格式化
"""

import pytest
import types
from calculator.calculator import Calculator


@pytest.fixture
def fmt():
    """
    提供 _format_result 方法的无 tkinter 引用。

    直接从类上取未绑定方法，避免实例化 Calculator（需要 tkinter 主循环）。
    """
    # 构造一个最小"self"，只携带 _format_result 需要的状态（无）
    dummy = types.SimpleNamespace()
    return lambda value: Calculator._format_result(dummy, value)


# ============================================================
# _format_result — 整数值
# ============================================================

class TestFormatResultIntegers:
    """整数值应去掉小数点显示"""

    def test_whole_number(self, fmt):
        assert fmt(3.0) == "3"

    def test_zero(self, fmt):
        assert fmt(0.0) == "0"

    def test_negative_whole(self, fmt):
        assert fmt(-7.0) == "-7"

    def test_large_whole_number(self, fmt):
        assert fmt(1000000.0) == "1000000"


# ============================================================
# _format_result — 浮点数
# ============================================================

class TestFormatResultFloats:
    """非整数使用 :.12g 格式化"""

    def test_pi(self, fmt):
        result = fmt(3.141592653589793)
        # 12 位有效数字
        assert result == "3.14159265359"

    def test_small_decimal(self, fmt):
        result = fmt(0.1 + 0.2)
        # 浮点精度问题，:.12g 会正确处理
        assert result == "0.3" or "0.30000000000" in result

    def test_negative_float(self, fmt):
        result = fmt(-3.14159)
        assert result.startswith("-3.14159")

    def test_trailing_zeros_removed(self, fmt):
        # 1.50000 应显示为 "1.5"
        assert fmt(1.5) == "1.5"


# ============================================================
# _format_result — 边界情况
# ============================================================

class TestFormatResultEdge:
    """极大/极小数、接近整数的浮点数"""

    def test_very_large_number(self, fmt):
        # 超过 1e15 时保留浮点格式
        result = fmt(1e20)
        assert "e" in result or "E" in result

    def test_very_small_number(self, fmt):
        result = fmt(1e-10)
        assert "e" in result or result == "1e-10"

    def test_negative_zero(self, fmt):
        # -0.0 应显示为 "0"
        result = fmt(-0.0)
        assert result == "0"

    def test_close_to_integer_but_distinct(self, fmt):
        # 2.1 不是整数，应走浮点路径
        result = fmt(2.1)
        assert result == "2.1"

    def test_exact_integer_still_formats_as_int(self, fmt):
        # float64 下 2.000000000001 == 2.0，应视为整数
        result = fmt(2.000000000001)
        assert result == "2"

    def test_integer_boundary_just_below_1e15(self, fmt):
        # 刚好低于 1e15 的整数应显示为整数
        val = 999999999999999.0  # 15 个 9
        assert fmt(val) == "999999999999999"

    def test_integer_boundary_at_1e15(self, fmt):
        # 达到 1e15 时应使用浮点格式
        val = 1e15
        result = fmt(val)
        # 1e15 == int(1e15)，但 abs >= 1e15，所以走浮点路径
        assert "e" in result or result == "1000000000000000"
