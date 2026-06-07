"""
小餅餅丶的简易计算器2.0 - 增强版
==================================

程序入口文件。

运行方式：
    python main.py

启动流程：
    1. 从 calculator 包导入 Calculator 类
    2. 实例化 Calculator —— 自动创建窗口、构建界面、加载历史记录
    3. 进入 tkinter 主事件循环（mainloop），等待用户操作
    4. 用户关闭窗口后，程序自动退出

依赖：
    - Python 3（标准库即可，无需安装第三方包）
    - tkinter（Python 自带的 GUI 库，标准 CPython 发行版已包含）
"""

from calculator.calculator import Calculator


if __name__ == "__main__":
    # 实例化 Calculator 会自动完成所有初始化并启动 GUI
    Calculator()
