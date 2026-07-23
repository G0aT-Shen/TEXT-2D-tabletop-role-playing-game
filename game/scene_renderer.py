"""程序化场景渲染 — 为绝夜之旅生成暗黑风格插图，不再纯文字。"""

import math
import random
import pygame
from typing import Tuple, List, Optional
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════
# 场景配置
# ══════════════════════════════════════════════════

@dataclass
class SceneConfig:
    name: str
    sky_colors: List[Tuple[int, int, int]]  # 天空渐变（底→顶）
    ground_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]       # 前景高亮
    mist_color: Tuple[int, int, int]
    moon: bool = False
    moon_color: Tuple[int, int, int] = (180, 160, 200)
    stars_count: int = 30
    architecture: Optional[str] = None       # "castle", "tower", "train", "ruins"
    vegetation: Optional[str] = None         # "forest", "dead_trees", "vines", "none"
    particles_type: Optional[str] = None     # "embers", "snow", "spores", "void_dust"


# 场景预设库
SCENE_PRESETS = {
    "train": SceneConfig(
        name="曙光号·列车",
        sky_colors=[(20, 12, 35), (28, 18, 50), (35, 22, 55)],
        ground_color=(18, 12, 28),
        accent_color=(220, 180, 60),
        mist_color=(40, 30, 60),
        moon=False, stars_count=8,
        architecture="train",
        particles_type="spores",
    ),
    "dark_forest": SceneConfig(
        name="暗夜森林",
        sky_colors=[(10, 8, 22), (18, 12, 30), (25, 15, 35)],
        ground_color=(12, 10, 20),
        accent_color=(60, 120, 60),
        mist_color=(25, 20, 40),
        moon=True, moon_color=(140, 120, 180),
        stars_count=40,
        vegetation="forest",
        particles_type="spores",
    ),
    "corrupted_castle": SceneConfig(
        name="暗影城堡",
        sky_colors=[(8, 5, 18), (15, 8, 25), (22, 12, 35)],
        ground_color=(10, 8, 16),
        accent_color=(200, 40, 40),
        mist_color=(35, 15, 25),
        moon=True, moon_color=(180, 100, 100),
        stars_count=25,
        architecture="castle",
        particles_type="embers",
    ),
    "crystal_cavern": SceneConfig(
        name="深渊裂隙",
        sky_colors=[(5, 8, 18), (10, 15, 30), (15, 22, 45)],
        ground_color=(8, 10, 15),
        accent_color=(80, 180, 220),
        mist_color=(20, 25, 50),
        moon=False, stars_count=0,
        architecture="ruins",
        particles_type="void_dust",
    ),
    "final_chamber": SceneConfig(
        name="绝夜神殿",
        sky_colors=[(2, 2, 8), (8, 4, 18), (20, 8, 30)],
        ground_color=(4, 3, 8),
        accent_color=(255, 30, 40),
        mist_color=(25, 8, 15),
        moon=False, stars_count=15,
        architecture="tower",
        particles_type="embers",
    ),
    "temple_ruins": SceneConfig(
        name="荒废神殿",
        sky_colors=[(12, 10, 25), (22, 16, 38), (30, 20, 50)],
        ground_color=(14, 12, 22),
        accent_color=(100, 80, 160),
        mist_color=(30, 22, 50),
        moon=True, moon_color=(160, 140, 200),
        stars_count=35,
        architecture="ruins",
        particles_type="snow",
    ),
}

# 章节→默认场景映射
CHAPTER_SCENES = {
    1: "train",            # 第1章：列车→暗夜森林
    2: "dark_forest",      # 第2章：暗夜森林
    3: "corrupted_castle", # 第3章：暗影城堡
    4: "crystal_cavern",   # 第4章：深渊→最终boss
}


# ══════════════════════════════════════════════════
# 场景渲染器
# ══════════════════════════════════════════════════

class SceneRenderer:
    """程序化场景生成器——纯pygame绘图，零外部资源。"""

    def __init__(self, screen_w: int, screen_h: int):
        self.w = screen_w
        self.h = screen_h
        self.current_scene: Optional[SceneConfig] = None
        self._scene_cache: dict = {}  # (scene_name, tick_frame) → surface
        self._tick = 0
        self._random_seed = random.randint(0, 10000)

    # ── 场景切换 ──

    def set_scene(self, scene_name: str):
        """切换到指定场景。"""
        self.current_scene = SCENE_PRESETS.get(scene_name, SCENE_PRESETS["dark_forest"])
        self._random_seed = random.randint(0, 10000)

    def set_chapter_scene(self, chapter_id: int):
        """根据章节自动选择场景。"""
        name = CHAPTER_SCENES.get(chapter_id, "dark_forest")
        self.set_scene(name)

    # ── 主渲染入口 ──

    def render(self, screen: pygame.Surface, x: int, y: int, w: int, h: int):
        """渲染场景到指定矩形区域。"""
        self._tick += 1
        if self.current_scene is None:
            self.set_scene("dark_forest")

        cfg = self.current_scene
        t = pygame.time.get_ticks() / 1000.0
        rng = random.Random(self._random_seed)

        # ── 天空渐变 ──
        self._draw_sky(screen, x, y, w, h, cfg)

        # ── 月亮 ──
        if cfg.moon:
            self._draw_moon(screen, x, y, w, h, cfg, t)

        # ── 星星 ──
        if cfg.stars_count > 0:
            self._draw_stars(screen, x, y, w, h, cfg, t, rng)

        # ── 远景山脉/地平线 ──
        self._draw_horizon(screen, x, y, w, h, cfg, rng)

        # ── 建筑 ──
        if cfg.architecture:
            self._draw_architecture(screen, x, y, w, h, cfg, t, rng)

        # ── 植被 ──
        if cfg.vegetation:
            self._draw_vegetation(screen, x, y, w, h, cfg, t, rng)

        # ── 地面 ──
        self._draw_ground(screen, x, y, w, h, cfg)

        # ── 薄雾 ──
        self._draw_mist(screen, x, y, w, h, cfg, t, rng)

        # ── 粒子效果 ──
        if cfg.particles_type:
            self._draw_particles(screen, x, y, w, h, cfg, t, rng)

    # ═══════════════════════════════════════════
    # 子绘制单元
    # ═══════════════════════════════════════════

    def _draw_sky(self, screen, x, y, w, h, cfg: SceneConfig):
        """垂直渐变天空。"""
        bands = len(cfg.sky_colors) - 1
        if bands == 0:
            screen.fill(cfg.sky_colors[0], (x, y, w, h))
            return
        band_h = h // bands
        for i in range(bands):
            c1 = cfg.sky_colors[i]
            c2 = cfg.sky_colors[i + 1]
            sy = y + i * band_h
            for row in range(band_h + 1):
                ratio = row / max(1, band_h)
                r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                pygame.draw.line(screen, (r, g, b),
                               (x, sy + row), (x + w, sy + row))

    def _draw_moon(self, screen, x, y, w, h, cfg: SceneConfig, t: float):
        """暗月——带光晕和环形山暗斑。"""
        mx = x + w * 3 // 4
        my = y + h // 5
        mr = min(w, h) // 10

        # 外层光晕
        for i in range(3, 0, -1):
            alpha = 15 * i
            rr = mr + i * 12
            color = (*cfg.moon_color, alpha)
            surf = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (rr + 2, rr + 2), rr)
            screen.blit(surf, (mx - rr - 2, my - rr - 2))

        # 月亮本体
        pygame.draw.circle(screen, cfg.moon_color, (mx, my), mr)
        # 明暗面
        shadow_color = tuple(max(0, c - 60) for c in cfg.moon_color)
        pygame.draw.circle(screen, shadow_color, (mx + mr // 3, my), mr // 2)

    def _draw_stars(self, screen, x, y, w, h, cfg: SceneConfig, t: float, rng: random.Random):
        """闪烁星空（仅天空区域）。"""
        star_area_h = h // 2  # 只在天空上半部
        rng.seed(self._random_seed)
        for _ in range(cfg.stars_count):
            sx = x + rng.randint(10, w - 10)
            sy = y + rng.randint(5, star_area_h - 5)
            twinkle = 0.4 + 0.6 * abs(math.sin(t * rng.uniform(1.2, 3.5) + rng.uniform(0, 6)))
            brightness = int(twinkle * 180)
            size = rng.uniform(0.8, 2.2) * twinkle
            color = (brightness, brightness, min(255, brightness + 30))
            pygame.draw.circle(screen, color, (int(sx), int(sy)), max(0.5, size))

    def _draw_horizon(self, screen, x, y, w, h, cfg: SceneConfig, rng: random.Random):
        """地平线——远处山脉剪影。"""
        horizon_y = y + h * 3 // 5
        rng.seed(self._random_seed + 1)
        peaks = rng.randint(4, 8)
        points = [(x, horizon_y + 20)]
        for i in range(peaks + 1):
            px = x + int(w * i / peaks)
            py = horizon_y - rng.randint(10, h // 6)
            points.append((px, py))
        points.append((x + w, horizon_y + 20))

        # 远山（淡色）
        far_color = tuple(max(0, c - 15) for c in cfg.ground_color)
        self._draw_polygon_aa(screen, points, far_color)

        # 近山（深色剪影）
        points2 = [(x, horizon_y + 30)]
        for i in range(peaks + 2):
            px = x + int(w * i / (peaks + 1))
            py = horizon_y - rng.randint(3, h // 10)
            points2.append((px, py))
        points2.append((x + w, horizon_y + 30))
        self._draw_polygon_aa(screen, points2, cfg.ground_color)

    def _draw_architecture(self, screen, x, y, w, h, cfg: SceneConfig, t: float, rng: random.Random):
        """绘制建筑剪影。"""
        rng.seed(self._random_seed + 2)
        ground_y = y + h * 3 // 5

        if cfg.architecture == "castle":
            self._draw_castle(screen, x, y, w, h, cfg, ground_y, rng, t)
        elif cfg.architecture == "tower":
            self._draw_tower(screen, x, y, w, h, cfg, ground_y, rng, t)
        elif cfg.architecture == "train":
            self._draw_train(screen, x, y, w, h, cfg, ground_y, rng, t)
        elif cfg.architecture == "ruins":
            self._draw_ruins(screen, x, y, w, h, cfg, ground_y, rng, t)

    def _draw_castle(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """哥特城堡剪影——塔楼、城垛、窗户。"""
        castle_w = w // 2
        cx = x + w // 2 - castle_w // 2
        # 主楼
        tower_h = h // 3
        tower_top = ground_y - tower_h
        color = cfg.ground_color

        main_rect = (cx + castle_w // 4, tower_top, castle_w // 2, tower_h)
        pygame.draw.rect(screen, color, main_rect)

        # 两侧塔楼
        tw = castle_w // 6
        for side_x in [cx, cx + castle_w - tw]:
            th = tower_h + rng.randint(15, 40)
            tt = ground_y - th
            pygame.draw.rect(screen, color, (side_x, tt, tw, th))
            # 塔楼尖顶
            spire_pts = [(side_x, tt), (side_x + tw // 2, tt - tw), (side_x + tw, tt)]
            pygame.draw.polygon(screen, color, spire_pts)

        # 窗户——随机几个亮着
        win_color = (255, 180, 40)
        win_count = rng.randint(3, 7)
        for _ in range(win_count):
            wx = cx + castle_w // 4 + rng.randint(5, castle_w // 2 - 15)
            wy = tower_top + rng.randint(10, tower_h - 20)
            ww, wh = 8, 12
            flicker = 0.5 + 0.5 * abs(math.sin(t * rng.uniform(1.5, 3.5) + rng.uniform(0, 5)))
            alpha = int(flicker * 180)
            win_surf = pygame.Surface((ww + 4, wh + 4), pygame.SRCALPHA)
            pygame.draw.rect(win_surf, (*win_color, alpha), (2, 2, ww, wh))
            # 拱形顶
            pygame.draw.ellipse(win_surf, (*win_color, alpha), (2, 0, ww, wh // 2))
            screen.blit(win_surf, (wx - 2, wy - 2))

    def _draw_tower(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """孤塔/神殿剪影。"""
        tower_w = w // 4
        tx = x + w // 2 - tower_w // 2
        tower_h = h // 2
        color = cfg.ground_color
        pygame.draw.rect(screen, color, (tx, ground_y - tower_h, tower_w, tower_h))

        # 塔顶
        top_w = tower_w + 15
        top_pts = [(tx - 8, ground_y - tower_h), (tx + tower_w + 8, ground_y - tower_h),
                   (tx + tower_w + 2, ground_y - tower_h - 25),
                   (tx - 2, ground_y - tower_h - 25)]
        pygame.draw.polygon(screen, color, top_pts)

        # 中央光柱
        pulse = 0.4 + 0.6 * abs(math.sin(t * 1.5))
        beam_alpha = int(pulse * 80)
        beam_surf = pygame.Surface((20, tower_h), pygame.SRCALPHA)
        for row in range(tower_h):
            a = int(beam_alpha * (1 - row / tower_h))
            pygame.draw.line(beam_surf, (*cfg.accent_color, a),
                           (0, row), (20, row))
        screen.blit(beam_surf, (tx + tower_w // 2 - 10, ground_y - tower_h))

    def _draw_train(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """蒸汽列车剪影。"""
        train_w = w * 3 // 5
        tx = x + w // 2 - train_w // 2
        train_h = h // 7
        body_y = ground_y - train_h
        color = cfg.ground_color

        # 车身
        pygame.draw.rect(screen, color, (tx, body_y, train_w, train_h), border_radius=4)
        # 车顶
        roof_y = body_y - train_h // 3
        pygame.draw.rect(screen, color, (tx + 8, roof_y, train_w - 16, train_h // 3), border_radius=3)
        # 烟囱
        chimney_w = train_h // 2
        chimney_x = tx + train_w // 6
        chimney_h = train_h // 2
        pygame.draw.rect(screen, color, (chimney_x, roof_y - chimney_h, chimney_w, chimney_h))
        # 车轮
        for wx in [tx + train_w // 6, tx + train_w // 2, tx + train_w * 5 // 6]:
            pygame.draw.circle(screen, color, (wx, ground_y), train_h // 4 + 2)
            pygame.draw.circle(screen, (30, 20, 40), (wx, ground_y), train_h // 4)

        # 车窗亮光
        win_color = (255, 200, 80)
        for i in range(4):
            wx = tx + train_w // 5 + i * train_w // 7
            wy = body_y + train_h // 4
            flicker = 0.6 + 0.4 * abs(math.sin(t * 2.0 + i * 0.8))
            alpha = int(flicker * 150)
            win_surf = pygame.Surface((16, 14), pygame.SRCALPHA)
            pygame.draw.rect(win_surf, (*win_color, alpha), (0, 0, 16, 14), border_radius=2)
            screen.blit(win_surf, (wx, wy))

    def _draw_ruins(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """废墟剪影——断柱、残垣。"""
        color = cfg.ground_color
        # 断柱
        for i in range(rng.randint(2, 4)):
            rx = x + w // 5 + i * w // 4 + rng.randint(-15, 15)
            rh = rng.randint(h // 8, h // 4)
            rw = rng.randint(8, 15)
            pygame.draw.rect(screen, color, (rx, ground_y - rh, rw, rh))
            # 柱顶裂缝
            crack_y = ground_y - rh + rng.randint(5, 12)
            pygame.draw.line(screen, cfg.sky_colors[0], (rx + rw // 2, crack_y),
                           (rx + rw // 2 + rng.randint(-4, 4), crack_y + rng.randint(5, 10)), 1)
        # 地面碎石
        for _ in range(rng.randint(3, 6)):
            sx = x + rng.randint(10, w - 10)
            sy = ground_y + rng.randint(5, 20)
            sr = rng.randint(2, 5)
            pygame.draw.rect(screen, color, (sx, sy, sr * 2, sr))

    def _draw_vegetation(self, screen, x, y, w, h, cfg, t, rng):
        """绘制植被剪影。"""
        rng.seed(self._random_seed + 3)
        ground_y = y + h * 3 // 5

        if cfg.vegetation == "forest":
            self._draw_forest(screen, x, y, w, h, cfg, ground_y, rng, t)
        elif cfg.vegetation == "dead_trees":
            self._draw_dead_trees(screen, x, y, w, h, cfg, ground_y, rng, t)
        elif cfg.vegetation == "vines":
            pass  # 简化

    def _draw_forest(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """暗黑森林——多层树干剪影。"""
        color = cfg.ground_color
        trunk_color = tuple(max(0, c - 8) for c in color)

        # 远景树（较淡）
        far_color = tuple(min(255, c + 20) for c in color)
        for _ in range(rng.randint(6, 10)):
            tx = x + rng.randint(0, w)
            th = rng.randint(h // 6, h // 3)
            tw = rng.randint(4, 8)
            pygame.draw.rect(screen, far_color, (tx, ground_y - th, tw, th))
            # 树冠
            canopy_r = tw * rng.randint(2, 4)
            canopy_y = ground_y - th - canopy_r // 2
            pygame.draw.ellipse(screen, far_color,
                              (tx - canopy_r + tw // 2, canopy_y, canopy_r * 2, canopy_r))

        # 近景树（剪影）
        for _ in range(rng.randint(4, 7)):
            tx = x + rng.randint(5, w - 5)
            th = rng.randint(h // 5, h // 2)
            tw = rng.randint(6, 14)
            pygame.draw.rect(screen, trunk_color, (tx, ground_y - th, tw, th))
            # 不规则树冠
            canopy_r = tw * rng.randint(3, 5)
            canopy_y = ground_y - th - canopy_r // 2
            # 多个椭圆叠出自然感
            for _ in range(3):
                cx = tx + tw // 2 + rng.randint(-canopy_r // 2, canopy_r // 2)
                cy = canopy_y + rng.randint(-canopy_r // 3, canopy_r // 3)
                cr = canopy_r * rng.uniform(0.5, 0.9)
                pygame.draw.ellipse(screen, trunk_color,
                                  (cx - cr, cy - cr, cr * 2, cr * 2))

    def _draw_dead_trees(self, screen, x, y, w, h, cfg, ground_y, rng, t):
        """枯树剪影——扭曲的枝干。"""
        color = cfg.ground_color
        for _ in range(rng.randint(3, 6)):
            tx = x + rng.randint(10, w - 10)
            th = rng.randint(h // 8, h // 4)
            tw = rng.randint(3, 7)
            pygame.draw.line(screen, color, (tx, ground_y), (tx, ground_y - th), tw)
            # 分枝
            for _ in range(rng.randint(1, 3)):
                branch_y = ground_y - th + rng.randint(th // 3, th * 2 // 3)
                branch_len = rng.randint(15, 40)
                branch_angle = rng.uniform(-1.2, -0.3) if rng.random() < 0.5 else rng.uniform(0.3, 1.2)
                bx = tx + int(branch_len * math.cos(branch_angle))
                by = branch_y + int(branch_len * math.sin(branch_angle))
                pygame.draw.line(screen, color, (tx, branch_y), (bx, by), max(1, tw - 1))

    def _draw_ground(self, screen, x, y, w, h, cfg):
        """地面区域。"""
        ground_y = y + h * 3 // 5
        pygame.draw.rect(screen, cfg.ground_color, (x, ground_y, w, h - ground_y))

    def _draw_mist(self, screen, x, y, w, h, cfg, t, rng):
        """流动薄雾——多层半透明椭圆。"""
        rng.seed(self._random_seed + 4)
        mist_count = rng.randint(4, 8)
        ground_y = y + h * 3 // 5
        for i in range(mist_count):
            phase = rng.uniform(0, math.pi * 2)
            drift = math.sin(t * 0.3 + phase) * 25
            mx = x + rng.randint(-20, w // 2) + int(drift)
            my = ground_y - rng.randint(20, h // 4)
            mw = rng.randint(w // 4, w // 2)
            mh = rng.randint(15, 35)
            alpha = int(rng.uniform(15, 35))
            mist_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
            pygame.draw.ellipse(mist_surf, (*cfg.mist_color, alpha),
                              (0, 0, mw, mh))
            screen.blit(mist_surf, (mx - mw // 2, my - mh // 2))

    def _draw_particles(self, screen, x, y, w, h, cfg, t, rng):
        """环境粒子——余烬/孢子/虚尘/雪花。"""
        rng.seed(self._random_seed + 5)
        count = {"embers": 25, "spores": 20, "void_dust": 30, "snow": 35}.get(cfg.particles_type, 15)

        if cfg.particles_type == "embers":
            color = (255, 140, 30)
            min_size, max_size = 0.8, 2.5
            speed_range = (15, 40)
        elif cfg.particles_type == "spores":
            color = (100, 200, 100)
            min_size, max_size = 0.5, 1.8
            speed_range = (5, 15)
        elif cfg.particles_type == "void_dust":
            color = (120, 160, 220)
            min_size, max_size = 0.6, 2.0
            speed_range = (8, 25)
        else:  # snow
            color = (200, 210, 230)
            min_size, max_size = 0.8, 2.0
            speed_range = (8, 20)

        for _ in range(count):
            px = rng.uniform(0, w)
            py = rng.uniform(0, h)
            # 基于时间+种子的循环位置
            phase_y = rng.uniform(0, h)
            phase_x = rng.uniform(0, math.pi * 2)
            effective_y = (phase_y + t * speed_range[0] * rng.uniform(0.7, 1.3)) % (h * 1.2) - h * 0.1
            effective_x = px + math.sin(t * rng.uniform(0.5, 1.2) + phase_x) * rng.uniform(8, 20)
            size = rng.uniform(min_size, max_size)
            alpha = int(rng.uniform(40, 120))
            px_int = x + int(effective_x)
            py_int = y + int(effective_y)
            if 0 <= px_int < x + w and 0 <= py_int < y + h:
                p_surf = pygame.Surface((int(size * 2) + 2, int(size * 2) + 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*color, alpha),
                                 (int(size) + 1, int(size) + 1), size)
                screen.blit(p_surf, (px_int - size, py_int - size))

    # ═══════════════════════════════════════════
    # 战斗场景: 敌人+玩家剪影
    # ═══════════════════════════════════════════

    def render_combat_background(self, screen: pygame.Surface, x: int, y: int, w: int, h: int,
                                 is_boss: bool = False, enemy_name: str = ""):
        """渲染战斗背景——更激烈的色调。"""
        t = pygame.time.get_ticks() / 1000.0
        rng = random.Random(self._random_seed)

        if is_boss:
            sky = [(4, 2, 10), (15, 5, 22), (30, 10, 35)]
            ground = (8, 4, 14)
            accent = (255, 40, 40)
        else:
            sky = [(12, 8, 25), (20, 14, 35), (28, 18, 45)]
            ground = (15, 10, 28)
            accent = (200, 160, 40)

        cfg = SceneConfig(
            name="combat", sky_colors=sky, ground_color=ground,
            accent_color=accent, mist_color=(25, 15, 35),
            stars_count=8 if not is_boss else 20,
            particles_type="embers" if is_boss else "spores",
        )

        # 渲染基本场景
        self._draw_sky(screen, x, y, w, h, cfg)
        if not is_boss:
            self._draw_stars(screen, x, y, w, h, cfg, t, rng)
        self._draw_horizon(screen, x, y, w, h, cfg, rng)
        self._draw_ground(screen, x, y, w, h, cfg)
        self._draw_mist(screen, x, y, w, h, cfg, t, rng)
        self._draw_particles(screen, x, y, w, h, cfg, t, rng)

        # Boss战额外效果
        if is_boss:
            self._draw_boss_aura(screen, x, y, w, h, accent, t)

        # 敌人剪影
        self._draw_enemy_silhouette(screen, x, y, w, h, enemy_name, is_boss, t)

    def _draw_boss_aura(self, screen, x, y, w, h, accent, t):
        """Boss气场——脉冲光环。"""
        pulse = 0.5 + 0.5 * abs(math.sin(t * 2.5))
        cx = x + w // 2
        cy = y + h // 3
        for i in range(3):
            radius = 60 + i * 30 + int(pulse * 15)
            alpha = int((1 - i * 0.3) * 25 * pulse)
            aura_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (*accent, alpha),
                             (radius + 2, radius + 2), radius, 2)
            screen.blit(aura_surf, (cx - radius - 2, cy - radius - 2))

    def _draw_enemy_silhouette(self, screen, x, y, w, h, enemy_name: str, is_boss: bool, t: float):
        """绘制敌人剪影——根据名称生成不同形状。"""
        cx = x + w // 3
        gy = y + h * 3 // 5

        # 基础剪影颜色
        if is_boss:
            color = (25, 10, 20)
            eye_color = (255, 30, 30)
        else:
            color = (20, 15, 28)
            eye_color = (200, 160, 40)

        # 根据敌人类型选择剪影形状
        if "龙" in enemy_name or "dragon" in enemy_name.lower():
            self._draw_dragon_silhouette(screen, cx, gy, color, eye_color, t)
        elif "树" in enemy_name or "lord" in enemy_name.lower():
            self._draw_treant_silhouette(screen, cx, gy, color, eye_color, t)
        elif "神" in enemy_name or "god" in enemy_name.lower():
            self._draw_deity_silhouette(screen, cx, gy, color, eye_color, t)
        elif "领主" in enemy_name:
            self._draw_knight_silhouette(screen, cx, gy, color, eye_color, t)
        elif "游魂" in enemy_name or "spirit" in enemy_name.lower():
            self._draw_spirit_silhouette(screen, cx, gy, color, eye_color, t)
        elif "狼" in enemy_name or "wolf" in enemy_name.lower():
            self._draw_wolf_silhouette(screen, cx, gy, color, eye_color, t)
        else:
            self._draw_generic_silhouette(screen, cx, gy, color, eye_color, t)

    def _draw_dragon_silhouette(self, screen, cx, gy, color, eye_color, t):
        """龙形剪影——翼展+长颈。"""
        # 身体
        body_w, body_h = 60, 35
        pygame.draw.ellipse(screen, color, (cx - body_w // 2, gy - body_h - 15, body_w, body_h))
        # 颈部
        neck_h = 50
        pygame.draw.line(screen, color, (cx + 10, gy - body_h - 10), (cx + 25, gy - body_h - neck_h), 10)
        # 头部
        head_r = 15
        pygame.draw.circle(screen, color, (cx + 30, gy - body_h - neck_h - 5), head_r)
        # 翅膀
        wing_span = 70
        wing_y = gy - body_h
        l_wing = [(cx - 5, wing_y), (cx - wing_span, wing_y - 25), (cx - wing_span + 20, wing_y + 10)]
        r_wing = [(cx + 5, wing_y), (cx + wing_span, wing_y - 25), (cx + wing_span - 20, wing_y + 10)]
        for wing in [l_wing, r_wing]:
            pygame.draw.polygon(screen, color, wing)
        # 眼睛
        pulse = 0.5 + 0.5 * abs(math.sin(t * 3.0))
        eye_r = 3
        alpha = int(pulse * 200)
        eye_surf = pygame.Surface((eye_r * 4, eye_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(eye_surf, (*eye_color, alpha), (eye_r * 2, eye_r * 2), eye_r)
        screen.blit(eye_surf, (cx + 33, gy - body_h - neck_h - 8))

    def _draw_treant_silhouette(self, screen, cx, gy, color, eye_color, t):
        """树灵剪影——粗壮树干+枝蔓。"""
        # 树干
        trunk_w, trunk_h = 25, 80
        pygame.draw.rect(screen, color, (cx - trunk_w // 2, gy - trunk_h, trunk_w, trunk_h))
        # 树冠
        crown_r = 40
        pygame.draw.ellipse(screen, color, (cx - crown_r, gy - trunk_h - 20, crown_r * 2, crown_r))
        pygame.draw.ellipse(screen, color, (cx - 20, gy - trunk_h - 35, 45, 40))
        pygame.draw.ellipse(screen, color, (cx + 5, gy - trunk_h - 30, 40, 35))
        # 枝蔓
        for angle in [-0.8, 0.6, -0.3]:
            bx = cx + int(30 * math.cos(angle))
            by = gy - trunk_h + 15
            ex = bx + int(40 * math.cos(angle))
            ey = by - 30
            pygame.draw.line(screen, color, (bx, by), (ex, ey), 4)
        # 眼睛（树洞亮光）
        pulse = 0.5 + 0.5 * abs(math.sin(t * 1.8))
        eye_alpha = int(pulse * 150)
        eye_surf = pygame.Surface((16, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(eye_surf, (*eye_color, eye_alpha), (0, 0, 16, 12))
        screen.blit(eye_surf, (cx - 8, gy - trunk_h + 15))

    def _draw_deity_silhouette(self, screen, cx, gy, color, eye_color, t):
        """神祇剪影——高大漂浮，光环。"""
        # 身躯
        body_h = 90
        pygame.draw.line(screen, color, (cx, gy), (cx, gy - body_h), 12)
        # 头部
        head_r = 14
        pygame.draw.circle(screen, color, (cx, gy - body_h - 8), head_r)
        # 悬浮效果——轻微上下
        float_offset = int(math.sin(t * 1.2) * 5)
        # 光环
        halo_r = 35 + int(abs(math.sin(t * 2.0)) * 5)
        halo_alpha = int(40 + 25 * abs(math.sin(t * 2.0)))
        halo_surf = pygame.Surface((halo_r * 2 + 4, halo_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (*eye_color, halo_alpha),
                         (halo_r + 2, halo_r + 2), halo_r, 2)
        screen.blit(halo_surf, (cx - halo_r - 2, gy - body_h - halo_r + float_offset))
        # 散开的手臂
        for angle in [-1.0, 1.0]:
            ax = cx + int(50 * math.cos(angle))
            ay = gy - body_h + 30 + float_offset
            pygame.draw.line(screen, color, (cx, gy - body_h + 20 + float_offset), (ax, ay), 5)

    def _draw_knight_silhouette(self, screen, cx, gy, color, eye_color, t):
        """骑士剪影——铠甲轮廓+剑。"""
        body_h = 65
        # 腿
        for offset in [-10, 10]:
            pygame.draw.line(screen, color, (cx + offset, gy), (cx + offset // 2, gy - 25), 7)
        # 身体
        pygame.draw.rect(screen, color, (cx - 15, gy - 55, 30, 35), border_radius=4)
        # 头部
        pygame.draw.circle(screen, color, (cx, gy - 60), 12)
        # 头盔缝隙亮光
        pulse = 0.5 + 0.5 * abs(math.sin(t * 2.5))
        eye_alpha = int(pulse * 180)
        eye_surf = pygame.Surface((16, 3), pygame.SRCALPHA)
        pygame.draw.line(eye_surf, (*eye_color, eye_alpha), (2, 1), (14, 1), 3)
        screen.blit(eye_surf, (cx - 8, gy - 62))
        # 剑
        sword_h = 40
        pygame.draw.line(screen, (80, 70, 100), (cx + 20, gy - 50), (cx + 35, gy - 50 - sword_h), 4)
        # 剑柄辉光
        glow_alpha = int(30 + 25 * pulse)
        glow_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*eye_color, glow_alpha), (5, 5), 5)
        screen.blit(glow_surf, (cx + 30, gy - 52))

    def _draw_spirit_silhouette(self, screen, cx, gy, color, eye_color, t):
        """游魂剪影——飘浮、扭曲。"""
        wave = math.sin(t * 2.0) * 8
        # 上半身
        pts = []
        for i in range(6):
            py = gy - i * 12
            px = cx + int(math.sin(i * 0.7 + t * 1.5) * (8 - i))
            pts.append((px, py))
        if len(pts) >= 2:
            for i in range(len(pts) - 1):
                pygame.draw.line(screen, color, pts[i], pts[i + 1], max(8 - i, 3))
        # 头部
        pygame.draw.circle(screen, color, (cx, gy - 70), 10)
        # 幽灵眼
        for ex in [-4, 4]:
            alpha = int(180 * (0.6 + 0.4 * abs(math.sin(t * 3.0))))
            eye_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(eye_surf, (*eye_color, alpha), (3, 3), 3)
            screen.blit(eye_surf, (cx + ex - 3, gy - 72))

    def _draw_wolf_silhouette(self, screen, cx, gy, color, eye_color, t):
        """狼形剪影。"""
        # 身体
        pygame.draw.ellipse(screen, color, (cx - 20, gy - 25, 45, 20))
        # 头部
        pygame.draw.circle(screen, color, (cx + 20, gy - 28), 12)
        # 耳朵
        for ex in [3, 10]:
            pygame.draw.polygon(screen, color, [(cx + 15 + ex, gy - 38), (cx + 18 + ex, gy - 48), (cx + 22 + ex, gy - 38)])
        # 腿
        for lx in [-12, -2, 12]:
            pygame.draw.line(screen, color, (cx + lx, gy - 12), (cx + lx, gy + 5), 5)
        # 尾巴
        pygame.draw.line(screen, color, (cx - 22, gy - 18), (cx - 35, gy - 30), 3)
        # 眼睛
        pulse = 0.5 + 0.5 * abs(math.sin(t * 3.5))
        alpha = int(pulse * 200)
        eye_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
        pygame.draw.circle(eye_surf, (*eye_color, alpha), (2, 2), 2)
        screen.blit(eye_surf, (cx + 24, gy - 32))

    def _draw_generic_silhouette(self, screen, cx, gy, color, eye_color, t):
        """通用人形剪影。"""
        # 身体
        pygame.draw.rect(screen, color, (cx - 10, gy - 35, 20, 25), border_radius=3)
        # 头
        pygame.draw.circle(screen, color, (cx, gy - 40), 10)
        # 眼睛
        pulse = 0.5 + 0.5 * abs(math.sin(t * 2.5))
        alpha = int(pulse * 180)
        for ex in [-3, 3]:
            eye_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
            pygame.draw.circle(eye_surf, (*eye_color, alpha), (2, 2), 2)
            screen.blit(eye_surf, (cx + ex - 2, gy - 42))

    # ═══════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════

    def _draw_polygon_aa(self, screen, points, color):
        """绘制多边形（带简单抗锯齿——画两层）。"""
        pygame.draw.polygon(screen, color, points)
        # 稍大一点的半透明层模拟AA
        aa_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        expanded = []
        cx = sum(p[0] for p in points) / max(1, len(points))
        cy = sum(p[1] for p in points) / max(1, len(points))
        for px, py in points:
            dx = px - cx
            dy = py - cy
            expanded.append((px + dx * 0.02, py + dy * 0.02))
        pygame.draw.polygon(aa_surf, (*color, 40), expanded)
        screen.blit(aa_surf, (0, 0))

    @staticmethod
    def scene_for_chapter(chapter_id: int) -> str:
        return CHAPTER_SCENES.get(chapter_id, "dark_forest")

    @staticmethod
    def scene_for_boss(enemy_name: str) -> str:
        """根据Boss名返回场景。"""
        if "神" in enemy_name:
            return "final_chamber"
        if "龙" in enemy_name:
            return "corrupted_castle"
        if "树" in enemy_name:
            return "dark_forest"
        if "领主" in enemy_name:
            return "corrupted_castle"
        return "corrupted_castle"
