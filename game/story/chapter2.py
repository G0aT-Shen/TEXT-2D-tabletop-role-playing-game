"""第二章: 幽影迷途 — 深入暗影森林，发现古老诅咒的真相."""

from ..event import Event, EventType, Choice
from ..chapter import Chapter


def get_chapter2() -> Chapter:
    events = [
        # ===== 事件0: 幽灵列车 =====
        Event(
            event_id="c2_train",
            title="👻 幽灵列车",
            description=(
                "幽灵列车在无尽的黑暗中缓缓行驶。\n\n"
                "车厢内部与之前的曙光号截然不同——墙壁上覆盖着古老的符文，\n"
                "散发着微弱的蓝色荧光。座位空无一人，却有低语在耳边回荡。\n\n"
                "你注意到车厢的公告板上钉着一张泛黄的报纸：\n"
                "「黑暗瘟疫蔓延——影月森林的居民全部失踪」\n"
                "日期是……三百年前。\n\n"
                "列车突然减速，前方出现了一个被浓密迷雾笼罩的站台。\n"
                "站台上立着一块字迹斑驳的木牌：「影月森林站」。\n"
                "看来这就是你们必须下车的地方。"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="研读车厢上的古老符文（INT检定 DC=13）",
                    result_text="你仔细研究车厢上的神秘符文。",
                    check_type="int", dc=11,
                    success_text="你解读出部分符文的内容：它们描述了一场古老的仪式——「绝夜仪式」。某个强大的存在试图用这个仪式将整个世界拖入永恒的黑夜。符文还提到了一件关键物品——「晨曦碎片」，据说是对抗绝夜的唯一希望。",
                    failure_text="符文太过古老，你无法完全解读，只能零星认出几个词：「黑暗」「仪式」「代价」。",
                    critical_success_text="你的智慧洞察了符文的全貌！这不仅是一场黑暗仪式，更是一个循环诅咒。每隔三百年，会有一批「被选中者」被拉入绝夜之境。要打破诅咒，必须在第四个节点——「绝夜神殿」——使用四块晨曦碎片。你成功记忆了全部符文内容！",
                    critical_failure_text="你错误解读了符文，以为只要破坏列车就能回去。你冲动之下破坏了车厢的符文阵列，引发了黑暗能量的反噬！HP -15。",
                    hp_change=-15,
                    xp_reward=30,
                    flags_set={"understood_ritual": True},
                ),
                Choice(
                    text="探索幽灵列车的其他车厢（DEX检定 DC=12）",
                    result_text="你悄悄穿过连接处，探索这辆神秘的列车。",
                    check_type="dex", dc=10,
                    success_text="你在第三节车厢发现了前一批「被选中者」留下的笔记。笔记记录了他们在森林中的遭遇，以及一张标注了安全路径的地图。地图上标注了一处名为「月光避难所」的地点。",
                    failure_text="车厢门锁住了，你无法进入。",
                    critical_success_text="你找到了一个被遗忘的乘客日记，作者是一位三百年前的圣职者。日记详细记载了对抗黑暗的方法、森林中的怪物弱点，以及一个至关重要的秘密——「绝夜之神」害怕「光明记忆」！此外，日记夹层中有一瓶大治疗药水。",
                    critical_failure_text="你触发了一个古老的陷阱！暗影能量从地板涌出，将你短暂地拉入了噩梦幻境。HP -10，并受到惊吓。",
                    hp_change=-10,
                    xp_reward=30,
                    item_reward="大治疗药水",
                ),
                Choice(
                    text="在站台上寻找线索（WIS检定 DC=11）",
                    result_text="你走下幽灵列车，在迷雾笼罩的站台上搜索。",
                    check_type="wis", dc=9,
                    success_text="站台上残留着打斗的痕迹和早已干涸的黑色血迹。你发现了一枚徽章，上面刻着太阳的图案——这是这个世界曾经有光明的证明。徽章上还刻着一行小字：「晨曦不灭」。",
                    failure_text="迷雾太浓，你找不到更多有用的线索。",
                    critical_success_text="你的感知超越了常人！你不仅找到了徽章，还感应到了森林中残存的「光明记忆」——这些记忆碎片指引你找到了一条隐藏的小路，直接通往森林的核心区域。",
                    critical_failure_text="迷雾中隐藏着陷阱！你一脚踩空，掉进了捕兽夹。HP -8，DEX暂时-2。",
                    hp_change=-8,
                    xp_reward=20,
                    item_reward="晨曦徽章",
                ),
            ],
        ),

        # ===== 事件1: 迷雾森林 =====
        Event(
            event_id="c2_mist_forest",
            title="🌫️ 迷雾森林",
            description=(
                "你踏入影月森林，浓密的迷雾让人几乎看不清三步之外的景象。\n\n"
                "树木的枝干扭曲如挣扎的人形，空气中弥漫着腐烂和某种甜腻气味。\n"
                "脚下的泥土松软，每踩一步都像要被大地吞没。\n\n"
                "前方传来两种声音：\n"
                "左侧有微弱的呼救声——似乎有人被困；\n"
                "右侧传来低沉的诵经声——像是什么仪式正在进行。"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="去查看呼救声（可能是幸存者）",
                    result_text="你循着呼救声小心翼翼地前进。",
                    trigger_combat=True, combat_enemy="demon_imp",
                    xp_reward=35,
                    flags_set={"rescued_survivor": True},
                ),
                Choice(
                    text="去探查诵经声（INT检定 DC=14）",
                    result_text="你被神秘的诵经声吸引，决定前去一探究竟。",
                    check_type="int", dc=12,
                    success_text="你发现了一群身穿黑袍的邪教徒正在进行献祭仪式。你从他们的祷文中了解到——他们正在为「绝夜之神」收集「光明的碎片」。仪式中心摆放着一块发光的晶石——那就是晨曦碎片之一！",
                    failure_text="你没能听清他们在说什么。而且你靠得太近，引起了他们的警觉。",
                    critical_success_text="你完全破解了邪教徒的祷文！他们来自一个叫「暗夜之拥」的组织。你不仅搞清楚了仪式的运作方式，还趁他们不备，用智谋将那块晨曦碎片偷到了手！",
                    critical_failure_text="你不慎暴露了行踪！邪教徒们集体向你发起了精神攻击，黑暗能量侵蚀了你的意识。HP -12，MP -10。",
                    hp_change=-12,
                    mp_change=-10,
                    xp_reward=40,
                    item_reward="晨曦碎片(蓝)",
                    flags_set={"found_crystal": True},
                ),
            ],
        ),

        # ===== 事件2: 月光避难所 =====
        Event(
            event_id="c2_sanctuary",
            title="🏕️ 月光避难所",
            description=(
                "穿越迷雾后，你发现了一处被月光笼罩的空地。\n\n"
                "这里似乎不受黑暗的侵蚀——树木恢复了正常的绿色，\n"
                "地面上生长着散发微光的银色花朵。\n"
                "空地中央有一座石制祭坛，周围散落着篝火的余烬。\n\n"
                "「有人在吗？」一个苍老的声音从阴影中传来。\n"
                "一位身披兽皮的老猎人走了出来：「你们……也是被那辆列车带来的？」\n"
                "「我在这里已经独自生活了三十年。这里叫月光避难所，是这片森林中唯一安全的地方。」"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="向老猎人请教森林的秘密（CHA检定 DC=12）",
                    result_text="你恭敬地向老猎人请教。",
                    check_type="cha", dc=10,
                    success_text="老猎人被你诚恳的态度打动。他告诉你：「这片森林的中心有一棵腐化树灵——它是黑暗力量在这片土地的代理人。打败它，你就能找到第二块晨曦碎片。」他还送给你一些他自制的狩猎工具。",
                    failure_text="老猎人似乎不愿多谈：「有些事，知道得越多越危险。」",
                    critical_success_text="你的真诚触动了老猎人内心最深处！他不仅倾囊相授，还决定亲自带你前往森林中心的捷径。他还透露：「我年轻时也曾是『被选中者』，但我没有勇气继续前进……孩子，替我完成这趟旅程。」",
                    critical_failure_text="你的提问方式激怒了老猎人。他认定你是黑暗派来的探子，举起猎枪对准了你。虽然最终误会解除，但他什么也不愿意告诉你了。",
                    xp_reward=30,
                    item_reward="狩猎工具",
                    flags_set={"hunter_help": True},
                ),
                Choice(
                    text="在月光祭坛前冥想恢复（WIS检定 DC=10）",
                    result_text="你在银色的月光下闭上眼睛，感受这片圣地的力量。",
                    check_type="wis", dc=8,
                    success_text="月光的力量抚慰了你的身心。HP和MP完全恢复！你还感知到了森林中隐藏的危险——腐化树灵的具体位置已经烙印在你的脑海中。",
                    failure_text="你的心绪不宁，无法完全静下心来。只恢复了部分HP。",
                    critical_success_text="你与月光祭坛产生了深度共鸣！一道银色光柱从天而降，不仅完全治愈了你的伤，还赐予了你「月光的祝福」——在接下来的战斗中，所有检定获得+2加值。HP/MP全恢复，获得永久BUFF。",
                    critical_failure_text="你在冥想时被黑暗力量入侵了意识！噩梦般的幻象充斥你的脑海。MP -15，且无法获得休息效果。",
                    mp_change=-15,
                    xp_reward=20,
                ),
            ],
        ),

        # ===== 事件2b: 关键抉择 — 试炼 vs 突破 =====
        Event(
            event_id="c2_crossroad",
            title="⚡ 抉择时刻",
            description=(
                "离开月光避难所后，老猎人指出了两条通往森林核心的道路。\n\n"
                "「左边是『森林之灵』设下的试炼之路。通过考验者将获得灵体的祝福，\n"
                "但试炼本身并不轻松——它考验的是你的智慧与判断力。」\n\n"
                "「右边是直接穿过腐化区域的捷径。那里充满了被感染的生物，\n"
                "但如果你足够强大，可以一路杀过去——能省下不少时间。」\n\n"
                "「选择权在你手中。记住——道路本身就决定了你是谁。」"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="🌿 接受森林之灵的试炼（WIS检定 DC=14）",
                    result_text="你选择尊重这片古老森林的意志，步入试炼之路。",
                    check_type="wis", dc=12,
                    success_text="森林之灵认可了你的敬意。三道试炼你一一通过：\n1. 识别毒果与解药\n2. 解读古树之语\n3. 在迷宫中找到核心\n\n作为回报，森林之灵降下了祝福——你的感知力永久提升了。",
                    failure_text="部分试炼你没能通过，但森林之灵依然尊重你的努力。你获得了部分祝福。",
                    critical_success_text="你以惊人的智慧完成了全部试炼！森林之灵欣喜若狂，不仅赐予你「自然之息」——每回合治疗HP+5的永久祝福，还赠送你一枚蕴含远古力量的「林魂护符」。",
                    critical_failure_text="你在试炼中严重失误，触怒了森林之灵！藤蔓从四面八方袭来将你捆绑。HP -10，你被迫返回原路重新开始。",
                    hp_change=-10,
                    xp_reward=40,
                    faction_reputation={"OBSERVER": 30, "DAWN": 15},
                    flags_set={"chose_trial": True, "forest_blessing": True},
                ),
                Choice(
                    text="⚔️ 强行突破腐化区域（触发连续战斗）",
                    result_text="你选择最直接的路径——用力量碾压一切阻碍。",
                    trigger_combat=True, combat_enemy="void_walker",
                    xp_reward=45,
                    faction_reputation={"SHADOW": 30},
                    flags_set={"chose_breakthrough": True},
                ),
            ],
        ),

        # ===== 事件2c: 分支 — 试炼线 =====
        Event(
            event_id="c2_trial_path",
            title="🌿 森林之灵的祝福",
            description=(
                "你走出试炼迷宫时，一个由枝叶和月光构成的灵体浮现在你面前。\n\n"
                "「凡人，你证明了你的智慧与敬意。」\n"
                "「这片森林已经三百年没人能通过全部试炼了。」\n\n"
                "灵体一挥手指向远方：「腐化树灵的弱点是火焰与圣光。\n"
                "但小心——它的根须覆盖了整片森林，每一步都可能触发。」\n\n"
                "「带着我的祝福，去终结黑暗吧。」"
            ),
            event_type=EventType.STORY,
            required_flags={"chose_trial": True},
            choices=[
                Choice(
                    text="感谢森林之灵，准备最终的战斗",
                    result_text="你感受到体内的自然之力。腐化树灵——你的下一个对手——已经近在眼前。",
                    xp_reward=15,
                    item_reward="急救包",
                    faction_reputation={"DAWN": 10},
                ),
            ],
        ),

        # ===== 事件2d: 分支 — 突破线 =====
        Event(
            event_id="c2_breakthrough_path",
            title="⚔️ 杀出重围",
            description=(
                "击败虚空行者后，你在腐化区域的深处发现了一个暗影生物的营地。\n"
                "这里的怪物显然在为腐化树灵输送能量——从周围吸取来的生命精华。\n\n"
                "营地中央有一个仪式祭坛，上面摆放着被污染的水晶。\n"
                "如果摧毁这些水晶，一定能削弱树灵的力量。\n\n"
                "但祭坛周围还有大量守卫……"
            ),
            event_type=EventType.CHOICE,
            required_flags={"chose_breakthrough": True},
            choices=[
                Choice(
                    text="💪 杀入祭坛，摧毁所有水晶（战斗）",
                    result_text="你提起武器，杀入敌阵！",
                    trigger_combat=True, combat_enemy="corrupted_knight",
                    xp_reward=50,
                    gold_reward=60,
                    faction_reputation={"SHADOW": 10},
                    flags_set={"weakened_boss": True},
                ),
                Choice(
                    text="🔮 用法力远程引爆水晶（INT检定 DC=13）",
                    result_text="你凝聚魔力，远程引爆祭坛上的被污染水晶。",
                    check_type="int", dc=11,
                    success_text="水晶在魔力共振下逐一碎裂！远处的腐化树灵发出痛苦的嚎叫——它的力量被削弱了。",
                    failure_text="你的魔力不够精准，只摧毁了两块水晶。",
                    critical_success_text="你以华丽的奥术技巧将所有水晶同时引爆！爆炸的连锁反应还清除了整个营地的大部分怪物。腐化树灵被严重削弱。",
                    critical_failure_text="你错误地激发了水晶的能量！黑暗能量反噬，HP -8，MP -10。祭坛反而充能完毕。",
                    hp_change=-8,
                    mp_change=-10,
                    xp_reward=35,
                    faction_reputation={"OBSERVER": 10},
                    flags_set={"weakened_boss": True},
                ),
            ],
        ),

        # ===== 事件3: 腐化树灵（第二章Boss） =====
        Event(
            event_id="c2_boss",
            title="🌳 腐化树灵",
            description=(
                "你来到了森林的最深处。\n\n"
                "这里的树木全部扭曲缠绕在一起，形成了一个巨大的木质巨茧。\n"
                "地面震动——树茧缓缓裂开，一个由无数藤蔓和腐木组成的怪物显现出来。\n\n"
                "「凡人来此……献出你的生命之力……滋养这片森林……」\n"
                "腐化树灵的根系从大地中汲取黑暗能量，它的体型不断膨胀！\n\n"
                "树灵的中央嵌着一块发光的绿色晶石——那是第二块晨曦碎片！\n"
                "第二章的守护者，就站在你的面前。"
            ),
            event_type=EventType.BOSS,
            choices=[
                Choice(
                    text="⚔️ 击败腐化树灵，夺取晨曦碎片！",
                    result_text="你举起武器，迎向这头被黑暗腐蚀的远古树灵！这是第二章的最终战斗！",
                    trigger_combat=True, combat_enemy="forest_lord",
                    xp_reward=350,
                    flags_set={"chapter2_complete": True},
                ),
            ],
            auto_next="c2_end",
        ),

        # ===== 事件4: 第二章结束 =====
        Event(
            event_id="c2_end",
            title="🌅 第二章 · 完",
            description=(
                "腐化树灵化为漫天的绿色光点，消散在森林的微风中。\n"
                "你取下了那颗翠绿的晨曦碎片。\n\n"
                "随着树灵的净化，整片森林的迷雾开始消退。\n"
                "树木恢复了生机，银色的月光洒满了林间空地。\n\n"
                "老猎人站在远处向你挥手：「你做到了！前方有一处古老的传送阵，它会把你们带到下一站——深渊荒原。」\n"
                "「但要小心……深渊领主正在那里等着你。」\n\n"
                "远处，幽灵列车的汽笛声再次响起。\n"
                "这一次，你知道自己要去哪里。\n\n"
                "【第二章「幽影迷途」· 完】\n"
                "下一章：第三章「深渊觉醒」"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="带着两块晨曦碎片，继续前行",
                    result_text="你将翠绿的晨曦碎片收好，大步走向幽灵列车。两块碎片在你怀中散发着温暖的光芒——这是对抗黑暗的希望。",
                    xp_reward=80,
                ),
            ],
        ),
    ]

    return Chapter(
        chapter_id=2,
        title="第二章",
        subtitle="幽影迷途",
        intro_text=(
            "击败暗影巨龙后，幽灵列车载着你驶入更深的黑暗。\n"
            "空气中弥漫着更加浓重的不祥气息。\n"
            "你已经知道，自己并非偶然来到这里——\n"
            "你是「被选中者」，背负着打破绝夜诅咒的使命。\n\n"
            "第二章：幽影迷途 —— 影月森林的秘密等待着你。"
        ),
        events=events,
    )
