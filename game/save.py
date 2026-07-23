"""存档系统 — JSON格式存档/读档（支持双人）。"""

import json
import os
from datetime import datetime
from typing import Optional, Dict

SAVE_DIR = "saves"
MAX_SLOTS = 3


def ensure_save_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def save_game(slot: int, player_dict: dict, chapter_dict: dict,
              player2_dict: dict = None) -> bool:
    """保存游戏到指定槽位（1-3）。"""
    if slot < 1 or slot > MAX_SLOTS:
        return False

    ensure_save_dir()
    data = {
        "version": 2,
        "timestamp": datetime.now().isoformat(),
        "multiplayer": player2_dict is not None,
        "player": player_dict,
        "player2": player2_dict,
        "chapter": chapter_dict,
    }
    path = os.path.join(SAVE_DIR, f"save_{slot}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True


def load_game(slot: int) -> Optional[Dict]:
    """从指定槽位读取存档。"""
    if slot < 1 or slot > MAX_SLOTS:
        return None

    path = os.path.join(SAVE_DIR, f"save_{slot}.json")
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_save_info(slot: int) -> Optional[Dict]:
    """获取存档信息（不读取完整数据）。"""
    data = load_game(slot)
    if data is None:
        return None
    is_mp = data.get("multiplayer", False) or data.get("player2") is not None
    p1_name = data.get("player", {}).get("name", "未知")
    p2_name = ""
    if is_mp and data.get("player2"):
        p2_name = " & " + data["player2"].get("name", "未知")
    return {
        "slot": slot,
        "timestamp": data.get("timestamp", "未知"),
        "player_name": p1_name + p2_name,
        "player_class": data.get("player", {}).get("char_class", "未知"),
        "level": data.get("player", {}).get("level", 1),
        "chapter": data.get("chapter", {}).get("current_chapter_index", 0) + 1,
        "multiplayer": is_mp,
    }


def delete_save(slot: int) -> bool:
    """删除存档。"""
    path = os.path.join(SAVE_DIR, f"save_{slot}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def list_saves() -> list:
    """列出所有存档信息。"""
    result = []
    for slot in range(1, MAX_SLOTS + 1):
        info = get_save_info(slot)
        if info:
            result.append(info)
    return result
