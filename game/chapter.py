"""章节管理 — 四大章节的流程控制."""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

from .event import Event, EventType, Choice


@dataclass
class Chapter:
    """章节数据。"""
    chapter_id: int
    title: str
    subtitle: str
    intro_text: str
    events: List[Event] = field(default_factory=list)
    is_final: bool = False


class ChapterManager:
    """章节管理器。"""

    def __init__(self):
        self.chapters: List[Chapter] = []
        self.current_chapter_index: int = 0
        self.current_event_index: int = 0
        self.flags: Dict[str, object] = {}  # 全局标记
        self._load_chapters()

    def _load_chapters(self):
        """加载所有章节数据。"""
        from .story.chapter1 import get_chapter1
        from .story.chapter2 import get_chapter2
        from .story.chapter3 import get_chapter3
        from .story.chapter4 import get_chapter4

        self.chapters = [
            get_chapter1(),
            get_chapter2(),
            get_chapter3(),
            get_chapter4(),
        ]
        # 防御：跳过初始 conditional 不匹配的事件，防止软锁
        self._skip_invalid_events()

    @property
    def current_chapter(self) -> Optional[Chapter]:
        if 0 <= self.current_chapter_index < len(self.chapters):
            return self.chapters[self.current_chapter_index]
        return None

    @property
    def current_event(self) -> Optional[Event]:
        ch = self.current_chapter
        if ch and 0 <= self.current_event_index < len(ch.events):
            event = ch.events[self.current_event_index]
            # 检查触发条件
            if event.required_flags:
                for key, val in event.required_flags.items():
                    if self.flags.get(key) != val:
                        return None
            return event
        return None

    @property
    def is_chapter_complete(self) -> bool:
        ch = self.current_chapter
        return ch is not None and self.current_event_index >= len(ch.events)

    @property
    def is_game_complete(self) -> bool:
        return self.current_chapter_index >= len(self.chapters)

    def advance_event(self):
        """推进到下一个事件（跳过不符合条件的事件）。"""
        self.current_event_index += 1
        ch = self.current_chapter
        if not ch:
            return
        # 直接访问事件列表跳过不匹配的 required_flags
        while self.current_event_index < len(ch.events):
            event = ch.events[self.current_event_index]
            if event.required_flags:
                if not all(self.flags.get(k) == v for k, v in event.required_flags.items()):
                    self.current_event_index += 1
                    continue
            break

    def advance_chapter(self):
        """推进到下一章节。"""
        self.current_chapter_index += 1
        self.current_event_index = 0
        # 跳过新章节中 conditional 不匹配的事件，防止软锁
        self._skip_invalid_events()

    def _skip_invalid_events(self):
        """跳过当前索引处 conditional 不匹配的事件。"""
        ch = self.current_chapter
        if not ch:
            return
        while self.current_event_index < len(ch.events):
            event = ch.events[self.current_event_index]
            if event.required_flags:
                if not all(self.flags.get(k) == v for k, v in event.required_flags.items()):
                    self.current_event_index += 1
                    continue
            break

    def set_flag(self, key: str, value: object):
        self.flags[key] = value

    def get_flag(self, key: str, default=None):
        return self.flags.get(key, default)

    def to_dict(self) -> dict:
        """序列化章节管理器数据。flags 中的复杂类型会被 JSON 编码。"""
        import json
        serialized_flags = {}
        for k, v in self.flags.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                serialized_flags[k] = v
            else:
                # 尝试 JSON 序列化复杂类型
                try:
                    serialized_flags[k] = json.dumps(v)
                except (TypeError, ValueError):
                    # 最后尝试 repr，至少保留可读信息
                    serialized_flags[k] = repr(v)
        return {
            "current_chapter_index": self.current_chapter_index,
            "current_event_index": self.current_event_index,
            "flags": serialized_flags,
        }

    def from_dict(self, data: dict):
        self.current_chapter_index = data["current_chapter_index"]
        self.current_event_index = data["current_event_index"]
        self.flags = data.get("flags", {})
