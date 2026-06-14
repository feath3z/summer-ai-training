"""
计算器主应用类（calculator.py）
==============================

本模块是计算器应用的核心，包含 Calculator 类，负责：
  1. 状态管理：维护显示值、表达式 token 列表、记忆存储等运行时状态
  2. 业务逻辑：处理数字输入、运算符、等号计算、科学函数等操作
  3. 模块组合：导入并协调 expression（表达式求值）、history（历史记录）、ui（界面）三个模块

【设计模式：回调映射】
  Calculator 类通过 callbacks 字典将自己的方法暴露给 UI 模块。
  UI 模块不直接依赖 Calculator 类，只通过回调函数名（字符串键）调用业务逻辑。
  这种松耦合设计使得 UI 和逻辑可以独立修改，互不影响。

  callbacks = {
      'press_num': self.press_num,      # UI 按下数字键时调用
      'press_operator': self.press_operator,  # UI 按下运算符时调用
      ...
  }

【状态变量说明】
  self.result       — tkinter.StringVar，绑定到显示屏，用户看到的数字
  self.tokens       — list[str]，累积的表达式 token，如 ['3', '+', '5', '*']
  self.ispresssign  — bool，上一次按键是否为运算符（用于检测连续运算符）
  self.memory       — float，记忆存储的数值（MC/MR/MS/M+/M- 功能）
  self.is_radian    — bool，角度模式 False=角度制 True=弧度制
  self.pending_power — bool，是否处于幂运算等待输入指数的状态
  self.temp_value   — float，幂运算的底数（用户按 x^y 时暂存当前值）

【表达式求值流程（以 "3+5*2=" 为例）】
  1. 用户按 '3'  → press_num('3')      → 显示屏: "3"
  2. 用户按 '+'  → press_operator('+')  → tokens: ['3', '+'], 显示屏不变
  3. 用户按 '5'  → press_num('5')       → 显示屏: "5"
  4. 用户按 '*'  → press_operator('*')  → tokens: ['3', '+', '5', '*']
  5. 用户按 '2'  → press_num('2')       → 显示屏: "2"
  6. 用户按 '='  → press_equal()        → tokens: ['3', '+', '5', '*', '2']
                                           → 拼接为 "3+5*2"
                                           → expression.evaluate("3+5*2") = 13.0
                                           → 显示屏: "13"
"""

import logging
import tkinter
import math
import tkinter.messagebox

from . import expression
from .expression import ExpressionError
from .history import HistoryManager
from . import ui

logger = logging.getLogger(__name__)


class Calculator:
    """
    增强版计算器主类。

    整合基本运算、科学计算、历史记录、记忆功能，
    是整个应用的入口和核心控制器。

    实例化后自动创建窗口、构建界面并进入主事件循环。
    """

    def __init__(self):
        """
        初始化计算器：创建窗口、设置状态变量、构建界面、启动事件循环。

        初始化顺序：
        1. 创建 tkinter 主窗口并设置尺寸限制
        2. 初始化所有状态变量（显示值、token 列表、记忆等）
        3. 加载历史记录管理器
        4. 构建回调映射表
        5. 通过 ui 模块构建菜单栏、主界面和科学计算按钮
        6. 进入 tkinter 主事件循环（阻塞，直到窗口关闭）
        """
        # ==================== 创建主窗口 ====================
        self.root = tkinter.Tk()
        self.root.minsize(306, 510)    # 最小窗口尺寸（防止缩小后按钮重叠）
        self.root.maxsize(350, 560)    # 最大窗口尺寸（计算器不需要全屏）
        self.root.title('小餅餅丶的简易计算器2.0 - 增强版')

        # ==================== 初始化状态变量 ====================

        # 显示屏变量：绑定到界面的 Label 控件，修改此变量会自动更新显示
        # 初始值 "0" 表示计算器启动时显示屏显示 0
        self.result = tkinter.StringVar(value="0")

        # 表达式 token 列表：累积用户输入的数字和运算符
        # 例如用户输入 "3+5*2=" 后，列表为 ['3', '+', '5', '*', '2']
        # 按等号后拼接为字符串送给表达式解析器求值
        self.tokens = []

        # 运算符标志：上一次按键是否为运算符
        # 用途1：按运算符后，下一次按数字会清屏（覆盖显示的数字）
        # 用途2：检测连续按运算符的情况，此时替换而非追加
        self.ispresssign = False

        # 记忆存储：MC/MR/MS/M+/M- 功能使用的数值
        # MC: 清零 memory
        # MR: 将 memory 的值读到显示屏
        # MS: 将显示屏的值存入 memory
        # M+: 将显示屏的值加到 memory
        # M-: 将显示屏的值从 memory 减去
        self.memory = 0.0

        # 角度/弧度模式：影响三角函数的输入解释
        # False = 角度制（degrees）：sin(90) = 1.0
        # True  = 弧度制（radians）：sin(π/2) = 1.0
        self.is_radian = False

        # 幂运算状态（修复：在 __init__ 中初始化，避免使用 hasattr 检查）
        # 当用户按 x^y 按钮时，pending_power 设为 True，等待用户输入指数
        # 按等号时检测到 pending_power 为 True，执行 temp_value ** current_value
        self.pending_power = False
        self.temp_value = 0.0

        # 历史记录管理器：负责将计算记录持久化到 JSON 文件
        self.history_manager = HistoryManager()

        # ==================== 构建回调映射表 ====================
        # 将 Calculator 的方法以字符串键映射的方式暴露给 UI 模块。
        # UI 模块通过 callbacks['press_num'] 调用 self.press_num，
        # 无需直接导入或引用 Calculator 类，实现解耦。
        callbacks = {
            # 数字和基本运算
            'press_num': self.press_num,          # 数字键 (0-9, .)
            'press_operator': self.press_operator, # 运算符键 (+, -, *, /, %)
            'press_equal': self.press_equal,       # 等号键 (=)
            'delete_one': self.delete_one,         # 退格键 (←)
            'toggle_sign': self.toggle_sign,       # 正负号切换 (±)
            'reciprocal': self.reciprocal,         # 倒数 (1/x)
            'square_root': self.square_root,       # 平方根 (√)
            'clear_all': self.clear_all,           # 全部清除 (C)
            'clear_entry': self.clear_entry,       # 清除当前输入 (CE)
            # 记忆功能
            'mc': self.mc,       # Memory Clear - 清除记忆
            'mr': self.mr,       # Memory Recall - 读取记忆
            'ms': self.ms,       # Memory Store - 存入记忆
            'm_add': self.m_add, # Memory Add - 加到记忆
            'm_sub': self.m_sub, # Memory Subtract - 从记忆减去
            # 科学计算
            'sin': self.sin_func,     # 正弦函数
            'cos': self.cos_func,     # 余弦函数
            'tan': self.tan_func,     # 正切函数
            'log': self.log_func,     # 常用对数（以10为底）
            'ln': self.ln_func,       # 自然对数（以e为底）
            'power': self.power_func, # 幂运算 (x^y)
            'toggle_radian': self.toggle_radian,  # 角度/弧度切换
            # 辅助功能
            'show_history': self.show_history,       # 显示历史记录窗口
            'copy_result': self.copy_result,         # 复制结果到剪贴板
            'clear_history': self.clear_history_record,  # 清空历史记录
            'show_date_calc': self.show_date_calculator, # 日期计算器
            'show_help': self.show_help,             # 显示帮助
            'show_about': self.show_about,           # 显示关于信息
        }

        # ==================== 构建界面 ====================
        # 依次调用 ui 模块的构建函数，传入窗口和回调映射
        # 注意：科学计算按钮（sin/cos/tan/log/ln/x^y）已融入 build_main_layout 中
        ui.build_menu(self.root, callbacks)              # 菜单栏
        ui.build_main_layout(self.root, self.result, callbacks)  # 主界面（含科学按钮）

        # ==================== 启动主事件循环 ====================
        # mainloop() 是 tkinter 的阻塞调用，持续监听用户操作（点击、键盘等），
        # 直到窗口被关闭。窗口关闭后程序自动退出。
        logger.info("计算器初始化完成，进入主事件循环")
        self.root.mainloop()

    # ==================== 格式化工具 ====================

    def _format_result(self, value: float) -> str:
        """
        将计算结果格式化为适合在显示屏上显示的字符串。

        格式化策略：
        - 整数值（如 3.0）→ 显示为 "3"（去掉小数点，更美观）
        - 大整数值（绝对值 < 10^15）→ 显示为整数形式
        - 其他浮点数 → 使用 12 位有效数字格式化（:.12g）

        为什么用 :.12g 而非 str()[:12]？
        原始代码使用 str(result)[:12] 直接截取字符串前 12 个字符，
        这会导致：
        - 负数的负号占用一个字符位，实际有效数字只有 11 位
        - 科学计数法表示时可能截断指数部分（如 "-1.23456789e+" 丢失数字）
        - 无法做数值舍入，只是粗暴截断

        f'{value:.12g}' 会：
        - 保留 12 位有效数字（不是 12 个字符）
        - 自动去除尾部多余的零
        - 使用科学计数法表示极大/极小数（如 1e+20）
        - 数值舍入而非字符串截断

        Args:
            value: 计算结果的浮点数值

        Returns:
            格式化后的字符串，适合直接显示在计算器屏幕上
        """
        # 整数值直接显示为整数字符串，去掉 ".0" 后缀
        # 条件：值等于其整数形式 且 绝对值不超过 10^15（避免 int 转换精度问题）
        if isinstance(value, float) and value == int(value) and abs(value) < 1e15:
            return str(int(value))
        # 浮点数使用 12 位有效数字格式化
        return f'{value:.12g}'

    # ==================== 核心计算逻辑 ====================

    def press_num(self, num: str):
        """
        处理数字键输入（0-9 和小数点）。

        输入规则：
        1. 如果上一次按键是运算符（ispresssign=True），清屏后显示新数字
           例：按 "3" "+" 后再按 "5"，显示屏从 "3" 变为 "5"（而非 "35"）
        2. 小数点规则：
           - 当前数字已包含小数点则忽略（防止出现 "3.14.15"）
           - 当前为 "0" 时按小数点显示 "0."（而非 ".0"）
        3. 当前显示为 "0" 或 "错误" 时，直接替换为新数字
        4. 其他情况将新数字追加到末尾（如 "3" + "5" = "35"）

        Args:
            num: 用户按下的数字字符，如 '0'-'9' 或 '.'
        """
        # 如果上一次按键是运算符，需要清屏开始输入新数字
        if self.ispresssign:
            self.result.set("0")
            self.ispresssign = False

        # 小数点特殊处理
        if num == '.':
            current = self.result.get()
            if '.' in current:
                return  # 已有小数点，忽略本次输入
            if current == '0':
                self.result.set('0.')  # 从 "0" 开始小数，显示 "0." 而非 "."
                return

        # 数字拼接逻辑
        oldnum = self.result.get()
        if oldnum == '0' or oldnum == '错误':
            # 初始状态或错误状态，直接替换
            self.result.set(str(num))
            logger.debug("数字输入: %s (替换模式)", num)
        else:
            # 追加到已有数字末尾（如 "3" + "5" = "35"）
            self.result.set(oldnum + str(num))
            logger.debug("数字输入: %s (追加模式, 当前值: %s)", num, oldnum + str(num))

    def press_operator(self, sign: str):
        """
        处理运算符键输入（+, -, *, /, %）。

        操作逻辑：
        1. 如果当前显示为"错误"，重置状态后返回
        2. 如果上一次按键也是运算符（连续运算符），替换最后一个运算符
           例：按 "3" "+" 后再按 "-"，tokens 从 ['3', '+'] 变为 ['3', '-']
           （修复了原始代码中连续运算符导致表达式非法的 bug）
        3. 正常情况：将当前显示值和运算符加入 token 列表

        Args:
            sign: 运算符字符，如 '+'、'-'、'*'、'/'、'%'
        """
        num = self.result.get()

        # 错误状态下按运算符：重置为初始状态
        if num == '错误':
            self.result.set('0')
            self.tokens.clear()
            return

        # 连续按运算符时，替换最后一个运算符（而非追加）
        # 这样 "5 + - * 3" 会被正确处理为 "5 * 3"
        if self.ispresssign and self.tokens:
            self.tokens[-1] = sign
            return

        # 正常情况：将当前显示值和运算符依次加入 token 列表
        # 例：显示 "3" 按 "+"，tokens 变为 ['3', '+']
        self.tokens.append(str(num))
        self.tokens.append(sign)
        self.ispresssign = True  # 标记上一次按键为运算符
        logger.debug("运算符输入: %s, 当前表达式: %s", sign, ''.join(self.tokens))

    def press_equal(self):
        """
        处理等号键输入，执行最终计算。

        计算流程：
        1. 检查是否处于幂运算模式（pending_power=True）
           → 是则调用 power_execute() 计算 x^y
        2. 检查当前显示是否为"错误"→ 是则重置
        3. 将当前显示值追加到 token 列表末尾
        4. 拼接所有 token 为表达式字符串（如 ['3', '+', '5'] → "3+5"）
        5. 调用 expression.evaluate() 安全求值（替代原始的 eval()）
        6. 格式化结果并显示
        7. 记录到历史
        8. 清空 token 列表，准备下一次计算

        错误处理：
        - ExpressionError: 表达式语法错误或除零，显示"错误"
        - ValueError/OverflowError: 数值溢出（如 10^1000），显示"错误"
        """
        try:
            # 幂运算模式：用户之前按了 x^y，现在输入指数后按等号
            if self.pending_power:
                self.power_execute()
                self.pending_power = False
                return

            # 错误状态下按等号：重置为初始状态
            curnum = self.result.get()
            if curnum == '错误':
                self.result.set('0')
                self.tokens.clear()
                return

            # 将当前显示值追加到 token 列表，完成表达式构建
            # 例：tokens 为 ['3', '+']，当前显示 "5"，拼接后为 "3+5"
            self.tokens.append(str(curnum))
            calculatestr = ''.join(self.tokens)

            # 使用安全的表达式解析器求值（替代原始的 eval()）
            # expression.evaluate() 使用递归下降解析器，不会执行任意代码
            result = expression.evaluate(calculatestr)
            result_str = self._format_result(result)

            # 更新显示并记录历史
            self.result.set(result_str)
            self.history_manager.add(calculatestr, result_str)

            # 清空 token 列表，准备下一次计算
            self.tokens.clear()
            self.ispresssign = True  # 等号后按数字会清屏开始新输入
            logger.info("计算成功: %s = %s", calculatestr, result_str)

        except ExpressionError as e:
            # 表达式解析错误（语法错误、除零等）
            self.result.set('错误')
            self.tokens.clear()
            logger.error("表达式解析失败: %s, 输入: %s", e, calculatestr)
        except (ValueError, OverflowError) as e:
            # 数值错误（如溢出）
            self.result.set('错误')
            self.tokens.clear()
            logger.error("数值计算错误: %s, 输入: %s", e, calculatestr)

    def delete_one(self):
        """
        处理退格键（←），删除显示屏数字的最后一个字符。

        规则：
        - 当前为空、"0" 或"错误"→ 重置为 "0"
        - 多位数 → 删除最后一个字符（如 "314" → "31"）
        - 只剩一位 → 重置为 "0"（如 "3" → "0"）
        """
        current = self.result.get()
        if current == '' or current == '0' or current == '错误':
            self.result.set('0')
        elif len(current) > 1:
            # 删除最后一个字符
            self.result.set(current[:-1])
        else:
            self.result.set('0')

    def toggle_sign(self):
        """
        处理正负号切换键（±）。

        将显示屏数字取反：
        - 正数 → 负数（"314" → "-314"）
        - 负数 → 正数（"-314" → "314"）
        - "0" 或"错误"→ 不做操作
        """
        strnum = self.result.get()
        if strnum != '错误' and strnum != '0':
            if strnum.startswith('-'):
                # 已有负号，去掉负号（变正）
                self.result.set(strnum[1:])
            else:
                # 无负号，加上负号（变负）
                self.result.set('-' + strnum)

    def reciprocal(self):
        """
        处理倒数键（1/x），计算当前显示值的倒数。

        计算公式：result = 1 / x
        特殊情况：x = 0 时除零，显示"错误"

        计算完成后清空 token 列表，因为倒数是一个完整的即时运算，
        不参与后续的多步表达式构建。
        """
        try:
            num = float(self.result.get())
            if num == 0:
                self.result.set('错误')
                logger.warning("倒数运算失败: 除零错误, 输入: %s", num)
                return
            result = 1 / num
            result_str = self._format_result(result)
            self.result.set(result_str)
            self.history_manager.add(f"1/({num})", result_str)
            self.tokens.clear()       # 即时运算，清空表达式
            self.ispresssign = True   # 标记为运算符后状态，防止数字追加
            logger.info("倒数运算成功: 1/(%s) = %s", num, result_str)
        except ValueError as e:
            self.result.set('错误')
            logger.error("倒数运算失败: %s, 输入: %s", e, self.result.get())

    def clear_all(self):
        """
        处理全部清除键（C），重置所有状态到初始值。

        清除内容：
        1. 清空 token 列表
        2. 显示屏重置为 "0"
        3. 运算符标志重置为 False
        4. 幂运算状态重置（修复了原始代码中状态残留的 bug）

        注意：clear_all 与 clear_entry 的区别：
        - C（clear_all）：清除一切，包括已输入的表达式
        - CE（clear_entry）：只清除当前正在输入的数字，保留已有表达式
        """
        self.tokens.clear()
        self.result.set("0")
        self.ispresssign = False
        self.pending_power = False
        self.temp_value = 0.0
        logger.debug("全部清除: 状态已重置")

    def clear_entry(self):
        """
        处理清除当前输入键（CE），只清除显示屏上正在输入的数字。

        与 clear_all（C）不同，CE 不清空已有的 token 列表。
        例：输入 "3+5" 后按 CE，tokens 仍为 ['3', '+']，显示屏变为 "0"
        用户可以重新输入一个数字来替换刚才的 "5"。
        """
        self.result.set("0")
        self.ispresssign = False
        logger.debug("清除当前输入: 显示已重置为 0")

    def square_root(self):
        """
        处理平方根键（√），计算当前显示值的平方根。

        计算公式：result = √x = math.sqrt(x)
        特殊情况：x < 0 时实数范围内无解，显示"错误"

        计算完成后作为即时运算处理，清空 token 列表。
        """
        try:
            num = float(self.result.get())
            if num < 0:
                self.result.set('错误')
                logger.warning("平方根运算失败: 负数输入 %s", num)
                return
            result = math.sqrt(num)
            result_str = self._format_result(result)
            self.result.set(result_str)
            self.history_manager.add(f"√({num})", result_str)
            self.tokens.clear()
            self.ispresssign = True
            logger.info("平方根运算成功: √(%s) = %s", num, result_str)
        except ValueError as e:
            self.result.set('错误')
            logger.error("平方根运算失败: %s, 输入: %s", e, self.result.get())

    # ==================== 科学计算功能 ====================

    def _apply_unary_func(self, name: str, math_func, display_fmt: str):
        """
        科学函数的通用处理逻辑（模板方法）。

        所有一元科学函数（sin、cos、tan、log、ln）的处理流程相同：
        1. 读取当前显示值
        2. 根据函数类型做预处理（如角度转弧度、检查负数）
        3. 调用对应的 math 模块函数
        4. 格式化并显示结果
        5. 记录到历史

        通过参数化消除了 5 个几乎相同的函数之间的代码重复。

        Args:
            name: 函数名称标识，如 'sin'、'cos'、'tan'、'log'、'ln'
                  用于判断是否需要角度转换或负数检查
            math_func: 对应的 math 模块函数，如 math.sin、math.cos、math.log10
            display_fmt: 历史记录中显示的表达式格式，如 "sin(45)"、"log10(100)"
        """
        try:
            num = float(self.result.get())

            # 角度制→弧度制转换：三角函数在角度模式下需要先将角度转为弧度
            # math 模块的三角函数默认使用弧度制
            # math.radians(90) = π/2 ≈ 1.5708
            if name in ('sin', 'cos', 'tan') and not self.is_radian:
                num = math.radians(num)

            # 对数函数输入检查：log(x) 和 ln(x) 要求 x > 0
            # x <= 0 时实数范围内无解，显示"错误"
            # （修复了原始代码中依赖 bare except 捕获 math.log 异常的问题）
            if name in ('log', 'ln') and num <= 0:
                self.result.set('错误')
                logger.warning("%s 运算失败: 非正数输入 %s", name, num)
                return

            result = math_func(num)
            result_str = self._format_result(result)
            self.result.set(result_str)
            self.history_manager.add(display_fmt, result_str)
            logger.info("%s 运算成功: %s = %s", name, display_fmt, result_str)
        except ValueError as e:
            # math 函数可能抛出 ValueError（如 math.sqrt 对负数）
            self.result.set('错误')
            logger.error("%s 运算失败: %s, 输入: %s", name, e, self.result.get())

    def sin_func(self):
        """正弦函数：计算 sin(x)。角度模式下 x 为角度，弧度模式下 x 为弧度。"""
        self._apply_unary_func('sin', math.sin, f"sin({self.result.get()})")

    def cos_func(self):
        """余弦函数：计算 cos(x)。角度模式下 x 为角度，弧度模式下 x 为弧度。"""
        self._apply_unary_func('cos', math.cos, f"cos({self.result.get()})")

    def tan_func(self):
        """正切函数：计算 tan(x)。角度模式下 x 为角度，弧度模式下 x 为弧度。"""
        self._apply_unary_func('tan', math.tan, f"tan({self.result.get()})")

    def log_func(self):
        """常用对数：计算 log₁₀(x)，要求 x > 0。"""
        self._apply_unary_func('log', math.log10, f"log10({self.result.get()})")

    def ln_func(self):
        """自然对数：计算 ln(x) = logₑ(x)，要求 x > 0。"""
        self._apply_unary_func('ln', math.log, f"ln({self.result.get()})")

    def power_func(self):
        """
        幂运算的第一步：记录底数，等待用户输入指数。

        x^y 是一个二元运算（需要两个输入），处理流程分两步：
        1. 用户按 x^y → 调用本函数，将当前显示值暂存为底数（temp_value），
           设置 pending_power=True 表示正在等待指数输入
        2. 用户输入指数后按 = → 调用 press_equal()，检测到 pending_power=True，
           调用 power_execute() 计算 temp_value ** current_value
        """
        try:
            num = float(self.result.get())
            self.temp_value = num       # 暂存底数
            self.result.set(str(num))   # 显示屏保持不变
            self.ispresssign = True     # 标记为运算符后状态，等待指数输入
            self.pending_power = True   # 进入幂运算等待模式
            logger.info("幂运算模式: 底数 = %s, 等待输入指数", num)
        except ValueError as e:
            self.result.set("错误")
            logger.error("幂运算设置失败: %s, 输入: %s", e, self.result.get())

    def power_execute(self):
        """
        幂运算的第二步：执行 x^y 的计算。

        当用户在幂运算模式下按等号时被调用。
        使用 self.temp_value（底数）和当前显示屏值（指数）计算幂。
        计算公式：result = temp_value ** current_value

        错误处理：
        - ValueError: 无效运算（如 (-2)^0.5，负数的非整数次幂）
        - OverflowError: 结果过大（如 10^1000）
        """
        try:
            num = float(self.result.get())
            result = self.temp_value ** num  # 幂运算
            result_str = self._format_result(result)
            self.result.set(result_str)
            self.history_manager.add(f"{self.temp_value}^{num}", result_str)
            self.tokens.clear()
            self.ispresssign = True
            logger.info("幂运算成功: %s^%s = %s", self.temp_value, num, result_str)
        except (ValueError, OverflowError) as e:
            self.result.set("错误")
            logger.error("幂运算失败: %s, 底数: %s, 指数: %s", e, self.temp_value, self.result.get())

    def toggle_radian(self):
        """
        切换角度/弧度模式。

        影响所有三角函数（sin、cos、tan）对输入值的解释：
        - 角度模式（默认）：sin(90) = 1.0
        - 弧度模式：sin(1.5708) ≈ 1.0

        切换后弹出提示框告知用户当前模式。
        """
        self.is_radian = not self.is_radian
        mode = "弧度" if self.is_radian else "角度"
        logger.info("角度模式切换: 当前为 %s 模式", mode)
        tkinter.messagebox.showinfo("模式切换", f"已切换到{mode}模式")

    # ==================== 记忆功能 ====================
    # 记忆功能模拟了实体计算器上的 M 键系列，提供一个独立的存储空间，
    # 可以在多步计算中间暂存和复用数值。

    def mc(self):
        """Memory Clear — 清除记忆存储，将 memory 重置为 0。"""
        self.memory = 0.0
        logger.info("记忆操作: MC — 记忆已清零")

    def mr(self):
        """
        Memory Recall — 读取记忆值到显示屏。
        将 memory 中存储的数值显示在屏幕上，供用户在后续计算中使用。
        """
        self.result.set(self._format_result(self.memory))
        logger.info("记忆操作: MR — 读取记忆值 %s", self.memory)

    def ms(self):
        """
        Memory Store — 将当前显示屏值存入记忆。
        覆盖 memory 中原有的值（如果有）。
        如果当前显示为"错误"则忽略操作（修复了原始代码的崩溃 bug）。
        """
        value = self.result.get()
        if value == '错误':
            logger.warning("记忆操作: MS 失败 — 当前显示为错误状态")
            return  # 错误状态下不执行存储，防止 float("错误") 崩溃
        self.memory = float(value)
        logger.info("记忆操作: MS — 存入 %s", value)

    def m_add(self):
        """
        Memory Add — 将当前显示屏值累加到记忆。
        计算公式：memory = memory + current_value
        如果当前显示为"错误"则忽略操作。
        """
        value = self.result.get()
        if value == '错误':
            logger.warning("记忆操作: M+ 失败 — 当前显示为错误状态")
            return
        self.memory += float(value)
        logger.info("记忆操作: M+ — 累加 %s, 记忆值: %s", value, self.memory)

    def m_sub(self):
        """
        Memory Subtract — 将当前显示屏值从记忆中减去。
        计算公式：memory = memory - current_value
        如果当前显示为"错误"则忽略操作。
        """
        value = self.result.get()
        if value == '错误':
            logger.warning("记忆操作: M- 失败 — 当前显示为错误状态")
            return
        self.memory -= float(value)
        logger.info("记忆操作: M- — 累减 %s, 记忆值: %s", value, self.memory)

    # ==================== 辅助功能 ====================

    def copy_result(self):
        """
        复制当前显示屏值到系统剪贴板。
        使用 tkinter 的剪贴板接口：先清空剪贴板，再写入当前值。
        复制完成后弹出提示框。
        """
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result.get())
        logger.info("复制结果到剪贴板: %s", self.result.get())
        tkinter.messagebox.showinfo("提示", "已复制到剪贴板")

    def clear_history_record(self):
        """
        清空所有历史记录。
        通过 HistoryManager 清空内存和文件中的记录。
        此操作不可撤销。
        """
        self.history_manager.clear()
        logger.info("历史记录已清空")
        tkinter.messagebox.showinfo("提示", "历史记录已清空")

    def show_history(self):
        """
        打开历史记录查看窗口。
        委托给 ui 模块的 build_history_window() 创建独立窗口。
        传入 _clear_history_from_window 回调，允许从历史窗口内部清空记录。
        """
        ui.build_history_window(
            self.root,
            self.history_manager.entries,
            on_clear=self._clear_history_from_window
        )

    def _clear_history_from_window(self):
        """
        从历史记录窗口触发的清空操作。
        清空记录后弹出提示框，告知用户操作完成。
        """
        self.history_manager.clear()
        logger.info("历史记录已清空 (从历史窗口触发)")
        tkinter.messagebox.showinfo("提示", "历史记录已清空")

    def show_date_calculator(self):
        """
        打开日期计算器窗口。
        委托给 ui 模块的 build_date_window() 创建独立窗口。
        传入 history_manager 以便日期计算结果也能被记录到历史。
        """
        ui.build_date_window(self.root, self.history_manager)

    def show_help(self):
        """显示使用帮助信息，介绍计算器的各项功能和快捷键。"""
        help_text = """计算器2.0使用帮助：

1. 基本运算：+ - * / // %
2. 科学计算：sin, cos, tan, log, ln, x^y
3. 记忆功能：MC(清空记忆), MR(读取), MS(存入), M+(累加), M-(累减)
4. 历史记录：自动保存，可查看和清空
5. 日期计算：菜单栏→查看→日期计算

快捷键：
Ctrl+C - 复制结果
        """
        tkinter.messagebox.showinfo("帮助", help_text)

    def show_about(self):
        """显示关于信息，包含版本号和功能列表。"""
        about_text = """小餅餅丶的简易计算器2.0
增强版 v2.0

新增功能：
- 科学计算器 (sin/cos/tan/log/ln/x^y)
- 历史记录自动保存
- 日期计算工具
- 角度/弧度切换
- 记忆功能 (MC/MR/MS/M+/M-)

© 2024 小餅餅丶
        """
        tkinter.messagebox.showinfo("关于", about_text)
