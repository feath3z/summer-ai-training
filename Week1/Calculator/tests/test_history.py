"""
history.py 单元测试

覆盖路径：
  - add() 追加记录
  - clear() 清空记录
  - entries 属性
  - max_entries 上限裁剪
  - 文件持久化（save/load）
  - 损坏文件 / 不存在文件的容错
"""

import json
import os
import pytest
from calculator.history import HistoryManager


@pytest.fixture
def history(tmp_path):
    """创建一个使用临时目录的 HistoryManager，避免污染真实数据文件。"""
    hm = HistoryManager.__new__(HistoryManager)
    hm.max_entries = 50
    hm._dir = str(tmp_path)
    hm._filepath = os.path.join(str(tmp_path), "calculator_history.json")
    hm._entries = []
    return hm


@pytest.fixture
def history_with_file(tmp_path):
    """创建一个已有历史文件的 HistoryManager。"""
    filepath = os.path.join(str(tmp_path), "calculator_history.json")
    data = [
        {"time": "2024-01-01 10:00:00", "expression": "1+1", "result": "2"},
        {"time": "2024-01-02 11:00:00", "expression": "3*4", "result": "12"},
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)

    hm = HistoryManager.__new__(HistoryManager)
    hm.max_entries = 50
    hm._dir = str(tmp_path)
    hm._filepath = filepath
    hm._entries = hm._load.__func__(hm)  # 手动调用 _load
    return hm


# ============================================================
# add()
# ============================================================

class TestAdd:
    """添加记录"""

    def test_add_single_entry(self, history):
        history.add("1+1", "2")
        assert len(history.entries) == 1
        assert history.entries[0]["expression"] == "1+1"
        assert history.entries[0]["result"] == "2"

    def test_add_has_time_field(self, history):
        history.add("2*3", "6")
        assert "time" in history.entries[0]
        # 格式应为 YYYY-MM-DD HH:MM:SS
        assert len(history.entries[0]["time"]) == 19

    def test_add_multiple_entries(self, history):
        history.add("1+1", "2")
        history.add("2+2", "4")
        history.add("3+3", "6")
        assert len(history.entries) == 3

    def test_add_persists_to_file(self, history):
        history.add("5*5", "25")
        with open(history._filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["expression"] == "5*5"


# ============================================================
# clear()
# ============================================================

class TestClear:
    """清空记录"""

    def test_clear_empties_entries(self, history):
        history.add("1+1", "2")
        history.add("2+2", "4")
        history.clear()
        assert history.entries == []

    def test_clear_persists_empty_list(self, history):
        history.add("1+1", "2")
        history.clear()
        with open(history._filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == []

    def test_clear_when_already_empty(self, history):
        # 不应报错
        history.clear()
        assert history.entries == []


# ============================================================
# max_entries 上限
# ============================================================

class TestMaxEntries:
    """记录数量上限裁剪"""

    def test_exceeds_max_trims_oldest(self, history):
        history.max_entries = 3
        for i in range(5):
            history.add(f"{i}+1", str(i + 1))
        # save() 裁剪后应只剩最后 3 条
        assert len(history.entries) == 3
        # 最早的两条应被裁掉
        assert history.entries[0]["expression"] == "2+1"
        assert history.entries[1]["expression"] == "3+1"
        assert history.entries[2]["expression"] == "4+1"

    def test_exact_max_not_trimmed(self, history):
        history.max_entries = 2
        history.add("1+1", "2")
        history.add("2+2", "4")
        assert len(history.entries) == 2


# ============================================================
# 文件加载（_load）
# ============================================================

class TestLoad:
    """从文件加载历史"""

    def test_load_existing_file(self, history_with_file):
        assert len(history_with_file.entries) == 2
        assert history_with_file.entries[0]["expression"] == "1+1"

    def test_load_nonexistent_file(self, tmp_path):
        """文件不存在时返回空列表。"""
        hm = HistoryManager.__new__(HistoryManager)
        hm.max_entries = 50
        hm._dir = str(tmp_path)
        hm._filepath = os.path.join(str(tmp_path), "nonexistent.json")
        hm._entries = hm._load.__func__(hm)
        assert hm._entries == []

    def test_load_corrupt_json(self, tmp_path):
        """文件内容不是合法 JSON 时返回空列表。"""
        filepath = os.path.join(str(tmp_path), "calculator_history.json")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("not valid json {{{")

        hm = HistoryManager.__new__(HistoryManager)
        hm.max_entries = 50
        hm._dir = str(tmp_path)
        hm._filepath = filepath
        hm._entries = hm._load.__func__(hm)
        assert hm._entries == []

    def test_load_non_list_json(self, tmp_path):
        """文件内容是合法 JSON 但不是列表时返回空列表。"""
        filepath = os.path.join(str(tmp_path), "calculator_history.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"not": "a list"}, f)

        hm = HistoryManager.__new__(HistoryManager)
        hm.max_entries = 50
        hm._dir = str(tmp_path)
        hm._filepath = filepath
        hm._entries = hm._load.__func__(hm)
        assert hm._entries == []


# ============================================================
# entries 属性
# ============================================================

class TestEntries:
    """entries 属性行为"""

    def test_entries_returns_list(self, history):
        assert isinstance(history.entries, list)

    def test_entries_empty_initially(self, history):
        assert history.entries == []

    def test_entries_is_same_reference(self, history):
        """多次访问应返回同一列表对象（UI 依赖此特性）。"""
        assert history.entries is history.entries
