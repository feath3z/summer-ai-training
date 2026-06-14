"""
历史记录管理器（history.py）
===========================

本模块负责计算器历史记录的持久化存储，将用户的每次计算操作记录到 JSON 文件中。

【设计要点】
  1. 使用绝对路径：基于 __file__（本模块文件的位置）计算历史文件路径，
     确保无论从哪个目录启动程序，历史文件始终保存在项目目录下。
     （修复了原始代码使用相对路径导致历史文件散落各处的问题）

  2. 精确异常捕获：只捕获 json.JSONDecodeError、OSError、ValueError 等具体异常，
     而非原始代码中的裸 except（会吞掉 KeyboardInterrupt 等不应被捕获的异常）。

  3. 记录上限：默认最多保留 50 条记录，超出时自动裁剪最旧的记录，
     防止文件无限增长。

【记录格式】
  每条记录是一个字典，包含三个字段：
  {
      "time": "2024-01-15 14:30:25",   # 计算时间
      "expression": "3+5*2",           # 计算表达式
      "result": "13"                   # 计算结果
  }

【文件位置】
  历史文件名为 calculator_history.json，保存在本模块所在目录下。
  路径通过 __file__ 动态计算，不依赖当前工作目录。
"""

import json
import logging
import os
import datetime

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    计算器历史记录管理器。

    负责历史记录的加载、保存、添加和清空操作。
    内部维护一个记录列表，所有变更都会自动同步到 JSON 文件。

    使用示例：
        hm = HistoryManager()           # 自动加载已有历史
        hm.add("3+5*2", "13")           # 添加一条记录
        entries = hm.entries             # 获取所有记录
        hm.clear()                       # 清空所有记录
    """

    def __init__(self, max_entries: int = 50):
        """
        初始化历史记录管理器。

        初始化过程：
        1. 计算历史文件的绝对路径（基于本模块文件位置）
        2. 尝试从文件加载已有历史记录
        3. 如果文件不存在或损坏，初始化为空列表

        Args:
            max_entries: 最大保留记录数，默认 50。
                         当记录超过此数量时，自动裁剪最旧的记录。
        """
        self.max_entries = max_entries

        # 使用 os.path.abspath(__file__) 获取本模块的绝对路径，
        # 再用 os.path.dirname 提取目录部分。
        # 这样无论从哪个目录启动程序（如 python /some/other/dir/main.py），
        # 历史文件始终保存在 calculator 包所在的目录下。
        self._dir = os.path.dirname(os.path.abspath(__file__))
        self._filepath = os.path.join(self._dir, "calculator_history.json")

        # 启动时立即加载已有历史记录
        self._entries = self._load()

    @property
    def entries(self) -> list:
        """
        获取历史记录列表的只读引用。

        返回的列表按时间顺序排列（最旧的在前，最新的在后）。
        UI 模块显示时可以通过 reversed() 倒序显示（最新在前）。

        Returns:
            历史记录列表，每个元素为 {"time": ..., "expression": ..., "result": ...} 字典
        """
        return self._entries

    def _load(self) -> list:
        """
        从 JSON 文件加载历史记录。

        加载逻辑：
        1. 检查文件是否存在
        2. 读取并解析 JSON
        3. 验证数据类型是否为列表
        4. 任何环节失败都返回空列表（不中断程序启动）

        Returns:
            历史记录列表，加载失败时返回空列表 []

        异常处理说明：
            - json.JSONDecodeError: 文件内容不是有效的 JSON 格式
            - OSError: 文件读取失败（权限不足、磁盘错误等）
            - ValueError: JSON 解析成功但数据格式不符合预期
            以上异常均被捕获并静默处理，返回空列表，确保程序正常启动。
        """
        try:
            if os.path.exists(self._filepath):
                logger.info("正在加载历史记录文件: %s", self._filepath)
                with open(self._filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 防御性检查：确保加载的数据确实是列表类型
                # （如果文件被手动修改为其他 JSON 类型，如字典或字符串，不应崩溃）
                if isinstance(data, list):
                    logger.info("历史记录加载成功: %d 条记录", len(data))
                    return data
                else:
                    logger.warning("历史文件数据格式异常: 期望 list，得到 %s，将使用空列表", type(data).__name__)
            else:
                logger.info("历史记录文件不存在，将创建新文件: %s", self._filepath)
        except json.JSONDecodeError as e:
            logger.error("历史文件 JSON 解析失败: %s, 文件: %s", e, self._filepath)
        except OSError as e:
            logger.error("历史文件读取失败: %s, 文件: %s", e, self._filepath)
        except ValueError as e:
            logger.error("历史文件数据格式错误: %s, 文件: %s", e, self._filepath)
        return []

    def save(self):
        """
        将当前历史记录列表保存到 JSON 文件。

        保存前会检查记录数量，超过 max_entries 时只保留最近的记录。
        使用 utf-8 编码以正确保存中文字符，ensure_ascii=False 允许中文直接写入
        （而非转义为 \\uXXXX 形式），提高文件可读性。

        异常处理说明：
            - OSError: 文件写入失败（磁盘满、权限不足等）
            此时静默失败，不影响计算器的正常使用。
        """
        try:
            # 超过上限时，只保留最近的 max_entries 条记录
            # 切片 [-max_entries:] 取列表末尾的 N 个元素
            if len(self._entries) > self.max_entries:
                logger.info("历史记录超过上限 (%d > %d)，裁剪旧记录", len(self._entries), self.max_entries)
                self._entries = self._entries[-self.max_entries:]
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
            logger.debug("历史记录保存成功: %d 条记录, 文件: %s", len(self._entries), self._filepath)
        except OSError as e:
            logger.error("历史文件写入失败: %s, 文件: %s", e, self._filepath)

    def add(self, expression: str, result: str):
        """
        添加一条计算记录并自动保存到文件。

        每次用户完成一次计算（按等号、执行科学函数等），都会调用此方法
        将计算过程和结果记录下来。

        Args:
            expression: 计算表达式字符串，如 "3+5*2"、"sin(45)"、"√(16)"
            result: 计算结果字符串，如 "13"、"0.707106781187"

        示例：
            hm.add("3+5*2", "13")
            # 记录：{"time": "2024-01-15 14:30:25", "expression": "3+5*2", "result": "13"}
        """
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._entries.append({
            "time": time_str,
            "expression": expression,
            "result": result
        })
        logger.debug("新增历史记录: %s = %s (时间: %s)", expression, result, time_str)
        self.save()

    def clear(self):
        """
        清空所有历史记录并保存到文件。

        调用后文件内容变为空列表 "[]"，内存中的记录也被清空。
        此操作不可撤销（记录一旦清空无法恢复）。
        """
        count = len(self._entries)
        self._entries.clear()
        logger.info("清空历史记录: 共删除 %d 条记录", count)
        self.save()
