"""UI渲染系统 — 基于Pygame的文本UI（增强版：粒子、动画、特效）。"""

import pygame
import sys
import math
import random
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass, field

from .character import Character, CharClass, CLASS_STATS
from .event import Event, Choice, EventType
from .combat import Enemy, CombatEngine, CombatAction
from .save import list_saves, get_save_info

# ── 颜色方案（暗黑主题 + 更多渐变色） ──
COLORS = {
    "bg": (15, 10, 30),
    "bg_dark": (5, 5, 15),
    "panel": (25, 18, 45),
    "panel_light": (35, 28, 55),
    "panel_highlight": (45, 38, 65),
    "border": (60, 50, 90),
    "border_bright": (90, 75, 130),
    "text": (220, 215, 230),
    "text_dim": (140, 135, 155),
    "text_bright": (245, 240, 255),
    "gold": (255, 200, 60),
    "gold_bright": (255, 230, 120),
    "gold_dark": (180, 140, 30),
    "red": (255, 80, 80),
    "red_dark": (180, 40, 40),
    "red_bright": (255, 120, 120),
    "green": (80, 220, 100),
    "green_dark": (40, 150, 60),
    "blue": (80, 160, 255),
    "blue_dark": (40, 100, 200),
    "purple": (160, 100, 255),
    "purple_dark": (100, 60, 180),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "hp_bar": (200, 40, 40),
    "hp_bar_bright": (255, 60, 60),
    "hp_bar_dark": (80, 10, 10),
    "mp_bar": (40, 100, 200),
    "mp_bar_bright": (60, 140, 255),
    "mp_bar_dark": (15, 40, 80),
    "xp_bar": (60, 180, 100),
    "xp_bar_bright": (80, 220, 120),
    "xp_bar_dark": (20, 80, 40),
    "highlight": (80, 60, 140),
    "boss_red": (220, 30, 30),
    "boss_glow": (255, 50, 50, 100),
    "star": (180, 170, 210),
    "star_bright": (240, 235, 255),
}

WIDTH, HEIGHT = 1024, 700
PANEL_WIDTH = 300
TEXT_AREA_WIDTH = WIDTH - PANEL_WIDTH - 40
SIDEBAR_X = WIDTH - PANEL_WIDTH


# ═══════════════════════════════════════════════
# 粒子系统
# ═══════════════════════════════════════════════

@dataclass
class Particle:
    """单个粒子。"""
    x: float
    y: float
    vx: float
    vy: float
    life: float          # 剩余生命 0~1
    max_life: float = 1.0
    size: float = 2.0
    color: Tuple[int, int, int] = (255, 255, 255)
    gravity: float = 0.0
    decay_type: str = "linear"  # linear, ease, spark

    def alive(self) -> bool:
        return self.life > 0

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt / self.max_life

    def alpha(self) -> int:
        """当前透明度。"""
        if self.decay_type == "ease":
            t = self.life
            return int(255 * t * t)
        elif self.decay_type == "spark":
            t = self.life
            return int(255 * (1.0 - abs(t - 0.5) * 2.0))
        return int(255 * self.life)


class ParticleSystem:
    """粒子系统管理器。"""

    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x: float, y: float, count: int = 10,
             speed: float = 80.0, spread: float = 360.0,
             color: Tuple[int, int, int] = (255, 255, 255),
             size: float = 2.0, life: float = 1.0,
             gravity: float = 0.0, decay: str = "linear"):
        """在位置 (x, y) 发射 count 个粒子。"""
        for _ in range(count):
            angle = random.uniform(0, math.radians(spread) if spread <= 360 else math.pi * 2)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - spd * 0.3  # 略微向上偏移
            self.particles.append(Particle(
                x=x, y=y, vx=vx, vy=vy,
                life=1.0, max_life=life + random.uniform(0, life * 0.5),
                size=size + random.uniform(-size * 0.5, size * 0.5),
                color=color, gravity=gravity, decay_type=decay
            ))

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.alive()]
        for p in self.particles:
            p.update(dt)

    def draw(self, screen: pygame.Surface):
        for p in self.particles:
            alpha = min(255, max(0, p.alpha()))
            if alpha < 5:
                continue
            r, g, b = p.color
            radius = max(0.5, p.size * p.life)
            # 用带透明的表面来绘制
            surf = pygame.Surface((int(radius * 2) + 2, int(radius * 2) + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (r, g, b, alpha),
                               (int(radius) + 1, int(radius) + 1), radius)
            screen.blit(surf, (p.x - radius, p.y - radius))

    def clear(self):
        self.particles.clear()


# ═══════════════════════════════════════════════
# 浮动伤害/治疗数字
# ═══════════════════════════════════════════════

@dataclass
class FloatingText:
    """浮动文字（伤害/治疗/状态）。"""
    x: float
    y: float
    text: str
    color: Tuple[int, int, int]
    life: float = 1.0
    max_life: float = 1.0
    rise_speed: float = 60.0

    def alive(self) -> bool:
        return self.life > 0

    def update(self, dt: float):
        self.y -= self.rise_speed * dt
        self.life -= dt / self.max_life


class FloatingTextSystem:
    """浮动文字管理器。"""

    def __init__(self):
        self.texts: List[FloatingText] = []

    def spawn(self, x: float, y: float, text: str, color: Tuple[int, int, int]):
        self.texts.append(FloatingText(x=x, y=y, text=text, color=color))

    def update(self, dt: float):
        self.texts = [t for t in self.texts if t.alive()]
        for t in self.texts:
            t.update(dt)

    def draw(self, screen: pygame.Surface, font):
        for t in self.texts:
            alpha = min(255, max(0, int(255 * t.life)))
            r, g, b = t.color
            surf = font.render(t.text, True, (r, g, b))
            alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(surf, (0, 0))
            alpha_surf.set_alpha(alpha)
            screen.blit(alpha_surf, (t.x - surf.get_width() // 2, t.y))

    def clear(self):
        self.texts.clear()


# ═══════════════════════════════════════════════
# 屏幕震动系统
# ═══════════════════════════════════════════════

class ScreenShake:
    """屏幕震动效果。"""

    def __init__(self):
        self.intensity: float = 0.0
        self.duration: float = 0.0
        self._timer: float = 0.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0

    def trigger(self, intensity: float = 8.0, duration: float = 0.3):
        self.intensity = intensity
        self.duration = duration
        self._timer = duration

    def update(self, dt: float) -> Tuple[float, float]:
        if self._timer > 0:
            self._timer -= dt
            decay = self._timer / self.duration if self.duration > 0 else 0
            amp = self.intensity * decay
            self._offset_x = random.uniform(-amp, amp)
            self._offset_y = random.uniform(-amp, amp)
            return self._offset_x, self._offset_y
        self._offset_x = 0.0
        self._offset_y = 0.0
        return 0.0, 0.0

    @property
    def offset(self) -> Tuple[float, float]:
        return self._offset_x, self._offset_y


# ═══════════════════════════════════════════════
# 星空背景（标题画面用）
# ═══════════════════════════════════════════════

class Starfield:
    """星空背景——带闪烁和缓慢移动。"""

    def __init__(self, count: int = 120, screen_w: int = WIDTH, screen_h: int = HEIGHT):
        self.stars = []
        for _ in range(count):
            self.stars.append({
                "x": random.uniform(0, screen_w),
                "y": random.uniform(0, screen_h),
                "size": random.uniform(0.5, 2.5),
                "speed": random.uniform(0.1, 0.6),
                "twinkle_speed": random.uniform(1.0, 4.0),
                "twinkle_offset": random.uniform(0, math.pi * 2),
                "brightness": random.uniform(0.3, 1.0),
            })

    def update(self, dt: float):
        t = pygame.time.get_ticks() / 1000.0
        for star in self.stars:
            star["y"] += star["speed"] * dt
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.uniform(0, WIDTH)
            star["brightness"] = 0.3 + 0.7 * abs(math.sin(
                t * star["twinkle_speed"] + star["twinkle_offset"]))

    def draw(self, screen: pygame.Surface):
        for star in self.stars:
            b = star["brightness"]
            r = int(COLORS["star"][0] * b)
            g = int(COLORS["star"][1] * b)
            b2 = int(COLORS["star"][2] * b)
            size = star["size"] * (0.8 + 0.2 * star["brightness"])
            if size > 1.5:
                # 亮星加十字光晕
                pygame.draw.circle(screen, (r, g, b2),
                                   (int(star["x"]), int(star["y"])), size)
                # 十字光芒
                glow = min(80, int(star["brightness"] * 60))
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    pygame.draw.line(screen, (r, g, b2, glow),
                                     (star["x"], star["y"]),
                                     (star["x"] + dx * size * 3, star["y"] + dy * size * 3), 1)
            else:
                pygame.draw.circle(screen, (r, g, b2),
                                   (int(star["x"]), int(star["y"])), max(0.5, size))


# ═══════════════════════════════════════════════
# 渐变绘制辅助
# ═══════════════════════════════════════════════

def _draw_gradient_bar(screen, x: int, y: int, w: int, h: int,
                       current: int, maximum: int,
                       color_low: Tuple[int, int, int],
                       color_high: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int] = None,
                       border_color: Tuple[int, int, int] = None,
                       shimmer: bool = False, time_ms: int = 0):
    """绘制带渐变的进度条，可选闪烁动画。"""
    if bg_color is None:
        bg_color = COLORS["panel_light"]
    if border_color is None:
        border_color = COLORS["border"]

    # 背景
    pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=3)

    if maximum > 0:
        ratio = min(1.0, current / maximum)
        fill_w = int(w * ratio)

        if fill_w > 0:
            # 渐变填充
            for px in range(fill_w):
                t = px / w
                r = int(color_low[0] + (color_high[0] - color_low[0]) * t)
                g = int(color_low[1] + (color_high[1] - color_low[1]) * t)
                b = int(color_low[2] + (color_high[2] - color_low[2]) * t)

                # 闪烁高亮
                if shimmer and time_ms > 0:
                    shimmer_t = (time_ms / 800.0 + px / w) % 2.0
                    if shimmer_t < 0.4:
                        boost = int(40 * (1.0 - shimmer_t / 0.4))
                        r = min(255, r + boost)
                        g = min(255, g + boost)
                        b = min(255, b + boost)

                pygame.draw.rect(screen, (r, g, b), (x + px, y + 1, 1, h - 2))

    # 边框
    pygame.draw.rect(screen, border_color, (x, y, w, h), 1, border_radius=3)


def _draw_panel_rounded(screen, x: int, y: int, w: int, h: int,
                        color=None, border_color=None, border_width: int = 2,
                        radius: int = 6):
    """绘制圆角面板。"""
    if color is None:
        color = COLORS["panel"]
    if border_color is None:
        border_color = COLORS["border"]

    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=radius)
    if border_width > 0:
        pygame.draw.rect(screen, border_color, (x, y, w, h), border_width, border_radius=radius)


def _color_lerp(a: Tuple[int, int, int], b: Tuple[int, int, int],
                t: float) -> Tuple[int, int, int]:
    """颜色线性插值。"""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


# ═══════════════════════════════════════════════
# 主UI类
# ═══════════════════════════════════════════════

class GameUI:
    """Pygame文本UI渲染器（增强版）。"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("绝夜之旅 — Journey of the Final Night")
        self.clock = pygame.time.Clock()

        # 字体
        self._init_fonts()

        # 选择相关
        self.selected_index: int = 0
        self.scroll_offset: int = 0
        self.input_text: str = ""
        self.input_active: bool = False

        # ── 特效系统 ──
        self.particles = ParticleSystem()
        self.floating_texts = FloatingTextSystem()
        self.screen_shake = ScreenShake()
        self.starfield = Starfield(150)
        
        # ── 场景渲染器 ──
        from .scene_renderer import SceneRenderer
        self.scene = SceneRenderer(WIDTH, HEIGHT)
        self._current_scene_name = "train"

        # 过渡动画
        self._fade_alpha: float = 1.0
        self._fade_target: float = 1.0
        self._fade_speed: float = 3.0

        # 帧时间
        self._last_time: float = 0.0
        self._delta_time: float = 0.0

        # 屏幕振动偏移缓存
        self._shake_x: float = 0.0
        self._shake_y: float = 0.0

    # ═══════════════════════════════════════════
    # 字体初始化
    # ═══════════════════════════════════════════

    def _init_fonts(self):
        """初始化字体（跨平台中文支持）。"""
        import os

        # 跨平台字体候选列表
        chinese_font_paths = [
            # Windows
            "C:\\Windows\\Fonts\\simhei.ttf",
            "C:\\Windows\\Fonts\\msyh.ttc",
            "C:\\Windows\\Fonts\\msyhbd.ttc",
            "C:\\Windows\\Fonts\\simsun.ttc",
            "C:\\Windows\\Fonts\\simkai.ttf",
            "C:\\Windows\\Fonts\\STKAITI.TTF",
            "C:\\Windows\\Fonts\\Deng.ttf",
            "C:\\Windows\\Fonts\\Dengb.ttf",
            # macOS
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            # Linux
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

        title_font = None
        normal_font = None
        small_font = None

        for path in chinese_font_paths:
            if not os.path.exists(path):
                continue
            try:
                test = pygame.font.Font(path, 24)
                surf = test.render("测试中文", True, (255, 255, 255))
                if surf.get_width() < 10:
                    continue
                title_font = pygame.font.Font(path, 40)
                normal_font = pygame.font.Font(path, 20)
                small_font = pygame.font.Font(path, 16)
                break
            except Exception:
                continue

        if title_font is None:
            # 回退到系统默认字体
            title_font = pygame.font.Font(None, 40)
            normal_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        self.font_title = title_font
        self.font = normal_font
        self.font_small = small_font

        # font_big: 用找到的中文字体创建24号字
        found_paths = [p for p in chinese_font_paths if os.path.exists(p)]
        if found_paths:
            self.font_big = pygame.font.Font(found_paths[0], 24)
        else:
            self.font_big = pygame.font.Font(None, 24)

        self.line_h = self.font.get_linesize() + 2
        self.line_h_small = self.font_small.get_linesize() + 1

    # ═══════════════════════════════════════════
    # 帧管理
    # ═══════════════════════════════════════════

    def _begin_frame(self):
        """每帧开始时调用，计算 delta time。"""
        now = pygame.time.get_ticks() / 1000.0
        if self._last_time == 0:
            self._dt = 0.016  # 默认 60fps
        else:
            self._dt = min(0.1, now - self._last_time)  # 防止大帧差
        self._last_time = now
        self._delta_time = self._dt

        # 更新特效系统
        self.particles.update(self._dt)
        self.floating_texts.update(self._dt)
        self._shake_x, self._shake_y = self.screen_shake.update(self._dt)

        # 更新淡入淡出
        if abs(self._fade_alpha - self._fade_target) > 0.005:
            self._fade_alpha += (self._fade_target - self._fade_alpha) * \
                                min(1.0, self._fade_speed * self._dt)

        # 更新星空
        self.starfield.update(self._dt)

    def _apply_shake(self) -> Tuple[int, int]:
        """应用屏幕震动偏移。"""
        return int(self._shake_x), int(self._shake_y)

    def fade_to(self, alpha: float, speed: float = 3.0):
        """触发淡入淡出。"""
        self._fade_target = alpha
        self._fade_speed = speed

    @property
    def dt(self) -> float:
        return self._delta_time

    @property
    def time_ms(self) -> int:
        return pygame.time.get_ticks()

    # ═══════════════════════════════════════════
    # 基础绘制工具（增强版）
    # ═══════════════════════════════════════════

    def _draw_text(self, text: str, x: int, y: int, color=None, font=None,
                   max_width: int = 0, center: bool = False,
                   shadow: bool = False, glow: bool = False) -> int:
        """绘制文本，支持阴影和发光效果。返回占用的y轴高度。"""
        if color is None:
            color = COLORS["text"]
        if font is None:
            font = self.font

        if max_width > 0:
            lines = self._wrap_text(text, font, max_width)
        else:
            lines = text.split("\n")

        for line in lines:
            if not line:
                y += self.line_h
                continue

            if center:
                x_pos = x + (max_width - font.size(line)[0]) // 2 if max_width \
                    else (WIDTH - font.size(line)[0]) // 2
            else:
                x_pos = x

            # 阴影效果
            if shadow:
                shadow_surf = font.render(line, True, (0, 0, 0))
                shadow_surf.set_alpha(100)
                self.screen.blit(shadow_surf, (x_pos + 2, y + 2))

            # 发光效果
            if glow:
                for offset in [-2, 2]:
                    glow_surf = font.render(line, True, color)
                    glow_surf.set_alpha(60)
                    self.screen.blit(glow_surf, (x_pos + offset, y))
                    self.screen.blit(glow_surf, (x_pos, y + offset))

            surf = font.render(line, True, color)
            self.screen.blit(surf, (x_pos, y))
            y += self.line_h

        return y

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """中文+英文混合自动换行。"""
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph:
                lines.append("")
                continue
            current = ""
            for char in paragraph:
                test = current + char
                w = font.size(test)[0]
                if w > max_width:
                    lines.append(current)
                    current = char
                else:
                    current = test
            if current:
                lines.append(current)
        return lines

    def _draw_panel(self, x: int, y: int, w: int, h: int, color=None, border=True):
        """绘制圆角面板背景。"""
        if color is None:
            color = COLORS["panel"]
        border_c = COLORS["border"] if border is True else border
        bw = 2 if border else 0
        _draw_panel_rounded(self.screen, x, y, w, h, color, border_c, bw)

    def _draw_bar(self, x: int, y: int, w: int, h: int,
                  current: int, maximum: int, color):
        """绘制渐变进度条（带闪烁动画）。"""
        # 根据颜色自动选择渐变对
        if color == COLORS["hp_bar"]:
            low, high = COLORS["hp_bar_dark"], COLORS["hp_bar_bright"]
        elif color == COLORS["mp_bar"]:
            low, high = COLORS["mp_bar_dark"], COLORS["mp_bar_bright"]
        elif color == COLORS["xp_bar"]:
            low, high = COLORS["xp_bar_dark"], COLORS["xp_bar_bright"]
        else:
            low, high = color, color

        _draw_gradient_bar(self.screen, x, y, w, h, current, maximum,
                           low, high, shimmer=True, time_ms=self.time_ms)

    def _draw_icon_button(self, x: int, y: int, w: int, h: int,
                          text: str, selected: bool = False,
                          icon: str = "", desc: str = ""):
        """绘制图标按钮（含悬浮高亮效果）。"""
        bg = COLORS["highlight"] if selected else COLORS["panel_light"]
        border_c = COLORS["gold"] if selected else COLORS["border"]

        _draw_panel_rounded(self.screen, x, y, w, h, bg, border_c, 2 if selected else 1, 4)

        # 选择指示
        if selected:
            # 左侧发光边
            glow_rect = pygame.Surface((4, h - 4), pygame.SRCALPHA)
            for i in range(4):
                alpha = 80 - i * 20
                pygame.draw.rect(glow_rect, (*COLORS["gold"], alpha), (i, 0, 1, h - 4))
            self.screen.blit(glow_rect, (x + 2, y + 2))

        # 图标 + 文字
        display = f"{icon} {text}" if icon else text
        self._draw_text(display, x + 12, y + 6,
                       COLORS["gold"] if selected else COLORS["text"], self.font)

        if desc:
            self._draw_text(desc, x + 12, y + 28,
                           COLORS["text"] if selected else COLORS["text_dim"], self.font_small)

    def _draw_glow_border(self, x: int, y: int, w: int, h: int,
                          color: Tuple[int, int, int], pulses: bool = False):
        """绘制发光边框。"""
        alpha_base = int(80 + 40 * math.sin(self.time_ms / 500.0)) if pulses else 100
        alpha_base = max(30, min(130, alpha_base))

        for offset in range(3):
            alpha = alpha_base - offset * 25
            if alpha <= 0:
                break
            glow_surf = pygame.Surface((w + offset * 2, h + offset * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color, alpha),
                             (0, 0, w + offset * 2, h + offset * 2), 2, border_radius=8)
            self.screen.blit(glow_surf, (x - offset, y - offset))

    # ═══════════════════════════════════════════
    # 标题画面（重制：星空背景 + 动态装饰）
    # ═══════════════════════════════════════════

    def draw_title_screen(self, menu_options: List[str], selected: int,
                          has_saves: bool = False):
        """绘制标题画面（星空背景增强版）。"""
        self._begin_frame()

        # 场景背景
        self.scene.set_scene("train")
        self.scene.render(self.screen, 0, 0, WIDTH, HEIGHT)
        
        # 暗色叠加
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 2, 8, 180))
        self.screen.blit(overlay, (0, 0))

        # 星空
        self.starfield.draw(self.screen)

        # 大型装饰月环
        center_x, center_y = WIDTH // 2, 200
        t = self.time_ms / 3000.0
        for i in range(3):
            radius = 120 + i * 30
            alpha = int(15 - i * 4)
            if alpha > 0:
                arc_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                # 不完整的圆弧
                start_angle = t + i * 0.8
                for angle in range(0, 360, 5):
                    a = math.radians(angle + start_angle * 30)
                    px = radius + math.cos(a) * radius * (0.6 + 0.4 * abs(math.sin(a * 2)))
                    py = radius + math.sin(a) * radius * 0.7
                    pygame.draw.circle(arc_surf, (*COLORS["gold_dark"], alpha),
                                      (int(px), int(py)), 1)
                self.screen.blit(arc_surf, (center_x - radius, center_y - radius))

        # 标题（带阴影和发光）
        title_y = 150
        self._draw_text("⚔️  绝 夜 之 旅  ⚔️", 0, title_y,
                        COLORS["gold_bright"], self.font_title,
                        max_width=WIDTH, center=True, shadow=True, glow=True)
        self._draw_text("Journey of the Final Night", 0, title_y + 55,
                        COLORS["text_dim"], self.font_small,
                        max_width=WIDTH, center=True)

        # 副标题
        self._draw_text("— 暗黑TRPG · 骰子判定 · 四大章节 —", 0, title_y + 90,
                        COLORS["purple"], self.font_small,
                        max_width=WIDTH, center=True)

        # 菜单选项
        menu_y = 370
        for i, option in enumerate(menu_options):
            # 跳过没有存档时的"继续游戏"
            if option == "继续游戏" and not has_saves:
                color = COLORS["text_dim"]
                prefix = "   "
                label = f"{option}  (无存档)"
            else:
                color = COLORS["gold"] if i == selected else COLORS["text"]
                prefix = "▶ " if i == selected else "   "
                label = option

            # 选中项左右装饰
            if i == selected:
                sel_y = menu_y + i * 45
                # 左侧菱形
                self._draw_text("◆", 200, sel_y, COLORS["gold"], self.font_small)
                self._draw_text("◆", WIDTH - 220, sel_y, COLORS["gold"], self.font_small)

            self._draw_text(f"{prefix}{label}", 0, menu_y + i * 45,
                            color, self.font_big, max_width=WIDTH, center=True)

        # 底部说明（分行排列）
        self._draw_text("↑↓ 选择  |  Enter 确认  |  Esc 退出",
                        0, HEIGHT - 50, COLORS["text_dim"], self.font_small,
                        max_width=WIDTH, center=True)

        # 底部版本信息
        self._draw_text("v1.0  —  Made with Pygame",
                        0, HEIGHT - 25, COLORS["text_dim"], self.font_small,
                        max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 角色创建画面（增强视觉反馈）
    # ═══════════════════════════════════════════

    def draw_create_screen(self, step: str, char_classes: List[CharClass],
                           selected: int, input_name: str = "",
                           has_error: str = "", player_label: int = 1):
        """绘制角色创建画面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        if step == "class":
            self._draw_create_class(char_classes, selected, player_label)
        elif step == "name":
            self._draw_create_name(input_name, selected, char_classes,
                                   has_error, player_label)
        elif step == "confirm":
            self._draw_create_confirm(char_classes, selected, input_name, player_label)

    def _draw_create_class(self, char_classes: List[CharClass], selected: int,
                           player_label: int = 1):
        p_label = f"玩家{player_label} " if player_label > 1 else ""
        self._draw_text(f"{p_label}选择你的职业", 0, 35,
                        COLORS["gold_bright"], self.font_title,
                        max_width=WIDTH, center=True, shadow=True)
        self._draw_text("每个职业有独特的属性和技能 — 慎重选择，这将决定你的旅途",
                        0, 78, COLORS["text_dim"], self.font_small,
                        max_width=WIDTH, center=True)

        # 分割线
        pygame.draw.line(self.screen, COLORS["border"], (120, 100),
                        (WIDTH - 120, 100), 1)

        start_y = 120
        card_w = WIDTH - 160
        for i, cc in enumerate(char_classes):
            y = start_y + i * 90
            is_sel = i == selected

            # 卡片背景
            bg_color = COLORS["panel_highlight"] if is_sel else COLORS["panel"]
            _draw_panel_rounded(self.screen, 80, y, card_w, 82, bg_color,
                               COLORS["gold"] if is_sel else COLORS["border"],
                               3 if is_sel else 1, 5)

            # 选中发光边框
            if is_sel:
                self._draw_glow_border(80, y, card_w, 82, COLORS["gold"], pulses=True)

            # 职业图标和名称
            icon_x = 105
            self._draw_text(cc.icon, icon_x, y + 8, COLORS["white"], self.font_title)
            self._draw_text(cc.display_name, icon_x + 55, y + 10,
                           COLORS["gold_bright"], self.font_big)
            self._draw_text(cc.description, icon_x + 55, y + 38,
                           COLORS["text_dim"], self.font_small)

            # 属性
            stats = CLASS_STATS[cc]
            stats_text = f"❤{stats['max_hp']}  💙{stats['max_mp']}   💪{stats['str']}   🏃{stats['dex']}   🧠{stats['int']}   🔮{stats['wis']}   💬{stats['cha']}   🍀{stats['luk']}"
            self._draw_text(stats_text, icon_x + 55, y + 58,
                           COLORS["text"], self.font_small)

        self._draw_text("← → 选择职业  |  Enter 确认", 0, HEIGHT - 50,
                        COLORS["text_dim"], self.font_small,
                        max_width=WIDTH, center=True)

    def _draw_create_name(self, input_name: str, selected_class_idx: int,
                          classes: List[CharClass], has_error: str,
                          player_label: int = 1):
        cc = classes[selected_class_idx]
        p_label = f"玩家{player_label} " if player_label > 1 else ""

        # 标题
        self._draw_text(f"{p_label}为你的角色命名", 0, 60,
                        COLORS["gold_bright"], self.font_title,
                        max_width=WIDTH, center=True, shadow=True)

        # 已选职业卡片
        card_w = 500
        card_x = (WIDTH - card_w) // 2
        card_y = 135
        _draw_panel_rounded(self.screen, card_x, card_y, card_w, 72,
                           COLORS["panel_highlight"], COLORS["gold"], 2, 5)
        self._draw_text(f"{cc.icon}  {cc.display_name}", 0, card_y + 12,
                       COLORS["gold_bright"], self.font_big,
                       max_width=WIDTH, center=True)

        stats = CLASS_STATS[cc]
        stats_str = f"❤{stats['max_hp']} | 💙{stats['max_mp']} | 💪{stats['str']} | 🏃{stats['dex']} | 🧠{stats['int']} | 🔮{stats['wis']} | 💬{stats['cha']} | 🍀{stats['luk']}"
        self._draw_text(stats_str, 0, card_y + 45,
                       COLORS["text"], self.font_small,
                       max_width=WIDTH, center=True)

        # 输入框区域
        input_y = 260
        self._draw_text("请输入角色名称:", 0, input_y,
                       COLORS["text"], self.font_big,
                       max_width=WIDTH, center=True)

        # 输入框 - 带发光效果
        box_w, box_h = 440, 50
        box_x = (WIDTH - box_w) // 2
        box_y = input_y + 48

        # 外发光
        if self.input_active:
            glow = int(20 + 15 * math.sin(self.time_ms / 300.0))
            glow_surf = pygame.Surface((box_w + 8, box_h + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*COLORS["gold"], glow),
                            (0, 0, box_w + 8, box_h + 8), border_radius=6)
            self.screen.blit(glow_surf, (box_x - 4, box_y - 4))

        # 输入框本体
        _draw_panel_rounded(self.screen, box_x, box_y, box_w, box_h,
                           COLORS["panel_light"],
                           COLORS["gold"] if self.input_active else COLORS["border"],
                           2, 4)

        # 文本内容 + 光标
        display_text = input_name
        if self.input_active and (self.time_ms // 500) % 2 == 0:
            display_text += "▌"
        elif not input_name and not self.input_active:
            display_text = "（点击此处输入名称后按Enter确认）"

        self._draw_text(display_text, box_x + 15, box_y + 10,
                       COLORS["text"] if input_name else COLORS["text_dim"],
                       self.font)

        # 错误提示
        if has_error:
            self._draw_text(f"⚠ {has_error}", 0, box_y + 65,
                           COLORS["red"], self.font_small,
                           max_width=WIDTH, center=True)

        # 底部提示
        self._draw_text("输入名称后按 Enter 确认  |  Backspace 删除  |  Esc 返回",
                       0, HEIGHT - 50, COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    def _draw_create_confirm(self, classes: List[CharClass],
                             selected_class_idx: int, name: str,
                             player_label: int = 1):
        cc = classes[selected_class_idx]
        p_label = f"玩家{player_label} " if player_label > 1 else ""

        self._draw_text(f"{p_label}确认角色信息", 0, 60,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True)

        # 角色卡片
        card_w = 520
        card_x = (WIDTH - card_w) // 2
        card_y = 140
        _draw_panel_rounded(self.screen, card_x, card_y, card_w, 340,
                           COLORS["panel"], COLORS["gold"], 2, 8)

        # 名称
        self._draw_text(f"✦  {name}  ✦", 0, card_y + 20,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True)

        # 职业
        self._draw_text(f"{cc.icon}  {cc.display_name}", 0, card_y + 70,
                       COLORS["gold"], self.font_big,
                       max_width=WIDTH, center=True)

        # 属性表（双列）
        stats = CLASS_STATS[cc]
        y = card_y + 115
        col1_x = card_x + 50
        col2_x = card_x + 280

        left_attrs = [
            ("❤ HP", stats['max_hp']), ("💙 MP", stats['max_mp']),
            ("💪 力量 STR", stats['str']), ("🏃 敏捷 DEX", stats['dex']),
        ]
        right_attrs = [
            ("🧠 智力 INT", stats['int']), ("🔮 感知 WIS", stats['wis']),
            ("💬 魅力 CHA", stats['cha']), ("🍀 幸运 LUK", stats['luk']),
        ]

        for (label, val) in left_attrs:
            self._draw_text(f"{label}: {val}", col1_x, y,
                           COLORS["text"], self.font)
            y += 35

        y = card_y + 115
        for (label, val) in right_attrs:
            self._draw_text(f"{label}: {val}", col2_x, y,
                           COLORS["text"], self.font)
            y += 35

        # 底部操作提示
        self._draw_text("Enter 踏上旅程  |  Esc 返回修改", 0, card_y + 360,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 游戏主界面（优化排版 + 视觉层次）
    # ═══════════════════════════════════════════

    def draw_game_screen(self, event: Event, player: Character,
                         event_log: List[str], selected_choice: int,
                         chapter_title: str, event_index: int,
                         total_events: int, player2: Character = None):
        """绘制游戏主界面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        # ── 左侧：场景背景 + 故事区域 ──
        # 先绘制场景作为背景
        if self._current_scene_name:
            self.scene.set_scene(self._current_scene_name)
        self.scene.render(self.screen, 0, 0, TEXT_AREA_WIDTH + 30, HEIGHT)

        # 半透明面板覆盖在场景上
        panel_surf = pygame.Surface((TEXT_AREA_WIDTH, HEIGHT - 20), pygame.SRCALPHA)
        panel_surf.fill((*COLORS["panel"], 210))
        self.screen.blit(panel_surf, (10, 10))


        # 章节和进度条
        self._draw_text(f"{chapter_title}  |  事件 {event_index + 1}/{total_events}",
                       25, 18, COLORS["text_dim"], self.font_small)

        # 微型进度条
        progress_w = TEXT_AREA_WIDTH - 50
        bar_x, bar_y = 25, 34
        pygame.draw.rect(self.screen, COLORS["panel_light"],
                        (bar_x, bar_y, progress_w, 3), border_radius=2)
        if total_events > 0:
            fill_w = int(progress_w * (event_index + 1) / total_events)
            _draw_gradient_bar(self.screen, bar_x, bar_y, fill_w, 3,
                             1, 1, COLORS["gold_dark"], COLORS["gold_bright"])

        # 事件标题 — Boss战特殊处理
        if event.event_type == EventType.BOSS:
            # Boss战标题带脉冲发光
            pulse = int(20 + 15 * math.sin(self.time_ms / 400.0))
            self._draw_glow_border(20, 38, TEXT_AREA_WIDTH - 30, 30,
                                  COLORS["boss_red"], pulses=True)
            title_color = COLORS["red_bright"]
        else:
            title_color = COLORS["gold_bright"]

        self._draw_text(event.title, 25, 42, title_color, self.font_big,
                       shadow=(event.event_type == EventType.BOSS))

        # 描述（增加行间距）
        desc_y = self._draw_text(event.description, 25, 78,
                                COLORS["text"], self.font,
                                max_width=TEXT_AREA_WIDTH - 50)

        # 事件日志
        if event_log:
            log_y = desc_y + 12
            # 日志背景条
            pygame.draw.rect(self.screen, COLORS["panel_light"],
                           (25, log_y, TEXT_AREA_WIDTH - 50,
                            min(len(event_log) * 20, 160)), border_radius=3)

            for log_line in event_log[-8:]:
                color = COLORS["text"]
                if "大成功" in log_line:
                    color = COLORS["gold_bright"]
                elif "大失败" in log_line:
                    color = COLORS["red_bright"]
                elif "成功" in log_line:
                    color = COLORS["green"]
                elif "失败" in log_line:
                    color = COLORS["red_dark"]
                log_y = self._draw_text(log_line, 32, log_y + 3,
                                       color, self.font_small,
                                       max_width=TEXT_AREA_WIDTH - 65)
                log_y += 1

        # 选项区域
        choice_start_y = max(HEIGHT - 200, desc_y + 130)
        if event.choices:
            # 选项分隔线
            sep_y = choice_start_y - 15
            pygame.draw.line(self.screen, COLORS["border"],
                           (30, sep_y), (TEXT_AREA_WIDTH - 30, sep_y), 1)

            self._draw_text("— 选择你的行动 —", 25, choice_start_y,
                           COLORS["gold"], self.font_big)

            for i, choice in enumerate(event.choices):
                cy = choice_start_y + 32 + i * 28
                is_sel = i == selected_choice
                prefix = "▸ " if is_sel else "  "
                color = COLORS["gold"] if is_sel else COLORS["text"]

                check_info = ""
                if choice.check_type:
                    check_info = f"  [{choice.check_type.upper()} DC={choice.dc}]"
                if choice.trigger_combat:
                    enemy = choice.combat_enemy or "???"
                    check_info = f"  [⚔ 战斗: {enemy}]"

                self._draw_text(f"{prefix}{i+1}. {choice.text}{check_info}",
                               35, cy, color, self.font_small,
                               max_width=TEXT_AREA_WIDTH - 70)

        # ── 右侧状态栏 ──
        if player2:
            self._draw_sidebar_dual(player, player2)
        else:
            self._draw_sidebar(player, chapter_title)

        # 底部操作键
        self._draw_text("↑↓ 选择  Enter 确认  S 存档  C 角色  Esc 菜单",
                       0, HEIGHT - 25, COLORS["text_dim"], self.font_small,
                       max_width=TEXT_AREA_WIDTH, center=True)

    def _draw_sidebar(self, player: Character, chapter_title: str):
        """绘制右侧角色状态栏（单玩家）。"""
        sx, sy = SIDEBAR_X + 12, 15
        sw = PANEL_WIDTH - 20
        self._draw_panel(SIDEBAR_X, 0, PANEL_WIDTH, HEIGHT)

        # 角色头像区域
        avatar_y = sy
        self._draw_text(f"🎭 {player.name}", sx - 7, avatar_y,
                       COLORS["gold_bright"], self.font,
                       max_width=sw + 5, center=True)
        self._draw_text(f"{player.char_class.icon} {player.char_class.display_name}  Lv.{player.level}",
                       sx - 7, avatar_y + 27, COLORS["text"], self.font_small,
                       max_width=sw + 5, center=True)

        # 分隔线
        sep1_y = avatar_y + 52
        pygame.draw.line(self.screen, COLORS["border"],
                        (sx - 7, sep1_y), (sx + sw - 10, sep1_y), 1)

        # HP条
        hp_y = sep1_y + 12
        self._draw_text("❤ HP", sx - 7, hp_y, COLORS["red"], self.font_small)
        self._draw_bar(sx + 40, hp_y + 2, sw - 50, 15,
                      player.stats.hp, player.stats.max_hp, COLORS["hp_bar"])
        self._draw_text(f"{player.stats.hp}/{player.stats.max_hp}",
                       sx + 42, hp_y + 18, COLORS["text"], self.font_small)

        # MP条
        mp_y = hp_y + 40
        self._draw_text("💙 MP", sx - 7, mp_y, COLORS["blue"], self.font_small)
        self._draw_bar(sx + 40, mp_y + 2, sw - 50, 15,
                      player.stats.mp, player.stats.max_mp, COLORS["mp_bar"])
        self._draw_text(f"{player.stats.mp}/{player.stats.max_mp}",
                       sx + 42, mp_y + 18, COLORS["text"], self.font_small)

        # XP条
        xp_y = mp_y + 40
        self._draw_text("⭐ EXP", sx - 7, xp_y, COLORS["green"], self.font_small)
        self._draw_bar(sx + 40, xp_y + 2, sw - 50, 15,
                      player.xp, player.xp_to_next, COLORS["xp_bar"])
        self._draw_text(f"{player.xp}/{player.xp_to_next}",
                       sx + 42, xp_y + 18, COLORS["text"], self.font_small)

        # 金币和暗影精华
        econ_y = xp_y + 38
        self._draw_text(f"💰 {player.gold} GP", sx - 7, econ_y, COLORS["gold"], self.font_small)
        if player.shadow_essence > 0:
            self._draw_text(f"💎 {player.shadow_essence} 精华", sx + 70, econ_y, COLORS["purple"], self.font_small)

        # 技能点和属性点提示
        if player.skill_points > 0 or player.pending_attr_points > 0:
            pts_line = ""
            if player.skill_points > 0:
                pts_line += f"📜 {player.skill_points}技能点 "
            if player.pending_attr_points > 0:
                pts_line += f"⬆ {player.pending_attr_points}属性点"
            self._draw_text(pts_line, sx - 7, econ_y + 18, COLORS["gold_bright"], self.font_small)

        # 分隔线
        sep2_y = econ_y + 40
        pygame.draw.line(self.screen, COLORS["border"],
                        (sx - 7, sep2_y), (sx + sw - 10, sep2_y), 1)

        # 属性表（紧凑两列）
        attr_y = sep2_y + 12
        attrs = [
            ("💪", player.stats.strength, player.str_mod),
            ("🏃", player.stats.dexterity, player.dex_mod),
            ("🧠", player.stats.intelligence, player.int_mod),
            ("🔮", player.stats.wisdom, player.wis_mod),
            ("💬", player.stats.charisma, player.cha_mod),
            ("🍀", player.stats.luck, 0),
        ]
        for idx, (icon, val, mod_val) in enumerate(attrs):
            col = idx % 2
            row = idx // 2
            ax = sx - 7 + col * (sw // 2)
            ay = attr_y + row * 22
            mod_str = f"+{mod_val}" if mod_val >= 0 else str(mod_val)
            self._draw_text(f"{icon} {val} ({mod_str})", ax, ay,
                           COLORS["text"], self.font_small)

        # 技能（仅显示已解锁的）
        skill_y = attr_y + 3 * 22 + 10
        pygame.draw.line(self.screen, COLORS["border"],
                        (sx - 7, skill_y), (sx + sw - 10, skill_y), 1)
        skill_y += 8
        unlocked_count = len([s for s in player.skills if not s.is_locked])
        self._draw_text(f"📜 技能 ({unlocked_count})", sx - 7, skill_y, COLORS["gold"], self.font_small)
        skill_y += 20

        for s in player.skills:
            if s.is_locked:
                continue
            cd_color = COLORS["red"] if s.current_cooldown > 0 else COLORS["green"]
            cd_text = f"CD:{s.current_cooldown}" if s.current_cooldown > 0 else "就绪"
            self._draw_text(f"• {s.name} MP:{s.mp_cost} {cd_text}",
                           sx - 4, skill_y, COLORS["text"], self.font_small, max_width=sw - 20)
            skill_y += 22

        # 阵营声望（仅显示 > 0 的阵营）
        from .faction import Faction, get_faction_tier, FACTION_TIERS
        if hasattr(player, 'faction_reputation') and player.faction_reputation:
            factions_with_rep = {k: v for k, v in player.faction_reputation.items() if v > 0}
            if factions_with_rep:
                fac_y = skill_y + 5
                pygame.draw.line(self.screen, COLORS["border"],
                               (sx - 7, fac_y), (sx + sw - 10, fac_y), 1)
                fac_y += 10
                self._draw_text("🏛 阵营", sx - 7, fac_y, COLORS["gold"], self.font_small)
                fac_y += 18
                for fac_name, rep in sorted(factions_with_rep.items(), key=lambda x: -x[1]):
                    try:
                        fac = Faction[fac_name]
                        tier = get_faction_tier(rep)
                        tier_name = FACTION_TIERS[tier]
                        self._draw_text(f"{fac.icon} {fac.display_name}: {tier_name}",
                                       sx - 4, fac_y, COLORS["text"], self.font_small)
                        fac_y += 15
                    except KeyError:
                        pass
                skill_y = fac_y

        # 道具
        if player.items:
            item_y = skill_y + 5
            pygame.draw.line(self.screen, COLORS["border"],
                           (sx - 7, item_y), (sx + sw - 10, item_y), 1)
            item_y += 10
            self._draw_text(f"🎒 道具 ({len(player.items)}/10)", sx - 7, item_y,
                           COLORS["gold"], self.font_small)
            item_y += 20
            for item in player.items[-5:]:
                name = item["name"] if isinstance(item, dict) else item
                self._draw_text(f"• {name}", sx - 4, item_y,
                               COLORS["text"], self.font_small)
                item_y += 18

    def _draw_sidebar_dual(self, p1: Character, p2: Character):
        """绘制右侧双人状态栏（紧凑版，优化排版）。"""
        sx, sy = SIDEBAR_X + 12, 10
        sw = PANEL_WIDTH - 20
        self._draw_panel(SIDEBAR_X, 0, PANEL_WIDTH, HEIGHT)

        half_h = HEIGHT // 2 - 10

        # ── 玩家1 区域 ──
        p1_bg = COLORS["panel_light"]
        _draw_panel_rounded(self.screen, sx - 7, sy, sw + 15, half_h, p1_bg,
                           COLORS["blue"], 2, 5)
        p1_label_y = sy + 5
        self._draw_text(f"[P1] {p1.name}  {p1.char_class.icon} Lv.{p1.level}",
                       sx - 4, p1_label_y, COLORS["gold_bright"],
                       self.font_small, max_width=sw + 8)

        # HP / MP 紧凑行
        row1_y = p1_label_y + 22
        self._draw_text("❤", sx - 4, row1_y, COLORS["red"], self.font_small)
        self._draw_bar(sx + 16, row1_y + 2, sw - 90, 10,
                      p1.stats.hp, p1.stats.max_hp, COLORS["hp_bar"])
        hp_text = f"{p1.stats.hp}/{p1.stats.max_hp}"
        self._draw_text(hp_text, sx + sw - 72, row1_y,
                       COLORS["text"], self.font_small)

        row2_y = row1_y + 15
        self._draw_text("💙", sx - 4, row2_y, COLORS["blue"], self.font_small)
        self._draw_bar(sx + 16, row2_y + 2, sw - 90, 10,
                      p1.stats.mp, p1.stats.max_mp, COLORS["mp_bar"])
        mp_text = f"{p1.stats.mp}/{p1.stats.max_mp}"
        self._draw_text(mp_text, sx + sw - 72, row2_y,
                       COLORS["text"], self.font_small)

        # 属性一行显示
        attr_y = row2_y + 16
        attrs_p1 = (f"💪{p1.stats.strength} 🏃{p1.stats.dexterity} "
                    f"🧠{p1.stats.intelligence} 🔮{p1.stats.wisdom} "
                    f"💬{p1.stats.charisma} 🍀{p1.stats.luck}")
        self._draw_text(attrs_p1, sx - 4, attr_y,
                       COLORS["text"], self.font_small, max_width=sw + 8)

        # ── 分隔 ──
        mid_y = half_h + 14
        pygame.draw.line(self.screen, COLORS["gold"],
                        (sx - 5, mid_y), (sx + sw + 5, mid_y), 2)

        # ── 玩家2 区域 ──
        p2_y = mid_y + 8
        p2_bg_h = HEIGHT - p2_y - 10
        _draw_panel_rounded(self.screen, sx - 7, p2_y, sw + 15, p2_bg_h,
                           COLORS["panel_light"], COLORS["green"], 2, 5)

        p2_label_y = p2_y + 5
        self._draw_text(f"[P2] {p2.name}  {p2.char_class.icon} Lv.{p2.level}",
                       sx - 4, p2_label_y, COLORS["gold_bright"],
                       self.font_small, max_width=sw + 8)

        p2_row1 = p2_label_y + 22
        self._draw_text("❤", sx - 4, p2_row1, COLORS["red"], self.font_small)
        self._draw_bar(sx + 16, p2_row1 + 2, sw - 90, 10,
                      p2.stats.hp, p2.stats.max_hp, COLORS["hp_bar"])
        self._draw_text(f"{p2.stats.hp}/{p2.stats.max_hp}",
                       sx + sw - 72, p2_row1, COLORS["text"], self.font_small)

        p2_row2 = p2_row1 + 15
        self._draw_text("💙", sx - 4, p2_row2, COLORS["blue"], self.font_small)
        self._draw_bar(sx + 16, p2_row2 + 2, sw - 90, 10,
                      p2.stats.mp, p2.stats.max_mp, COLORS["mp_bar"])
        self._draw_text(f"{p2.stats.mp}/{p2.stats.max_mp}",
                       sx + sw - 72, p2_row2, COLORS["text"], self.font_small)

        attr2_y = p2_row2 + 16
        attrs_p2 = (f"💪{p2.stats.strength} 🏃{p2.stats.dexterity} "
                    f"🧠{p2.stats.intelligence} 🔮{p2.stats.wisdom} "
                    f"💬{p2.stats.charisma} 🍀{p2.stats.luck}")
        self._draw_text(attrs_p2, sx - 4, attr2_y,
                       COLORS["text"], self.font_small, max_width=sw + 8)

    def _draw_compact_player(self, player: Character, x: int, y: int,
                             max_w: int, label: str):
        self._draw_text(f"[{label}] {player.name}  {player.char_class.icon} Lv.{player.level}",
                       x + 5, y, COLORS["gold_bright"], self.font_small,
                       max_width=max_w - 10)

    # ═══════════════════════════════════════════
    # 战斗界面（大幅增强）
    # ═══════════════════════════════════════════

    def draw_combat_screen(self, combat: CombatEngine, selected_action: int,
                           selected_skill: int, action_phase: str = "action"):
        """绘制战斗界面（增强版：粒子特效、浮动伤害、Boss视觉效果）。"""
        self._begin_frame()

        # 应用屏幕震动偏移
        shake_x, shake_y = self._apply_shake()

        self.screen.fill(COLORS["bg"])

        enemy = combat.enemy
        
        # ── 战斗场景背景 ──
        self.scene.render_combat_background(
            self.screen, 0, 0, TEXT_AREA_WIDTH + 30, HEIGHT,
            is_boss=enemy.is_boss, enemy_name=enemy.name
        )
        
        # ── 左侧：半透明战斗信息面板 ──
        left_w = TEXT_AREA_WIDTH
        panel_surf = pygame.Surface((left_w, HEIGHT - 20), pygame.SRCALPHA)
        panel_surf.fill((*COLORS["panel"], 220))
        self.screen.blit(panel_surf, (10, 10))

        # Boss特殊处理
        if enemy.is_boss:
            # Boss标题区域：暗红背景 + 脉冲发光
            boss_bg_y = 15
            boss_bg_h = 55
            pygame.draw.rect(self.screen, (30, 5, 5),
                           (20, boss_bg_y, left_w - 40, boss_bg_h), border_radius=6)
            self._draw_glow_border(20, boss_bg_y, left_w - 40, boss_bg_h,
                                  COLORS["boss_red"], pulses=True)
            self._draw_text(f"💀 {enemy.name}  Lv.{enemy.level} 【BOSS】",
                           30, boss_bg_y + 8, COLORS["boss_red"], self.font_big)

            # Boss HP条（加厚 + 脉冲）
            boss_bar_y = boss_bg_y + 35
            _draw_gradient_bar(self.screen, 30, boss_bar_y, left_w - 90, 20,
                              enemy.hp, enemy.max_hp,
                              (80, 5, 5), (220, 20, 20),
                              shimmer=True, time_ms=self.time_ms)
            self._draw_text(f"HP: {enemy.hp}/{enemy.max_hp}",
                          30, boss_bar_y + 22, COLORS["red_bright"],
                          self.font_small)

            # Boss粒子：周围定期发射暗红色粒子
            if self.time_ms % 200 < 50:
                self.particles.emit(
                    random.uniform(30, left_w - 30), boss_bg_y + boss_bg_h + 5,
                    count=3, speed=30, spread=180,
                    color=(200, 30, 30), size=1.5, life=0.8, decay="spark"
                )
        else:
            self._draw_text(f"👾 {enemy.name}  Lv.{enemy.level}",
                           25, 18, COLORS["red"], self.font_big)

            # 普通敌人HP条
            bar_w = left_w - 80
            self._draw_bar(25, 48, bar_w, 16,
                          enemy.hp, enemy.max_hp, COLORS["hp_bar"])
            self._draw_text(f"HP: {enemy.hp}/{enemy.max_hp}",
                           25 + bar_w + 10, 48, COLORS["text"], self.font_small)

        # 敌人描述
        desc_y = 80 if not enemy.is_boss else 102
        self._draw_text(enemy.description, 25, desc_y,
                       COLORS["text_dim"], self.font_small,
                       max_width=left_w - 50)

        # 浮动伤害数字
        self.floating_texts.draw(self.screen, self.font_big)

        # 战斗日志
        log_y = desc_y + 28
        pygame.draw.line(self.screen, COLORS["border"],
                        (25, log_y - 5), (left_w - 25, log_y - 5), 1)
        self._draw_text("─ 战斗记录 ─", 25, log_y,
                       COLORS["border"], self.font_small)
        log_y += 24

        for line in combat.log[-12:]:
            color = COLORS["text"]
            if "暴击" in line or "CRITICAL" in line:
                color = COLORS["gold_bright"]
            elif "击败" in line or "胜利" in line:
                color = COLORS["green"]
            elif "受到" in line:
                color = COLORS["red"]
            elif "回复" in line or "治疗" in line:
                color = COLORS["green"]
            elif "闪避" in line or "未命中" in line:
                color = COLORS["text_dim"]
            elif "技能" in line:
                color = COLORS["purple"]
            log_y = self._draw_text(line, 30, log_y, color, self.font_small,
                                    max_width=left_w - 60)

        # ── 右侧：行动菜单 ──
        sx = SIDEBAR_X + 12
        self._draw_panel(SIDEBAR_X, 0, PANEL_WIDTH, HEIGHT)

        # 当前玩家状态头部
        current_p = combat.current_player
        turn_info = f"[P{combat.current_player_index + 1}] " if combat.is_multiplayer else ""

        # 头像区域背景
        _draw_panel_rounded(self.screen, sx - 5, 12, PANEL_WIDTH - 10, 55,
                           COLORS["panel_highlight"], COLORS["border"], 1, 4)

        self._draw_text(f"🎯 {turn_info}{current_p.name}",
                       sx - 5, 18, COLORS["gold_bright"], self.font,
                       max_width=PANEL_WIDTH - 15, center=True)
        self._draw_text(f"❤ {current_p.hp}/{current_p.stats.max_hp}  "
                       f"💙 {current_p.mp}/{current_p.stats.max_mp}",
                       sx - 5, 42, COLORS["text"], self.font_small,
                       max_width=PANEL_WIDTH - 15, center=True)

        # 多人模式：另一个玩家状态条
        if combat.is_multiplayer:
            other_idx = 1 - combat.current_player_index
            other_p = combat.players[other_idx]
            other_text = (f"待机: [P{other_idx+1}] {other_p.name}  "
                         f"❤{other_p.hp}/{other_p.stats.max_hp}  "
                         f"💙{other_p.mp}/{other_p.stats.max_mp}")
            self._draw_text(other_text, sx - 2, 70,
                           COLORS["text_dim"], self.font_small)

        # 分隔
        menu_start_y = 82 if combat.is_multiplayer else 72
        pygame.draw.line(self.screen, COLORS["border"],
                        (sx - 5, menu_start_y),
                        (sx + PANEL_WIDTH - 15, menu_start_y), 1)

        # ── 行动指令菜单 ──
        if action_phase == "action":
            self._draw_text(f"⚔ {turn_info}选择行动:", sx - 2,
                           menu_start_y + 8, COLORS["gold"], self.font_big)

            actions = [
                ("⚔ 攻击", "普通物理攻击"),
                ("✨ 技能", "使用职业技能"),
                ("🛡 防御", "提升防御一回合"),
                ("🎒 道具", "使用背包道具"),
                ("🏃 逃跑", "尝试逃离战斗"),
            ]
            for i, (name, desc) in enumerate(actions):
                ay = menu_start_y + 38 + i * 52
                self._draw_icon_button(sx - 2, ay, PANEL_WIDTH - 20, 46,
                                      name, i == selected_action, desc=desc)

        elif action_phase == "skill":
            self._draw_text(f"📜 {turn_info}选择技能:", sx - 2,
                           menu_start_y + 8, COLORS["gold"], self.font_big)
            self._draw_text("Esc 返回", sx + 160, menu_start_y + 8,
                           COLORS["text_dim"], self.font_small)

            # 只显示已解锁的技能
            unlocked_skills = [s for s in current_p.skills if not s.is_locked]
            for i, skill in enumerate(unlocked_skills):
                sy2 = menu_start_y + 38 + i * 42
                can_use = skill.can_use(current_p.mp)
                is_sel = i == selected_skill

                color = (COLORS["gold"] if is_sel else
                        (COLORS["text"] if can_use else COLORS["text_dim"]))
                status = "[就绪]" if can_use else f"[CD:{skill.current_cooldown}]"
                status_color = COLORS["green"] if can_use else COLORS["red"]

                self._draw_icon_button(
                    sx - 2, sy2, PANEL_WIDTH - 20, 38,
                    f"{skill.name} MP:{skill.mp_cost} {status}",
                    is_sel, desc=skill.description
                )

        elif action_phase == "item":
            self._draw_text(f"🎒 {turn_info}选择道具:", sx - 2,
                           menu_start_y + 8, COLORS["gold"], self.font_big)
            self._draw_text("Esc 返回", sx + 160, menu_start_y + 8,
                           COLORS["text_dim"], self.font_small)

            items = current_p.items
            if items:
                for i, item_data in enumerate(items):
                    sy2 = menu_start_y + 38 + i * 52
                    is_sel = i == selected_skill
                    name = item_data["name"] if isinstance(item_data, dict) else item_data
                    desc = item_data.get("desc", "") if isinstance(item_data, dict) else ""
                    self._draw_icon_button(sx - 2, sy2, PANEL_WIDTH - 20, 46,
                                          name, is_sel, desc=desc)
            else:
                self._draw_text("（背包已空）", sx + 10, menu_start_y + 50,
                               COLORS["text_dim"], self.font)

        # 粒子绘制
        self.particles.draw(self.screen)

        # 底部操作提示
        self._draw_text("↑↓ 选择  Enter 确认  Esc 返回",
                       0, HEIGHT - 25, COLORS["text_dim"], self.font_small,
                       max_width=TEXT_AREA_WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 特效触发（供外部调用）
    # ═══════════════════════════════════════════

    def combat_hit_effect(self, x: int, y: int, damage: int, is_critical: bool = False):
        """战斗命中特效。"""
        # 屏幕震动
        if is_critical:
            self.screen_shake.trigger(12.0, 0.4)
        elif damage > 20:
            self.screen_shake.trigger(4.0, 0.2)

        # 粒子
        color = COLORS["gold_bright"] if is_critical else COLORS["red"]
        count = 15 if is_critical else 8
        self.particles.emit(x, y, count=count, speed=120, spread=360,
                           color=color, size=3.0, life=0.6, decay="spark")

        # 浮动数字
        text = f"CRIT {damage}!" if is_critical else f"-{damage}"
        self.floating_texts.spawn(x, y, text, color)

    def combat_heal_effect(self, x: int, y: int, amount: int):
        """治疗特效。"""
        self.particles.emit(x, y, count=6, speed=60, spread=200,
                           color=COLORS["green"], size=2.5, life=0.8,
                           gravity=-20, decay="ease")
        self.floating_texts.spawn(x, y, f"+{amount}", COLORS["green"])

    def combat_miss_effect(self, x: int, y: int):
        """未命中特效。"""
        self.floating_texts.spawn(x, y, "MISS", COLORS["text_dim"])

    def level_up_effect(self, x: int, y: int):
        """升级特效。"""
        self.particles.emit(x, y, count=25, speed=150, spread=360,
                           color=COLORS["gold_bright"], size=4.0, life=1.2,
                           gravity=-30, decay="ease")
        self.screen_shake.trigger(3.0, 0.5)

    def clear_effects(self):
        """清除所有特效。"""
        self.particles.clear()
        self.floating_texts.clear()

    # ═══════════════════════════════════════════
    # 角色详情面板
    # ═══════════════════════════════════════════

    def draw_character_sheet(self, player: Character, player2: Character = None):
        """绘制角色详情面板。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        if player2:
            self._draw_character_panel(player, 30, "P1")
            self._draw_character_panel(player2, WIDTH // 2 + 10, "P2")
        else:
            self._draw_character_panel(player, 30)

        self._draw_text("按 T 技能树 | 按 A 属性分配 | 其他键返回", 0, HEIGHT - 40,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    def _draw_character_panel(self, player: Character, x: int, label: str = ""):
        """绘制单角色详情面板。"""
        w = WIDTH // 2 - 40 if label else WIDTH - 80
        _draw_panel_rounded(self.screen, x, 30, w, HEIGHT - 80,
                           COLORS["panel"], COLORS["border"], 2, 8)

        title = f"[{label}] {player.name}" if label else f"📋 {player.name}"
        title_full = f"{title}  —  {player.char_class.icon} {player.char_class.display_name}  Lv.{player.level}"
        self._draw_text(title_full, 0, 48,
                       COLORS["gold_bright"],
                       self.font_title if not label else self.font,
                       max_width=x + w, center=not bool(label))

        y = 90 if label else 130
        cx = x + 20

        # 进度条
        bar_w = w - 50
        self._draw_text(f"❤ HP: {player.stats.hp}/{player.stats.max_hp}", cx, y,
                       COLORS["text"], self.font_small)
        self._draw_bar(cx + 180, y + 2, bar_w - 180, 12,
                      player.stats.hp, player.stats.max_hp, COLORS["hp_bar"])
        y += 22

        self._draw_text(f"💙 MP: {player.stats.mp}/{player.stats.max_mp}", cx, y,
                       COLORS["text"], self.font_small)
        self._draw_bar(cx + 180, y + 2, bar_w - 180, 12,
                      player.stats.mp, player.stats.max_mp, COLORS["mp_bar"])
        y += 22

        self._draw_text(f"⭐ EXP: {player.xp}/{player.xp_to_next}", cx, y,
                       COLORS["text"], self.font_small)
        self._draw_bar(cx + 180, y + 2, bar_w - 180, 12,
                      player.xp, player.xp_to_next, COLORS["xp_bar"])
        y += 25

        # 金币 + 暗影精华（分两行紧凑显示）
        self._draw_text(f"\U0001f4b0 {player.gold} GP     \U0001f48e {player.shadow_essence} 精华",
                       cx, y, COLORS["gold"], self.font_small, max_width=bar_w)
        y += 17
        self._draw_text(f"\U0001f4dc {player.skill_points} 技能点    \u2b06 {player.pending_attr_points} 属性点",
                       cx, y, COLORS["gold_dark"], self.font_small, max_width=bar_w)
        y += 20

        # 属性
        attrs = [
            f"STR:{player.stats.strength}(+{player.str_mod})  DEX:{player.stats.dexterity}(+{player.dex_mod})",
            f"INT:{player.stats.intelligence}(+{player.int_mod})  WIS:{player.stats.wisdom}(+{player.wis_mod})",
            f"CHA:{player.stats.charisma}(+{player.cha_mod})  LUK:{player.stats.luck}",
        ]
        for attr in attrs:
            self._draw_text(attr, cx, y, COLORS["text"], self.font_small)
            y += 18

        y += 5
        pygame.draw.line(self.screen, COLORS["border"],
                        (cx, y), (cx + w - 30, y), 1)
        y += 10

        # 技能（只显示已解锁的）
        unlocked = player.get_unlocked_skills()
        self._draw_text(f"\U0001f4dc 技能 ({len(unlocked)}):", cx, y, COLORS["gold"], self.font_small)
        y += 20
        for skill in unlocked:
            lock = "" if not skill.is_locked else " [已锁]"
            cd_status = f"CD:{skill.current_cooldown}" if skill.current_cooldown > 0 else "就绪"
            self._draw_text(f"\u2022 {skill.name}  MP:{skill.mp_cost} {cd_status}{lock}",
                           cx + 5, y, COLORS["text"], self.font_small, max_width=w - 40)
            y += 16
            self._draw_text(f"  {skill.description}", cx + 5, y,
                           COLORS["text_dim"], self.font_small, max_width=w - 40)
            y += 18

        if player.items:
            y += 5
            pygame.draw.line(self.screen, COLORS["border"],
                           (cx, y), (cx + w - 30, y), 1)
            y += 10
            self._draw_text(f"🎒 道具 ({len(player.items)}/10):", cx, y,
                           COLORS["gold"], self.font_small)
            y += 20
            for item in player.items:
                name = item["name"] if isinstance(item, dict) else item
                desc = item.get("desc", "") if isinstance(item, dict) else ""
                self._draw_text(f"• {name} — {desc}", cx + 5, y,
                               COLORS["text"], self.font_small,
                               max_width=w - 40)
                y += 18

        # 装备
        y += 5
        pygame.draw.line(self.screen, COLORS["border"],
                       (cx, y), (cx + w - 30, y), 1)
        y += 10
        self._draw_text("\u2694 装备:", cx, y, COLORS["gold"], self.font_small)
        y += 18

        slot_names = {"weapon": "武器", "armor": "护甲", "accessory_1": "饰品1", "accessory_2": "饰品2"}
        for slot_key, slot_label in slot_names.items():
            eq = player.equipment.get(slot_key)
            if eq:
                atk = f"攻+{eq.attack}" if eq.attack > 0 else ""
                def_ = f"防+{eq.defense}" if eq.defense > 0 else ""
                stats = " ".join(f"{atk} {def_}".split())
                name_text = f"\u2022 {slot_label}: {eq.full_name}  {stats}"
                self._draw_text(name_text, cx + 5, y,
                               COLORS["text"], self.font_small, max_width=w - 35)
                y += 15
                if eq.affixes:
                    affix_str = " | ".join(eq.get_affix_description())
                    self._draw_text(f"  {affix_str}", cx + 10, y,
                                   COLORS["gold"], self.font_small, max_width=w - 40)
                    y += 14
            else:
                self._draw_text(f"\u2022 {slot_label}: --空--", cx + 5, y,
                               COLORS["text_dim"], self.font_small)
                y += 15

    # ═══════════════════════════════════════════
    # 存档界面
    # ═══════════════════════════════════════════

    def draw_save_screen(self, save_infos: list, selected: int,
                         message: str = ""):
        """绘制存档管理界面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        self._draw_text("💾 存档管理", 0, 40,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True)

        for i in range(3):
            y = 140 + i * 140
            is_sel = i == selected
            bg = COLORS["panel_highlight"] if is_sel else COLORS["panel"]

            _draw_panel_rounded(self.screen, 100, y, WIDTH - 200, 118, bg,
                               COLORS["gold"] if is_sel else COLORS["border"],
                               3 if is_sel else 1, 6)

            if is_sel:
                self._draw_glow_border(100, y, WIDTH - 200, 118,
                                      COLORS["gold"], pulses=True)

            if i < len(save_infos):
                info = save_infos[i]
                self._draw_text(f"存档槽 {i+1}: {info['player_name']}  —  Lv.{info['level']}  {info['player_class']}",
                               130, y + 12,
                               COLORS["gold_bright"] if is_sel else COLORS["gold"],
                               self.font_big)
                self._draw_text(f"章节: 第{info['chapter']}章  |  保存时间: {info['timestamp']}",
                               130, y + 42, COLORS["text"], self.font_small)
                self._draw_text("Enter: 读取  |  Delete: 删除",
                               130, y + 68, COLORS["text_dim"], self.font_small)
            else:
                self._draw_text(f"存档槽 {i+1}: —— 空 ——", 130, y + 12,
                               COLORS["text_dim"], self.font_big)
                self._draw_text("Enter: 保存新存档", 130, y + 42,
                               COLORS["text_dim"], self.font_small)

        if message:
            # 成功消息：短暂绿色高亮
            msg_color = COLORS["green"] if "成功" in message or "保存" in message else COLORS["red"]
            self._draw_text(message, 0, HEIGHT - 90, msg_color, self.font,
                           max_width=WIDTH, center=True)

        self._draw_text("↑↓ 选择  |  Enter 确认  |  Esc 返回",
                       0, HEIGHT - 40, COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 游戏结束 / 通关
    # ═══════════════════════════════════════════

    def draw_game_over(self, text: str = "你被击败了..."):
        """绘制游戏结束画面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg_dark"])

        # 缓慢粒子效果
        if self.time_ms % 100 < 30:
            self.particles.emit(
                random.uniform(200, WIDTH - 200), HEIGHT // 2,
                count=2, speed=30, spread=180,
                color=(100, 20, 20), size=2.0, life=2.0, decay="ease"
            )
        self.particles.draw(self.screen)

        self._draw_text("💀", 0, 150, COLORS["red"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True)

        self._draw_text(text, 0, 230, COLORS["red_bright"], self.font_title,
                       max_width=WIDTH, center=True)
        self._draw_text("黑暗中，故事并未结束...", 0, 300,
                       COLORS["text_dim"], self.font,
                       max_width=WIDTH, center=True)
        self._draw_text("按 Enter 返回标题画面", 0, 400,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    def draw_game_win(self):
        """绘制通关画面。"""
        self._begin_frame()
        self.screen.fill((8, 5, 35))

        # 金色粒子
        if self.time_ms % 80 < 40:
            self.particles.emit(
                random.uniform(100, WIDTH - 100), random.uniform(100, 500),
                count=3, speed=40, spread=360,
                color=COLORS["gold_bright"], size=3.0,
                life=2.5, gravity=-15, decay="ease"
            )
        self.particles.draw(self.screen)

        self._draw_text("☀️", 0, 100, COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True, glow=True)

        self._draw_text("黎 明 降 临", 0, 175, COLORS["gold_bright"],
                       self.font_title, max_width=WIDTH, center=True,
                       shadow=True, glow=True)

        self._draw_text("你成功打破了绝夜的诅咒，为这个世界重新带来了光明。",
                       0, 260, COLORS["gold"], self.font,
                       max_width=WIDTH, center=True)
        self._draw_text("感谢游玩「绝夜之旅」", 0, 320,
                       COLORS["text_bright"], self.font,
                       max_width=WIDTH, center=True)
        self._draw_text("按 Enter 返回标题画面  |  按 N 开始 New Game+", 0, 430,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)
        self._draw_text("🔥 New Game+: 继承装备和金币，重新挑战更高难度", 0, 470,
                       COLORS["gold"], self.font_small,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 章节开场
    # ═══════════════════════════════════════════

    def draw_chapter_intro(self, chapter):
        """绘制章节开场介绍。"""
        self._begin_frame()
        
        # 场景背景
        from .scene_renderer import SceneRenderer
        scene_name = SceneRenderer.scene_for_chapter(chapter.chapter_id)
        self.scene.set_scene(scene_name)
        self.scene.render(self.screen, 0, 0, WIDTH, HEIGHT)
        
        # 暗色叠加层让文字可读
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 3, 15, 160))
        self.screen.blit(overlay, (0, 0))

        # 章节号大字
        self._draw_text(f"第 {chapter.chapter_id} 章", 0, 100,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True, glow=True)

        # 副标题
        self._draw_text(f"「{chapter.subtitle}」", 0, 165,
                       COLORS["gold"], self.font_big,
                       max_width=WIDTH, center=True)

        # 装饰分割线
        sep_y = 210
        deco = "━━━━━━  ✦  ━━━━━━"
        self._draw_text(deco, 0, sep_y,
                       COLORS["border_bright"], self.font_small,
                       max_width=WIDTH, center=True)

        # 章节描述
        self._draw_text(chapter.intro_text, 0, 255,
                       COLORS["text"], self.font,
                       max_width=WIDTH - 200, center=True)

        # 底部提示（脉冲效果）
        pulse_color = _color_lerp(
            COLORS["text_dim"], COLORS["text"],
            0.5 + 0.5 * math.sin(self.time_ms / 800.0)
        )
        self._draw_text("按 Enter 踏上征途", 0, HEIGHT - 80,
                       pulse_color, self.font_big,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # Phase 2：难度选择
    # ═══════════════════════════════════════════

    def draw_difficulty_select(self, options: list, selected: int):
        """绘制难度选择界面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        self._draw_text("选择游戏难度", 0, 80,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True)
        self._draw_text("难度影响敌人强度、掉落和奖励", 0, 130,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

        from .combat import DIFFICULTY_SETTINGS
        keys = ["easy", "normal", "hard"]
        descs = [
            "敌人生命/攻击/防御降低30%/20%/20%，适合轻松体验剧情",
            "均衡的战斗体验，推荐首选",
            "敌人生命/攻击/防御提升30%/20%/20%，奖励更丰厚",
        ]

        for i, (opt, key) in enumerate(zip(options, keys)):
            y = 220 + i * 130
            is_sel = i == selected
            bg = COLORS["panel_highlight"] if is_sel else COLORS["panel"]
            _draw_panel_rounded(self.screen, 120, y, WIDTH - 240, 110, bg,
                               COLORS["gold"] if is_sel else COLORS["border"],
                               3 if is_sel else 1, 8)

            if is_sel:
                self._draw_glow_border(120, y, WIDTH - 240, 110, COLORS["gold"], pulses=True)

            settings = DIFFICULTY_SETTINGS[key]
            self._draw_text(f"▶ {opt} 模式", 150, y + 10,
                           COLORS["gold_bright"] if is_sel else COLORS["text"], self.font_big)
            self._draw_text(descs[i], 150, y + 38,
                           COLORS["text"], self.font_small, max_width=WIDTH - 300)
            self._draw_text(f"敌人倍率: HP×{settings['hp_mult']} ATK×{settings['atk_mult']} "
                           f"DEF×{settings['def_mult']} | "
                           f"奖励倍率: XP×{settings['xp_mult']} 金币×{settings['gold_mult']}",
                           150, y + 62, COLORS["text_dim"], self.font_small)

        self._draw_text("↑↓ 选择  |  Enter 确认", 0, HEIGHT - 50,
                       COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # Phase 2：神秘商人商店
    # ═══════════════════════════════════════════

    def draw_shop_screen(self, player, player2, shop_items: list,
                         selected: int, chapter_manager, message: str = ""):
        """绘制神秘商人商店界面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        ch = chapter_manager.current_chapter
        chapter_name = f"第{ch.chapter_id}章 {ch.subtitle}" if ch else ""

        # 场景背景（列车场景）
        self.scene.set_scene("train")
        self.scene.render(self.screen, 0, 0, WIDTH, HEIGHT)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 3, 15, 200))
        self.screen.blit(overlay, (0, 0))

        # 标题
        self._draw_text("🧙 神秘商人", 0, 40,
                       COLORS["gold_bright"], self.font_title,
                       max_width=WIDTH, center=True, shadow=True, glow=True)
        self._draw_text(f"「来瞧瞧我的珍藏吧...这段路途可不容易」  —  {chapter_name}",
                       0, 90, COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

        # 右上角：玩家经济
        self._draw_text(f"💰 {player.gold} GP  |  💎 {player.shadow_essence} 暗影精华",
                       WIDTH - 400, 120, COLORS["gold"], self.font_small)

        # 商品列表
        item_start_y = 150
        visible_count = min(6, len(shop_items))
        for i in range(visible_count):
            idx = i
            if idx >= len(shop_items):
                break
            item = shop_items[idx]
            y = item_start_y + i * 70
            is_sel = idx == selected

            bg = COLORS["panel_highlight"] if is_sel else COLORS["panel"]
            border = COLORS["gold"] if is_sel else COLORS["border"]
            _draw_panel_rounded(self.screen, 60, y, WIDTH - 120, 63, bg, border,
                               2 if is_sel else 1, 5)

            if is_sel:
                self._draw_glow_border(60, y, WIDTH - 120, 63, COLORS["gold"], pulses=True)

            from .shop import can_afford
            curr = item.currency.upper().replace("SHADOW_ESSENCE", "精华")
            price_text = f"[{item.price} {curr}]"
            currency_color = COLORS["gold"] if item.currency == "gold" else COLORS["purple"]

            affable = can_afford(item, player.gold, player.shadow_essence) and item.stock != 0
            name_color = COLORS["gold_bright"] if is_sel else (COLORS["text"] if affable else COLORS["text_dim"])
            prefix = "▶ " if is_sel else "  "
            self._draw_text(f"{prefix}{item.name} {price_text}", 80, y + 5,
                           name_color, self.font_big)
            self._draw_text(item.description, 80, y + 33,
                           COLORS["text_dim"], self.font_small)
            if item.stock > 0:
                self._draw_text(f"库存: {item.stock}", WIDTH - 180, y + 33,
                               COLORS["text_dim"], self.font_small)

        # 更多提示
        if len(shop_items) > visible_count:
            self._draw_text(f"...还有 {len(shop_items) - visible_count} 件商品",
                           0, item_start_y + visible_count * 70 + 5,
                           COLORS["text_dim"], self.font_small,
                           max_width=WIDTH, center=True)

        # 消息
        if message:
            msg_color = COLORS["green"] if "✅" in message else COLORS["red"]
            self._draw_text(message, 0, HEIGHT - 100, msg_color, self.font,
                           max_width=WIDTH, center=True)

        self._draw_text("↑↓ 选择  |  Enter 购买  |  Esc 离开",
                       0, HEIGHT - 50, COLORS["text_dim"], self.font_small,
                       max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # Phase 2：技能树与属性分配
    # ═══════════════════════════════════════════

    def draw_skill_tree_screen(self, player, selected: int, message: str = ""):
        """绘制技能树和属性分配界面。"""
        self._begin_frame()
        self.screen.fill(COLORS["bg"])

        # ── 左侧：技能树 ──
        left_w = TEXT_AREA_WIDTH
        panel_surf = pygame.Surface((left_w, HEIGHT - 20), pygame.SRCALPHA)
        panel_surf.fill((*COLORS["panel"], 220))
        self.screen.blit(panel_surf, (10, 10))

        # 标题
        self._draw_text(f"📜 技能树 — {player.name}  Lv.{player.level}",
                       25, 18, COLORS["gold_bright"], self.font_big)
        self._draw_text(f"技能点: {player.skill_points}  |  属性点: {player.pending_attr_points}",
                       25, 44, COLORS["gold"], self.font_small)

        # 技能列表
        skill_y = 75
        unlocked = player.get_unlocked_skills()
        available = player.get_available_branches()
        all_display = unlocked + [player.skills[i] for i in available]

        if not all_display:
            self._draw_text("(暂无技能)", 25, skill_y, COLORS["text_dim"], self.font)
        else:
            for i, skill in enumerate(all_display):
                sy = skill_y + i * 36
                is_sel = i == selected
                is_locked = skill.is_locked

                prefix = "▸ " if is_sel else "  "
                lock_icon = "🔒 " if is_locked else "✅ "
                color = COLORS["gold"] if is_sel else (COLORS["text_dim"] if is_locked else COLORS["text"])

                branch = f" [{skill.branch_name}]" if skill.branch_name else ""
                status = ""
                if is_locked:
                    cost = 3 if skill.is_ultimate else 1
                    status = f" 需要{cost}技能点 Lv.{skill.required_level}"
                else:
                    cd_info = f"CD:{skill.cooldown}" if skill.cooldown > 0 else ""
                    status = f" MP:{skill.mp_cost} {cd_info}"

                self._draw_text(f"{prefix}{lock_icon}{skill.name}{branch}",
                               30, sy, color, self.font_small)
                # 描述
                self._draw_text(f"  {skill.description}  {status}",
                               30, sy + 16, COLORS["text_dim"], self.font_small)

        # ── 右侧：属性分配面板 ──
        sx, sy = SIDEBAR_X + 12, 15
        sw = PANEL_WIDTH - 20
        self._draw_panel(SIDEBAR_X, 0, PANEL_WIDTH, HEIGHT)

        self._draw_text("⬆ 属性分配", sx - 7, sy,
                       COLORS["gold_bright"], self.font_big, max_width=sw + 5)
        self._draw_text(f"待分配: {player.pending_attr_points}点", sx - 7, sy + 30,
                       COLORS["gold"], self.font_small)

        attr_y = sy + 60
        attrs = [
            ("1", "💪 力量 STR", player.stats.strength),
            ("2", "🏃 敏捷 DEX", player.stats.dexterity),
            ("3", "🧠 智力 INT", player.stats.intelligence),
            ("4", "🔮 感知 WIS", player.stats.wisdom),
            ("5", "💬 魅力 CHA", player.stats.charisma),
            ("6", "🍀 幸运 LUK", player.stats.luck),
        ]
        for key, name, val in attrs:
            self._draw_text(f"[{key}] {name}: {val}", sx - 7, attr_y,
                           COLORS["text"], self.font_small)
            attr_y += 25

        attr_y += 10
        self._draw_text("按数字键 1-6 分配属性", sx - 7, attr_y,
                       COLORS["text_dim"], self.font_small)

        # 消息
        if message:
            msg_color = COLORS["green"] if "✅" in message else COLORS["red"]
            self._draw_text(message, 0, HEIGHT - 30, msg_color, self.font_small,
                           max_width=WIDTH, center=True)
        else:
            self._draw_text("←→ 选择技能  Enter 解锁  Esc/Q 返回",
                           0, HEIGHT - 30, COLORS["text_dim"], self.font_small,
                           max_width=WIDTH, center=True)

    # ═══════════════════════════════════════════
    # 系统工具
    # ═══════════════════════════════════════════

    def set_current_scene(self, scene_name: str):
        """设置当前场景（由引擎调用）。"""
        self._current_scene_name = scene_name
        self.scene.set_scene(scene_name)

    def set_scene_from_event(self, event_type_str: str, chapter_id: int = 1):
        """根据事件类型和章节设置场景。"""
        # Boss战用终章场景
        if event_type_str == "boss":
            self._current_scene_name = "final_chamber"
            self.scene.set_scene("final_chamber")
        elif event_type_str == "combat":
            self._current_scene_name = "corrupted_castle"
            self.scene.set_scene("corrupted_castle")
        elif event_type_str == "train":
            self._current_scene_name = "train"
            self.scene.set_scene("train")
        else:
            from .scene_renderer import SceneRenderer
            scene_name = SceneRenderer.scene_for_chapter(chapter_id)
            self._current_scene_name = scene_name
            self.scene.set_scene(scene_name)

    def update_display(self):
        """更新画面。"""
        pygame.display.flip()
        self.clock.tick(60)  # 提升到60fps

    def tick(self, fps: int = 60):
        self.clock.tick(fps)

    def cleanup(self):
        pygame.quit()
