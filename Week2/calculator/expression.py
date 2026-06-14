"""
安全的数学表达式求值器（expression.py）
=======================================

本模块替代 Python 内置的 eval() 函数，提供一个安全、可控的数学表达式求值器。

【为什么要替代 eval()】
  原始代码使用 eval() 直接执行用户输入的表达式字符串，存在严重的安全隐患：
  即使表达式来自按钮输入，如果历史记录文件被篡改，或未来扩展文本输入，
  eval() 可能执行任意 Python 代码（如 __import__('os').system('rm -rf /')）。

【设计思路：递归下降解析器】
  本模块采用经典的递归下降（Recursive Descent）解析技术，分为两个阶段：
  1. 词法分析（Tokenization）：将原始字符串拆分为 token 列表
     例如 "3+5*2" → [('NUMBER',3), ('PLUS','+'), ('NUMBER',5), ('MULTIPLY','*'), ('NUMBER',2)]
  2. 语法分析（Parsing）：按语法规则递归求值，天然支持运算符优先级

【语法规则（优先级从低到高）】
  expression = term (('+' | '-') term)*        # 加减法（最低优先级）
  term       = unary (('*' | '/' | '//' | '%') unary)*  # 乘除法（较高优先级）
  unary      = '-' unary | atom                # 一元负号（最高优先级）
  atom       = NUMBER                          # 数字字面量

  这套规则确保 "3+5*2" 正确求值为 13（而非 16），即 * / 优先于 + -。

【支持的运算符】
  +   加法
  -   减法 / 一元负号
  *   乘法
  /   除法
  //  整除（地板除）
  %   取模（求余数）
"""

import logging

logger = logging.getLogger(__name__)


class ExpressionError(ValueError):
    """
    表达式解析或求值过程中发生的错误。

    继承自 ValueError，在以下情况抛出：
    - 表达式语法不正确（如 "3++*"、"3+*5"）
    - 除零错误（如 "10/0"）
    - 遇到不支持的符号（如字母、括号等）
    - 表达式不完整（如 "" 或 "3+"）

    调用方可通过 except ExpressionError 捕获并显示"错误"给用户。
    """
    pass


def evaluate(expression: str) -> float:
    """
    安全求值数学表达式字符串的入口函数。

    本函数是整个模块的唯一公开接口，内部完成词法分析和语法分析两个阶段。
    整个过程不使用 eval()、exec() 或任何动态代码执行，确保安全性。

    Args:
        expression: 数学表达式字符串，如 "3+5*2"、"-10/3"、"100%7"
                    数字可以是整数或小数（如 "3.14*2"）

    Returns:
        计算结果，类型为 float。例如 evaluate("3+5*2") 返回 13.0

    Raises:
        ExpressionError: 表达式格式错误、除零、或包含不支持的符号

    使用示例：
        >>> evaluate("3+5*2")
        13.0
        >>> evaluate("10/3")
        3.3333333333333335
        >>> evaluate("-3+5")
        2.0
        >>> evaluate("10%3")
        1.0
    """
    logger.info("开始解析表达式: %s", expression)

    # 第一阶段：词法分析 —— 将字符串拆分为 token 列表
    tokens = _tokenize(expression)
    logger.debug("词法分析结果: %s", tokens)

    # 第二阶段：语法分析 —— 递归下降解析并求值
    parser = _Parser(tokens)
    result = parser.parse_expression()

    # 检查是否所有 token 都已消费完毕
    # 如果解析结束后仍有剩余 token，说明表达式有多余内容（如 "3+5 7"）
    if parser.pos < len(parser.tokens):
        logger.error("表达式有多余内容: %s, 位置 %d, 剩余 token: %s",
                     expression, parser.pos, parser.tokens[parser.pos:])
        raise ExpressionError(f"意外的符号: {parser.tokens[parser.pos]}")

    logger.info("表达式求值成功: %s = %s", expression, result)
    return result


# ==================== 第一阶段：词法分析（Tokenization） ====================
#
# 词法分析器的任务是将原始字符串逐字符扫描，识别出一个个有意义的"词素"（token）。
# 例如 "3.14+5*2" 会被拆分为：
#   [('NUMBER', 3.14), ('PLUS', '+'), ('NUMBER', 5.0), ('MULTIPLY', '*'), ('NUMBER', 2.0)]
#
# 每个 token 是一个 (类型, 值) 的元组：
#   - ('NUMBER', float)   — 数字字面量
#   - ('PLUS', '+')       — 加号
#   - ('MINUS', '-')      — 减号
#   - ('MULTIPLY', '*')   — 乘号
#   - ('DIVIDE', '/')     — 除号
#   - ('FLOOR_DIVIDE', '//') — 整除号
#   - ('MODULO', '%')     — 取模号

def _tokenize(expression: str) -> list:
    """
    词法分析器：将表达式字符串拆分为 token 列表。

    逐字符扫描输入字符串，跳过空白，识别数字和运算符。
    数字会被解析为 float 类型的值存入 token。

    Args:
        expression: 原始数学表达式字符串

    Returns:
        token 列表，每个元素为 (类型名: str, 值) 的元组

    Raises:
        ExpressionError: 遇到不支持的字符或无效的数字格式

    示例：
        >>> _tokenize("3+5*2")
        [('NUMBER', 3.0), ('PLUS', '+'), ('NUMBER', 5.0), ('MULTIPLY', '*'), ('NUMBER', 2.0)]
        >>> _tokenize("10//3")
        [('NUMBER', 10.0), ('FLOOR_DIVIDE', '//'), ('NUMBER', 3.0)]
    """
    tokens = []       # 存放解析出的 token 列表
    i = 0             # 当前扫描位置
    n = len(expression)  # 表达式总长度

    while i < n:
        ch = expression[i]

        # 跳过空白字符（空格、制表符等），不影响表达式语义
        if ch == ' ':
            i += 1
            continue

        # 识别数字：以数字或小数点开头的连续字符序列
        # 支持整数（"42"）和小数（"3.14"），不支持科学计数法
        if ch.isdigit() or ch == '.':
            num_str = _read_number(expression, i)
            try:
                value = float(num_str)  # 统一转为 float，便于后续计算
            except ValueError:
                logger.error("词法分析失败: 无效的数字 '%s' 在表达式 '%s' 中", num_str, expression)
                raise ExpressionError(f"无效的数字: {num_str}")
            tokens.append(('NUMBER', value))
            i += len(num_str)  # 跳过已读取的数字字符
            continue

        # 识别运算符
        if ch == '+':
            tokens.append(('PLUS', '+'))
            i += 1
        elif ch == '-':
            tokens.append(('MINUS', '-'))
            i += 1
        elif ch == '*':
            tokens.append(('MULTIPLY', '*'))
            i += 1
        elif ch == '/':
            # 需要区分 '/'（除法）和 '//'（整除）
            # 检查下一个字符是否也是 '/'，如果是则组成 '//' 运算符
            if i + 1 < n and expression[i + 1] == '/':
                tokens.append(('FLOOR_DIVIDE', '//'))
                i += 2  # 跳过两个字符
            else:
                tokens.append(('DIVIDE', '/'))
                i += 1
        elif ch == '%':
            tokens.append(('MODULO', '%'))
            i += 1
        else:
            # 遇到字母、括号、特殊符号等不支持的字符，立即报错
            logger.error("词法分析失败: 不支持的符号 '%s' (位置 %d) 在表达式 '%s' 中", ch, i, expression)
            raise ExpressionError(f"不支持的符号: {ch}")

    return tokens


def _read_number(expression: str, start: int) -> str:
    """
    从指定位置开始读取一个完整的数字字符串（含小数点）。

    从 start 位置起，连续读取数字字符和最多一个小数点，
    直到遇到非数字字符为止。返回读取到的数字字符串。

    Args:
        expression: 完整的表达式字符串
        start: 开始读取的位置索引

    Returns:
        数字字符串，如 "3.14"、"42"、"0.5"

    Raises:
        ExpressionError: start 位置不是数字（理论上不应发生，由调用方保证）

    示例：
        >>> _read_number("3.14+5", 0)
        '3.14'
        >>> _read_number("3.14+5", 5)
        '5'
    """
    i = start
    n = len(expression)
    has_dot = False  # 标记是否已遇到小数点，防止出现 "3.14.15" 这样的非法数字

    while i < n:
        ch = expression[i]
        if ch.isdigit():
            i += 1
        elif ch == '.' and not has_dot:
            # 遇到第一个小数点，标记并继续读取
            has_dot = True
            i += 1
        else:
            # 遇到非数字字符（运算符、空白等），停止读取
            break

    # 安全检查：确保至少读取到了一个字符
    if i == start:
        logger.error("读取数字失败: 位置 %d 不是数字字符", start)
        raise ExpressionError("期望数字")

    return expression[start:i]


# ==================== 第二阶段：语法分析（Recursive Descent Parsing） ====================
#
# 递归下降解析器的核心思想：
#   每条语法规则对应一个方法，方法之间通过互相调用来体现优先级关系。
#   低优先级的方法调用高优先级的方法，高优先级的方法先被求值，
#   从而自然地实现了"先乘除后加减"的运算顺序。
#
# 调用链路示例（解析 "3+5*2"）：
#   parse_expression()         → 处理 + -（最低优先级）
#     └→ _parse_term()         → 处理 * / // %（较高优先级）
#         └→ _parse_unary()    → 处理一元负号（最高优先级）
#             └→ _parse_atom() → 读取数字字面量
#
# 这样 "3+5*2" 的求值过程为：
#   1. parse_expression 调用 _parse_term 获取左侧值 3
#   2. 发现 '+' 运算符，再调用 _parse_term 获取右侧值
#   3. _parse_term 内部先解析 5，再发现 '*'，解析 2，计算 5*2=10
#   4. 返回到 parse_expression，计算 3+10=13

class _Parser:
    """
    递归下降解析器，负责按语法规则对 token 列表进行解析和求值。

    语法规则（优先级从低到高）:
        expression = term (('+' | '-') term)*
        term       = unary (('*' | '/' | '//' | '%') unary)*
        unary      = '-' unary | atom
        atom       = NUMBER

    属性:
        tokens: token 列表，由 _tokenize() 生成
        pos:    当前解析位置（指向下一个待消费的 token）
    """

    def __init__(self, tokens: list):
        """
        初始化解析器。

        Args:
            tokens: token 列表，每个元素为 (类型名, 值) 的元组
        """
        self.tokens = tokens
        self.pos = 0  # 当前解析位置，从 0 开始

    def _current(self):
        """
        获取当前 token（不消费）。

        Returns:
            当前 token 元组 (类型, 值)，如果已到末尾则返回 ('EOF', None)

        说明：
            EOF (End Of File) 是解析器中的哨兵值，用于安全地"偷看"下一个 token，
            避免越界访问。当解析器看到 EOF 时，知道表达式已结束。
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', None)

    def _eat(self, expected_type: str):
        """
        消费一个指定类型的 token。

        检查当前 token 的类型是否匹配期望值，匹配则消费（推进 pos），
        不匹配则抛出异常。用于语法分析中验证预期的 token 序列。

        Args:
            expected_type: 期望的 token 类型名，如 'NUMBER'、'PLUS'

        Returns:
            被消费的 token 元组

        Raises:
            ExpressionError: 当前 token 类型与期望不符
        """
        tok = self._current()
        if tok[0] != expected_type:
            logger.error("语法分析失败: 期望 %s，得到 %s (位置 %d)", expected_type, tok[0], self.pos)
            raise ExpressionError(f"期望 {expected_type}，得到 {tok[0]}")
        self.pos += 1
        return tok

    def parse_expression(self) -> float:
        """
        解析并求值整个表达式（最低优先级：加法和减法）。

        语法：expression = term (('+' | '-') term)*

        先调用 _parse_term() 获取左侧项的值，
        然后循环检查是否有 + 或 - 运算符，
        如果有则继续解析右侧项并执行运算。

        Returns:
            表达式的最终计算结果

        示例流程（"3+5*2"）：
          1. left = _parse_term() → 3（term 内部会处理 5*2 得到 10）
             等等，实际是：left = _parse_term() 得到 3
          2. 发现 '+'，right = _parse_term() 得到 10（5*2）
          3. left = 3 + 10 = 13
        """
        left = self._parse_term()

        # 循环处理连续的 + - 运算（左结合）
        while self._current()[0] in ('PLUS', 'MINUS'):
            op = self._current()[0]
            self.pos += 1  # 消费运算符
            right = self._parse_term()  # 解析右侧项
            if op == 'PLUS':
                left = left + right
            else:
                left = left - right

        return left

    def _parse_term(self) -> float:
        """
        解析并求值一个"项"（较高优先级：乘法、除法、整除、取模）。

        语法：term = unary (('*' | '/' | '//' | '%') unary)*

        先调用 _parse_unary() 获取左侧因子，
        然后循环检查是否有 * / // % 运算符，
        如果有则继续解析右侧因子并执行运算。

        Returns:
            项的计算结果

        除零处理：
            当右操作数为 0 时，抛出 ExpressionError("除数不能为零")，
            而非让 Python 抛出 ZeroDivisionError，以提供更友好的错误信息。
        """
        left = self._parse_unary()

        # 循环处理连续的 * / // % 运算（左结合）
        while self._current()[0] in ('MULTIPLY', 'DIVIDE', 'FLOOR_DIVIDE', 'MODULO'):
            op = self._current()[0]
            self.pos += 1  # 消费运算符
            right = self._parse_unary()  # 解析右侧因子

            if op == 'MULTIPLY':
                left = left * right
            elif op == 'DIVIDE':
                # 除法需要检查除零
                if right == 0:
                    logger.error("除零错误: %s / 0", left)
                    raise ExpressionError("除数不能为零")
                left = left / right
            elif op == 'FLOOR_DIVIDE':
                # 整除（地板除）：如 10//3 = 3
                if right == 0:
                    logger.error("除零错误: %s // 0", left)
                    raise ExpressionError("除数不能为零")
                left = left // right
            elif op == 'MODULO':
                # 取模（求余数）：如 10%3 = 1
                if right == 0:
                    logger.error("除零错误: %s %% 0", left)
                    raise ExpressionError("除数不能为零")
                left = left % right

        return left

    def _parse_unary(self) -> float:
        """
        解析并求值一元运算（最高优先级：一元负号）。

        语法：unary = '-' unary | atom

        支持一元负号的递归处理，即可以有多个负号叠加：
          "-3"    → -(3) = -3
          "--3"   → -(-(3)) = 3（双重否定）
          "---3"  → -(-(-(3))) = -3

        通过递归调用自身实现：遇到 '-' 就消费它，然后递归解析后续内容并取反。
        如果当前 token 不是 '-'，则退化为 atom 解析。

        Returns:
            计算结果
        """
        if self._current()[0] == 'MINUS':
            self.pos += 1  # 消费 '-' 符号
            # 递归调用自身，处理可能的多重负号（如 --3）
            return -self._parse_unary()
        return self._parse_atom()

    def _parse_atom(self) -> float:
        """
        解析并返回一个原子值（表达式的最小单元：数字字面量）。

        语法：atom = NUMBER

        原子值是递归的"基本情况"（base case），不再调用其他解析方法，
        直接读取并返回一个数字 token 的值。

        Returns:
            数字的浮点值

        Raises:
            ExpressionError: 当前 token 不是数字（语法错误）
            ExpressionError: 遇到 EOF（表达式不完整，如 "3+5+"）
        """
        tok = self._current()
        if tok[0] == 'NUMBER':
            self.pos += 1  # 消费数字 token
            return tok[1]  # 返回数字的值
        if tok[0] == 'EOF':
            logger.error("表达式不完整: 在位置 %d 遇到 EOF", self.pos)
            raise ExpressionError("表达式不完整")
        # 当前 token 是运算符而非数字，说明语法有误（如 "3+*5"）
        logger.error("语法错误: 期望数字，得到 %s '%s' (位置 %d)", tok[0], tok[1], self.pos)
        raise ExpressionError(f"期望数字，得到 {tok[1]}")
