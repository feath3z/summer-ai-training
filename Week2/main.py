"""
小餅餅丶的简易计算器2.0 - 增强版
==================================

程序入口文件。

运行方式：
    python main.py

启动流程：
    1. 配置日志系统（输出到控制台和 calculator.log 文件）
    2. 从 calculator 包导入 Calculator 类
    3. 实例化 Calculator —— 自动创建窗口、构建界面、加载历史记录
    4. 进入 tkinter 主事件循环（mainloop），等待用户操作
    5. 用户关闭窗口后，程序自动退出

依赖：
    - Python 3（标准库即可，无需安装第三方包）
    - tkinter（Python 自带的 GUI 库，标准 CPython 发行版已包含）
"""

import logging
import os

from calculator.calculator import Calculator


def setup_logging():
    """
    配置日志系统。

    日志格式：
        时间戳    级别    来源模块                  线程     消息
        2024-01-15 10:30:45,123 INFO  calculator.calculator [main] 计算结果: 3+5 = 8.0

    输出目标：
        1. 控制台（标准输出）— 便于开发调试
        2. 文件 calculator.log — 持久化记录，便于事后分析
    """
    log_format = "%(asctime)s %(levelname)-5s %(name)-28s [%(threadName)s] %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"

    # 日志文件路径：与 main.py 同级目录
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_filepath = os.path.join(log_dir, "calculator.log")

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=log_datefmt,
        handlers=[
            logging.StreamHandler(),                          # 控制台输出
            logging.FileHandler(log_filepath, encoding="utf-8"),  # 文件输出
        ],
    )

    logging.info("日志系统已初始化，日志文件: %s", log_filepath)


if __name__ == "__main__":
    setup_logging()
    # 实例化 Calculator 会自动完成所有初始化并启动 GUI
    Calculator()
