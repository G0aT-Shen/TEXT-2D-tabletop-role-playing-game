"""第三章: 深渊觉醒 — 对抗暗黑势力的军队，做出关键抉择."""

from ..event import Event, EventType, Choice
from ..chapter import Chapter


def get_chapter3() -> Chapter:
    events = [
        # ===== 事件0: 深渊荒原 =====
        Event(
            event_id="c3_train",
            title="🌑 深渊荒原",
            description=(
                "幽灵列车停靠在一片荒芜的平原边缘。\n\n"
                "与之前的森林不同，这里寸草不生，大地龟裂，岩浆在裂缝中流淌。\n"
                "远处可以看到一座由黑铁铸成的巨大堡垒——深渊军团的要塞。\n"
                "无数暗影生物在平原上列队行进，仿佛在为某种大战做准备。\n\n"
                "列车上的符文突然亮起——一段新的信息浮现出来：\n"
                "「第三块碎片藏在深渊领主的王座之下。但小心——\n"
                "他早已知道你会来。这不是伏击，而是一场盛大的邀请。」\n\n"
                "前方有两条路通向要塞：\n"
                "一条是穿越军团营地的正面路线——危险但能收集情报；\n"
                "另一条是通过荒原地底的古老隧道——隐蔽但充满未知。"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="正面穿越军团营地（战斗+情报）",
                    result_text="你决定光明正大地面对敌人。",
                    trigger_combat=True, combat_enemy="night_reaver",
                    xp_reward=40,
                ),
                Choice(
                    text="走地底隧道（DEX检定 DC=14）",
                    result_text="你悄悄潜入古老的地底隧道。",
                    check_type="dex", dc=12,
                    success_text="隧道虽然阴暗逼仄，但确实安全地绕过了军团营地。你在隧道中发现了古代文明留下的壁画，描绘着光明与黑暗的战争——绝夜之神曾经也是光明的守护者，因为某种背叛才堕入黑暗。",
                    failure_text="隧道中布满了塌方和陷阱，你磕磕绊绊地前进，消耗了大量体力。HP -8。",
                    critical_success_text="你在隧道中如鱼得水！不仅完美避开了所有陷阱，还发现了一座古代军械库——里面的武器虽然古老，但依然可以使用。你获得了一把「破魔之弩」和五支附魔箭矢。",
                    critical_failure_text="隧道发生了大塌方！你被埋在碎石之下，费了好大力气才爬出来。HP -18，并且在接下来的战斗中STR-2。",
                    hp_change=-18,
                    xp_reward=45,
                    item_reward="破魔之弩",
                ),
            ],
        ),

        # ===== 事件1: 深渊军团 =====
        Event(
            event_id="c3_army",
            title="⚔️ 深渊军团",
            description=(
                "你接近了深渊要塞。\n\n"
                "要塞前的广场上集结着数千暗影生物——暗影狼、黑暗游魂、堕落骑士。\n"
                "一位身穿漆黑重甲的将领站在高台上，用深渊语嘶吼着战前动员。\n\n"
                "「人类已经发现了我们的计划！绝夜之神有令——\n"
                "在他们聚齐碎片之前，彻底消灭所有被选中者！」\n\n"
                "你注意到要塞侧面有一扇不起眼的小门，似乎是后勤通道。\n"
                "但直接杀入正面，也许能斩首这支军团的指挥官。"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="潜入要塞后勤通道（DEX检定 DC=15）",
                    result_text="你绕到要塞侧面，尝试从后勤通道潜入。",
                    check_type="dex", dc=13,
                    success_text="你成功潜入了要塞内部！避开了正面的大军，直接深入了要塞的核心区域。一路上你看到了深渊军团的后勤补给线和武器库——如果破坏了这些，外面的军团将不战自溃。",
                    failure_text="后勤通道有重兵把守，你没能成功潜入。",
                    critical_success_text="你以不可思议的潜入技巧绕过了所有守卫！不仅成功深入核心，还顺便破坏了深渊军团的武器库和粮仓。外面的军团陷入了混乱——这为你的最终战斗赢得了巨大的优势！",
                    critical_failure_text="你触发了要塞的警报系统！所有的深渊守卫都被惊动了。你被迫一路杀出重围，负伤累累。HP -20。",
                    hp_change=-20,
                    xp_reward=50,
                    flags_set={"infiltrated": True},
                ),
                Choice(
                    text="正面突袭，斩首指挥官（STR检定 DC=16）",
                    result_text="你怒吼一声，直接冲向军团指挥官！",
                    check_type="str", dc=14,
                    success_text="你在乱军中杀出一条血路，直取指挥官！虽然没能歼灭全部军团，但指挥官的死亡让深渊军团陷入了群龙无首的混乱。",
                    failure_text="军团的数量远超你的想象，你被重重包围，难以接近指挥官。",
                    critical_success_text="你如同战神降临！一刀斩杀指挥官后，军团的士气崩溃了。暗影生物们四散奔逃——你以一己之力击溃了整支深渊军团！",
                    critical_failure_text="你被军团重重包围，虽然奋力杀敌，但寡不敌众。HP -25，且被俘获至要塞地牢。",
                    hp_change=-25,
                    xp_reward=50,
                ),
            ],
        ),

        # ===== 事件2: 黑暗祭坛 =====
        Event(
            event_id="c3_altar",
            title="🕯️ 黑暗祭坛",
            description=(
                "你深入要塞内部，来到了一处巨大的地下空间。\n\n"
                "这里矗立着一座由黑曜石建成的祭坛，四周燃烧着幽蓝色的火焰。\n"
                "祭坛中央悬浮着一块红色的晶石——第三块晨曦碎片！\n\n"
                "然而祭坛周围站着四位深渊祭司，他们正在举行某种召唤仪式。\n"
                "「深渊领主即将降临——只要完成这个仪式……」\n\n"
                "你知道必须打断这个仪式，否则深渊领主将以完全体降临，\n"
                "那将是你无法对抗的力量。"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="用智谋破坏仪式（INT检定 DC=15）",
                    result_text="你仔细观察仪式的结构，寻找破解之法。",
                    check_type="int", dc=13,
                    success_text="你发现了仪式的关键节点——四角的幽蓝火焰必须同时熄灭。你利用要塞中的反射镜巧妙地将月光引导进来，同时扑灭了所有火焰。仪式中断，深渊祭司们被黑暗能量反噬，化为灰烬。",
                    failure_text="仪式的结构太过复杂，你没能找到破解的方法。",
                    critical_success_text="你不仅打断了仪式，还将仪式能量逆转！黑暗能量反噬到深渊领主身上，削弱了它大半的力量。当你面对深渊领主时，它将不再是完全体——这场胜利从此刻就已经注定！",
                    critical_failure_text="你在尝试破坏仪式时被黑暗能量击中！那股力量是如此强大，MP -20，并且你被暂时传送到了虚空之中，需要找到回来的路。",
                    mp_change=-20,
                    xp_reward=60,
                    flags_set={"ritual_broken": True},
                ),
                Choice(
                    text="直接攻击深渊祭司（战斗）",
                    result_text="你没有时间思考了，直接冲向祭坛！",
                    trigger_combat=True, combat_enemy="necromancer",
                    xp_reward=55,
                ),
            ],
        ),

        # ===== 事件3: 深渊领主（第三章Boss） =====
        Event(
            event_id="c3_boss",
            title="👑 深渊领主",
            description=(
                "大地震颤，祭坛崩裂。\n\n"
                "从裂缝中升起的是一位身高三米的恐怖存在——深渊领主。\n"
                "他的铠甲融入了他烧焦的皮肤，黑色火焰在他周身燃烧。\n"
                "他手持一把燃烧着不灭黑焰的巨剑，每一步都让要塞为之颤抖。\n\n"
                "「你就是那个收集碎片的人？」\n"
                "「有趣。我已经很久没有遇到值得一战的对手了。」\n"
                "深渊领主举起巨剑，黑暗火焰在空中凝聚。\n"
                "「来，让我看看你是否有资格面对绝夜之神！」"
            ),
            event_type=EventType.BOSS,
            choices=[
                Choice(
                    text="⚔️ 迎战深渊领主！",
                    result_text="你握紧武器，直面这位深渊军团的统帅。赢了这一战，第三块晨曦碎片就是你的！",
                    trigger_combat=True, combat_enemy="abyssal_lord",
                    xp_reward=500,
                    flags_set={"chapter3_complete": True},
                ),
            ],
            auto_next="c3_end",
        ),

        # ===== 事件4: 第三章结束 =====
        Event(
            event_id="c3_end",
            title="🌅 第三章 · 完",
            description=(
                "深渊领主单膝跪地，黑色火焰逐渐熄灭。\n"
                "「你……确实有资格。」他竟露出了一丝笑容。\n"
                "「绝夜之神曾经也是像你一样的英雄。是什么让他堕落……」\n"
                "「是孤独。永恒的孤独。」\n\n"
                "深渊领主化为灰烬，第三块红色晨曦碎片落入你的手中。\n"
                "三块碎片的共鸣让周围的黑暗退散了许多。\n\n"
                "要塞的墙壁轰然倒塌，露出了一条通往最高处的阶梯——\n"
                "绝夜神殿。\n\n"
                "幽灵列车无法抵达那里，你必须徒步攀登。\n"
                "最远的地方，最后的战斗，就在前方。\n\n"
                "【第三章「深渊觉醒」· 完】\n"
                "最终章：第四章「绝夜终章」"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="带着三块碎片，走向最终的决战",
                    result_text="你将三块晨曦碎片合在一起——它们发出的光芒照亮了前方的阶梯。这是一条向上的路，通往这趟旅程的终点。",
                    xp_reward=120,
                ),
            ],
        ),
    ]

    return Chapter(
        chapter_id=3,
        title="第三章",
        subtitle="深渊觉醒",
        intro_text=(
            "你已手握两块晨曦碎片，黑暗的力量感受到了威胁。\n"
            "深渊军团正在集结，深渊领主正等待着你的到来。\n"
            "这一章，你将面对真正的恶魔大军。\n"
            "在深渊要塞的阴影之下，你能感受到第三块碎片的召唤。\n\n"
            "第三章：深渊觉醒 —— 考验你的勇气与智慧。"
        ),
        events=events,
    )
