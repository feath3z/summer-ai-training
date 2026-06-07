"""
UI 布局模块

负责所有 tkinter 控件的创建与布局。通过 callbacks 字典绑定回调，
自身不含任何业务逻辑。各 build_* 函数由 Calculator 调用组装界面。
"""

import tkinter
import datetime
from typing import Dict, List, Callable


def build_menu(root: tkinter.Tk, callbacks: Dict[str, Callable]) -> None:
    """构建顶部菜单栏（查看 / 编辑 / 科学 / 帮助）。"""
    allmenu = tkinter.Menu(root)

    # ── 查看：历史记录、日期计算 ──
    view_menu = tkinter.Menu(allmenu, tearoff=0)
    view_menu.add_command(label='历史记录(Y)', command=callbacks['show_history'])
    view_menu.add_separator()
    view_menu.add_command(label='日期计算(D)', command=callbacks['show_date_calc'])
    allmenu.add_cascade(label='查看(V)', menu=view_menu)

    # ── 编辑：复制、清空历史 ──
    edit_menu = tkinter.Menu(allmenu, tearoff=0)
    edit_menu.add_command(label='复制(C)', command=callbacks['copy_result'])
    edit_menu.add_separator()
    edit_menu.add_command(label='清除历史记录', command=callbacks['clear_history'])
    allmenu.add_cascade(label='编辑(E)', menu=edit_menu)

    # ── 科学：角度/弧度切换 ──
    science_menu = tkinter.Menu(allmenu, tearoff=0)
    science_menu.add_command(label='角度/弧度切换', command=callbacks['toggle_radian'])
    allmenu.add_cascade(label='科学(S)', menu=science_menu)

    # ── 帮助：使用说明、关于 ──
    help_menu = tkinter.Menu(allmenu, tearoff=0)
    help_menu.add_command(label='查看帮助(V)', command=callbacks['show_help'])
    help_menu.add_separator()
    help_menu.add_command(label='关于计算器(A)', command=callbacks['show_about'])
    allmenu.add_cascade(label='帮助(H)', menu=help_menu)

    root.config(menu=allmenu)


def build_main_layout(
    root: tkinter.Tk,
    result_var: tkinter.StringVar,
    callbacks: Dict[str, Callable]
) -> None:
    """
    构建计算器主界面布局（科学按钮已融入主布局，共9行）。

    布局矩阵（5列 × 9行）：

    ┌──────┬──────┬──────┬──────┬──────┐
    │ 显示屏（占满整行）                    │  第0行
    ├──────┼──────┼──────┼──────┼──────┤
    │ MC   │ MR   │ MS   │ M+   │ M-   │  第1行
    ├──────┼──────┼──────┼──────┼──────┤
    │ ←    │ CE   │ C    │ ±    │ √    │  第2行
    ├──────┼──────┼──────┼──────┼──────┤
    │ sin  │ cos  │ tan  │ /    │ %    │  第3行
    ├──────┼──────┼──────┼──────┼──────┤
    │ log  │ ln   │ x^y  │ *    │ 1/x  │  第4行
    ├──────┼──────┼──────┼──────┼──────┤
    │ 7    │ 8    │ 9    │ -    │      │  第5行
    ├──────┼──────┼──────┼──────┼──────┤
    │ 4    │ 5    │ 6    │ +    │ =    │  第6行
    ├──────┼──────┼──────┼──────┼──────┤
    │ 1    │ 2    │ 3    │      │      │  第7行（=跨第5-8行）
    ├──────┼──────┼──────┼──────┼──────┤
    │ 0    │ .    │      │      │      │  第8行（0跨3列）
    └──────┴──────┴──────┴──────┴──────┘
    """
    # ── 布局常量 ──
    BTN_W = 55      # 按钮宽度 (px)
    BTN_H = 45      # 按钮高度 (px)
    GAP = 5         # 按钮间距 (px)
    START_X = 5     # 首列起始 X
    DISP_Y = 20     # 显示屏起始 Y
    ROW1_Y = DISP_Y + 75  # 第1行 Y（显示屏 70px + 间距 5px）

    def col_x(col: int) -> int:
        """返回第 col 列（0-4）的 X 坐标。"""
        return START_X + col * (BTN_W + GAP)

    def row_y(row: int) -> int:
        """返回第 row 行（从 1 开始）的 Y 坐标。"""
        return ROW1_Y + (row - 1) * (BTN_H + GAP)

    # ── 第0行：显示屏 ──
    show_label = tkinter.Label(
        root, bd=3, bg='white', font=('宋体', 30),
        anchor='e', textvariable=result_var
    )
    show_label.place(x=START_X, y=DISP_Y, width=5 * BTN_W + 4 * GAP, height=70)

    # ── 第1行：记忆键 (MC / MR / MS / M+ / M-) ──
    btn_mc = tkinter.Button(root, text='MC', command=callbacks['mc'])
    btn_mc.place(x=col_x(0), y=row_y(1), width=BTN_W, height=BTN_H)

    btn_mr = tkinter.Button(root, text='MR', command=callbacks['mr'])
    btn_mr.place(x=col_x(1), y=row_y(1), width=BTN_W, height=BTN_H)

    btn_ms = tkinter.Button(root, text='MS', command=callbacks['ms'])
    btn_ms.place(x=col_x(2), y=row_y(1), width=BTN_W, height=BTN_H)

    btn_m_add = tkinter.Button(root, text='M+', command=callbacks['m_add'])
    btn_m_add.place(x=col_x(3), y=row_y(1), width=BTN_W, height=BTN_H)

    btn_m_sub = tkinter.Button(root, text='M-', command=callbacks['m_sub'])
    btn_m_sub.place(x=col_x(4), y=row_y(1), width=BTN_W, height=BTN_H)

    # ── 第2行：退格 / 清除 / 正负号 / 开方 ──
    btn_back = tkinter.Button(root, text='←', command=callbacks['delete_one'])
    btn_back.place(x=col_x(0), y=row_y(2), width=BTN_W, height=BTN_H)

    btn_ce = tkinter.Button(root, text='CE', command=callbacks['clear_entry'])
    btn_ce.place(x=col_x(1), y=row_y(2), width=BTN_W, height=BTN_H)

    btn_c = tkinter.Button(root, text='C', command=callbacks['clear_all'])
    btn_c.place(x=col_x(2), y=row_y(2), width=BTN_W, height=BTN_H)

    btn_sign = tkinter.Button(root, text='±', command=callbacks['toggle_sign'])
    btn_sign.place(x=col_x(3), y=row_y(2), width=BTN_W, height=BTN_H)

    btn_sqrt = tkinter.Button(root, text='√', command=callbacks['square_root'])
    btn_sqrt.place(x=col_x(4), y=row_y(2), width=BTN_W, height=BTN_H)

    # ── 第3行：三角函数 / 除 / 取余 ──
    btn_sin = tkinter.Button(root, text='sin', command=callbacks['sin'], bg='#E0E0E0')
    btn_sin.place(x=col_x(0), y=row_y(3), width=BTN_W, height=BTN_H)

    btn_cos = tkinter.Button(root, text='cos', command=callbacks['cos'], bg='#E0E0E0')
    btn_cos.place(x=col_x(1), y=row_y(3), width=BTN_W, height=BTN_H)

    btn_tan = tkinter.Button(root, text='tan', command=callbacks['tan'], bg='#E0E0E0')
    btn_tan.place(x=col_x(2), y=row_y(3), width=BTN_W, height=BTN_H)

    btn_divide = tkinter.Button(root, text='/', command=lambda: callbacks['press_operator']('/'))
    btn_divide.place(x=col_x(3), y=row_y(3), width=BTN_W, height=BTN_H)

    btn_percent = tkinter.Button(root, text='%', command=lambda: callbacks['press_operator']('%'))
    btn_percent.place(x=col_x(4), y=row_y(3), width=BTN_W, height=BTN_H)

    # ── 第4行：对数 / 幂运算 / 乘 / 倒数 ──
    btn_log = tkinter.Button(root, text='log', command=callbacks['log'], bg='#E0E0E0')
    btn_log.place(x=col_x(0), y=row_y(4), width=BTN_W, height=BTN_H)

    btn_ln = tkinter.Button(root, text='ln', command=callbacks['ln'], bg='#E0E0E0')
    btn_ln.place(x=col_x(1), y=row_y(4), width=BTN_W, height=BTN_H)

    btn_power = tkinter.Button(root, text='x^y', command=callbacks['power'], bg='#FFD700')
    btn_power.place(x=col_x(2), y=row_y(4), width=BTN_W, height=BTN_H)

    btn_multiply = tkinter.Button(root, text='*', command=lambda: callbacks['press_operator']('*'))
    btn_multiply.place(x=col_x(3), y=row_y(4), width=BTN_W, height=BTN_H)

    btn_reciprocal = tkinter.Button(root, text='1/x', command=callbacks['reciprocal'])
    btn_reciprocal.place(x=col_x(4), y=row_y(4), width=BTN_W, height=BTN_H)

    # ── 第5行：7 / 8 / 9 / 减 ──
    btn_7 = tkinter.Button(root, text='7', command=lambda: callbacks['press_num']('7'))
    btn_7.place(x=col_x(0), y=row_y(5), width=BTN_W, height=BTN_H)

    btn_8 = tkinter.Button(root, text='8', command=lambda: callbacks['press_num']('8'))
    btn_8.place(x=col_x(1), y=row_y(5), width=BTN_W, height=BTN_H)

    btn_9 = tkinter.Button(root, text='9', command=lambda: callbacks['press_num']('9'))
    btn_9.place(x=col_x(2), y=row_y(5), width=BTN_W, height=BTN_H)

    btn_minus = tkinter.Button(root, text='-', command=lambda: callbacks['press_operator']('-'))
    btn_minus.place(x=col_x(3), y=row_y(5), width=BTN_W, height=BTN_H)

    # = 按钮：跨越第5-8行，占据整列高度
    btn_equal = tkinter.Button(root, text='=', command=callbacks['press_equal'])
    btn_equal.place(x=col_x(4), y=row_y(5), width=BTN_W, height=BTN_H * 4 + GAP * 3)

    # ── 第6行：4 / 5 / 6 / 加 ──
    btn_4 = tkinter.Button(root, text='4', command=lambda: callbacks['press_num']('4'))
    btn_4.place(x=col_x(0), y=row_y(6), width=BTN_W, height=BTN_H)

    btn_5 = tkinter.Button(root, text='5', command=lambda: callbacks['press_num']('5'))
    btn_5.place(x=col_x(1), y=row_y(6), width=BTN_W, height=BTN_H)

    btn_6 = tkinter.Button(root, text='6', command=lambda: callbacks['press_num']('6'))
    btn_6.place(x=col_x(2), y=row_y(6), width=BTN_W, height=BTN_H)

    btn_plus = tkinter.Button(root, text='+', command=lambda: callbacks['press_operator']('+'))
    btn_plus.place(x=col_x(3), y=row_y(6), width=BTN_W, height=BTN_H)

    # ── 第7行：1 / 2 / 3 ──
    btn_1 = tkinter.Button(root, text='1', command=lambda: callbacks['press_num']('1'))
    btn_1.place(x=col_x(0), y=row_y(7), width=BTN_W, height=BTN_H)

    btn_2 = tkinter.Button(root, text='2', command=lambda: callbacks['press_num']('2'))
    btn_2.place(x=col_x(1), y=row_y(7), width=BTN_W, height=BTN_H)

    btn_3 = tkinter.Button(root, text='3', command=lambda: callbacks['press_num']('3'))
    btn_3.place(x=col_x(2), y=row_y(7), width=BTN_W, height=BTN_H)

    # ── 第8行：0（跨3列）/ 小数点 ──
    btn_0 = tkinter.Button(root, text='0', command=lambda: callbacks['press_num']('0'))
    btn_0.place(x=col_x(0), y=row_y(8), width=BTN_W * 3 + GAP * 2, height=BTN_H)

    btn_dot = tkinter.Button(root, text='.', command=lambda: callbacks['press_num']('.'))
    btn_dot.place(x=col_x(3), y=row_y(8), width=BTN_W, height=BTN_H)


def build_history_window(
    root: tkinter.Tk,
    entries: List[Dict[str, str]],
    on_clear: Callable
) -> None:
    """弹出历史记录窗口，倒序显示条目，提供清空按钮。"""
    history_window = tkinter.Toplevel(root)
    history_window.title("历史记录")
    history_window.geometry("450x350")
    # transient：依附主窗口，跟随最小化/关闭，始终在主窗口上方
    history_window.transient(root)

    frame = tkinter.Frame(history_window)
    frame.pack(fill=tkinter.BOTH, expand=True, padx=5, pady=5)

    scrollbar = tkinter.Scrollbar(frame)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    listbox = tkinter.Listbox(frame, yscrollcommand=scrollbar.set, font=("宋体", 10))
    listbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    for item in reversed(entries):
        display = f"{item['time']}  |  {item['expression']} = {item['result']}"
        listbox.insert(tkinter.END, display)

    def clear_and_close():
        on_clear()
        history_window.destroy()

    clear_btn = tkinter.Button(history_window, text="清空历史", command=clear_and_close)
    clear_btn.pack(pady=5)


def build_date_window(root: tkinter.Tk, history_manager) -> None:
    """弹出日期计算器窗口，计算两个日期之间的天数差并记录到历史。

    Args:
        root: 主窗口，Toplevel 的父窗口
        history_manager: HistoryManager 实例，用于写入计算结果
    """
    date_window = tkinter.Toplevel(root)
    date_window.title("日期计算器")
    date_window.geometry("300x250")
    # transient：依附主窗口
    date_window.transient(root)

    tkinter.Label(date_window, text="开始日期 (YYYY-MM-DD):").pack(pady=5)
    start_entry = tkinter.Entry(date_window)
    start_entry.pack(pady=5)

    tkinter.Label(date_window, text="结束日期 (YYYY-MM-DD):").pack(pady=5)
    end_entry = tkinter.Entry(date_window)
    end_entry.pack(pady=5)

    result_label = tkinter.Label(date_window, text="相差天数: ")
    result_label.pack(pady=10)

    def calculate_days():
        try:
            start = datetime.datetime.strptime(start_entry.get(), "%Y-%m-%d")
            end = datetime.datetime.strptime(end_entry.get(), "%Y-%m-%d")
            days = (end - start).days
            result_label.config(text=f"相差天数: {abs(days)} 天")
            history_manager.add(
                f"{start_entry.get()}到{end_entry.get()}",
                f"{abs(days)}天"
            )
        except ValueError:
            result_label.config(text="日期格式错误!")

    btn = tkinter.Button(date_window, text="计算", command=calculate_days)
    btn.pack(pady=10)