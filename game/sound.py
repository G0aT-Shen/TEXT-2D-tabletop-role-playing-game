"""程序化音效系统 — 用 pygame.mixer 生成音效，零外部音频文件."""

import pygame
import math
import struct
from typing import Optional


class SoundManager:
    """程序化音效管理器。"""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self._init_sounds()

    def _init_sounds(self):
        """初始化所有音效。"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        if not self.enabled:
            return

        # 生成所有音效
        self.sounds["dice"] = self._make_dice_sound()
        self.sounds["hit"] = self._make_hit_sound()
        self.sounds["crit"] = self._make_crit_sound()
        self.sounds["heal"] = self._make_heal_sound()
        self.sounds["victory"] = self._make_victory_sound()
        self.sounds["defeat"] = self._make_defeat_sound()
        self.sounds["select"] = self._make_select_sound()
        self.sounds["confirm"] = self._make_confirm_sound()
        self.sounds["levelup"] = self._make_levelup_sound()
        self.sounds["achievement"] = self._make_achievement_sound()
        self.sounds["boss"] = self._make_boss_sound()
        self.sounds["shop"] = self._make_shop_sound()

    def _make_tone(self, freq: float, duration: float, volume: float = 0.3,
                   wave_type: str = "sine") -> Optional[pygame.mixer.Sound]:
        """生成一个简单音调。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            if wave_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == "saw":
                val = 2 * (t * freq - math.floor(t * freq + 0.5))
            else:
                val = math.sin(2 * math.pi * freq * t)
            # 淡入淡出
            fade = 1.0
            fade_samples = min(int(sample_rate * 0.02), num_samples // 4)
            if i < fade_samples:
                fade = i / max(1, fade_samples)
            elif i > num_samples - fade_samples:
                fade = (num_samples - i) / max(1, fade_samples)
            val *= volume * fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_noise(self, duration: float, volume: float = 0.2,
                    freq_filter: float = 0.5) -> Optional[pygame.mixer.Sound]:
        """生成噪音（用于骰子、打击声）。"""
        if not self.enabled:
            return None
        import random as rng
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        samples = []
        prev = 0
        for i in range(num_samples):
            raw = rng.uniform(-1, 1)
            # 简单低通滤波
            filtered = prev + freq_filter * (raw - prev)
            prev = filtered
            # 淡出
            fade = max(0, 1.0 - i / num_samples)
            val = filtered * volume * fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_sweep(self, start_freq: float, end_freq: float, duration: float,
                    volume: float = 0.3) -> Optional[pygame.mixer.Sound]:
        """生成频率扫描（用于升级、治疗）。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            progress = t / duration
            freq = start_freq + (end_freq - start_freq) * progress
            val = math.sin(2 * math.pi * freq * t)
            fade = 1.0
            fade_samples = min(int(sample_rate * 0.03), num_samples // 4)
            if i < fade_samples:
                fade = i / max(1, fade_samples)
            elif i > num_samples - fade_samples:
                fade = (num_samples - i) / max(1, fade_samples)
            val *= volume * fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _samples_to_sound(self, samples: list) -> Optional[pygame.mixer.Sound]:
        """将浮点采样列表转换为 pygame Sound 对象。"""
        if not self.enabled or not samples:
            return None
        try:
            # 转换为 16-bit 整数
            int_samples = []
            for s in samples:
                val = max(-1.0, min(1.0, s))
                int_val = int(val * 32767)
                int_samples.append(struct.pack('h', int_val))
                int_samples.append(struct.pack('h', int_val))  # 双声道
            sound = pygame.mixer.Sound(buffer=b''.join(int_samples))
            return sound
        except Exception:
            return None

    # ── 具体音效 ──

    def _make_dice_sound(self):
        """骰子声 — 短促的木块碰撞。"""
        if not self.enabled:
            return None
        return self._make_noise(0.15, 0.15, freq_filter=0.3)

    def _make_hit_sound(self):
        """攻击命中 — 低频闷响。"""
        if not self.enabled:
            return None
        return self._make_tone(120, 0.12, 0.35, "sine")

    def _make_crit_sound(self):
        """暴击 — 高频锐响 + 低频冲击。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 0.25)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            val = (math.sin(2 * math.pi * 800 * t) * 0.2 +
                   math.sin(2 * math.pi * 150 * t) * 0.3)
            fade = max(0, 1.0 - t / 0.25)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_heal_sound(self):
        """治疗 — 上升音调。"""
        return self._make_sweep(400, 800, 0.3, 0.25)

    def _make_victory_sound(self):
        """胜利 — 和弦上升。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 0.6)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            val = (math.sin(2 * math.pi * 523 * t) * 0.15 +  # C
                   math.sin(2 * math.pi * 659 * t) * 0.15 +  # E
                   math.sin(2 * math.pi * 784 * t) * 0.15)   # G
            fade = 1.0
            if i < sample_rate * 0.05:
                fade = i / (sample_rate * 0.05)
            elif i > num_samples - sample_rate * 0.1:
                fade = (num_samples - i) / (sample_rate * 0.1)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_defeat_sound(self):
        """失败 — 下降音调。"""
        return self._make_sweep(400, 100, 0.5, 0.3)

    def _make_select_sound(self):
        """菜单选择 — 短促 blip。"""
        return self._make_tone(600, 0.05, 0.15, "square")

    def _make_confirm_sound(self):
        """确认 — 双音 blip。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 0.12)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            freq = 600 if t < 0.06 else 900
            val = math.sin(2 * math.pi * freq * t) * 0.2
            fade = max(0, 1.0 - abs(t - 0.06) / 0.06)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_levelup_sound(self):
        """升级 — 上升和弦。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 0.8)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            freq1 = 523 + t * 200  # 上升
            val = (math.sin(2 * math.pi * freq1 * t) * 0.15 +
                   math.sin(2 * math.pi * (freq1 * 1.5) * t) * 0.1)
            fade = 1.0
            if i > num_samples - sample_rate * 0.15:
                fade = (num_samples - i) / (sample_rate * 0.15)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_achievement_sound(self):
        """成就解锁 — 华丽和弦。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 0.7)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            val = (math.sin(2 * math.pi * 659 * t) * 0.12 +  # E
                   math.sin(2 * math.pi * 880 * t) * 0.12 +  # A
                   math.sin(2 * math.pi * 1047 * t) * 0.12)  # C
            fade = 1.0
            if i < sample_rate * 0.03:
                fade = i / (sample_rate * 0.03)
            elif i > num_samples - sample_rate * 0.15:
                fade = (num_samples - i) / (sample_rate * 0.15)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_boss_sound(self):
        """Boss 出场 — 低频轰鸣。"""
        if not self.enabled:
            return None
        sample_rate = 22050
        num_samples = int(sample_rate * 1.0)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            val = math.sin(2 * math.pi * 60 * t) * 0.3
            val += math.sin(2 * math.pi * 80 * t) * 0.2
            fade = 1.0
            if i < sample_rate * 0.1:
                fade = i / (sample_rate * 0.1)
            val *= fade
            samples.append(val)
        return self._samples_to_sound(samples)

    def _make_shop_sound(self):
        """商店 — 清脆铃声。"""
        return self._make_tone(1200, 0.1, 0.15, "sine")

    # ── 播放接口 ──

    def play(self, name: str):
        """播放指定音效。"""
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.stop()
            snd.play()

    def toggle(self):
        """切换音效开关。"""
        self.enabled = not self.enabled
        if self.enabled and not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            except Exception:
                self.enabled = False
        elif not self.enabled and pygame.mixer.get_init():
            pygame.mixer.stop()
