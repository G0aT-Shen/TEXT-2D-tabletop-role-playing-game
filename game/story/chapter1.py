"""第一章: 暗夜降临 — 列车误入黑暗领域，初遇妖魔."""

from ..event import Event, EventType, Choice
from ..chapter import Chapter


def get_chapter1() -> Chapter:
    events = [
        # ===== 事件0: 列车启程（序章） =====
        Event(
            event_id="c1_intro",
            title="🌅 黄昏启程",
            description=(
                "暮色笼罩大地，你登上了名为「曙光号」的蒸汽列车。\n\n"
                "列车的汽笛声划破黄昏的宁静，车轮在铁轨上有节奏地敲击着。\n"
                "车厢里弥漫着陈旧的皮革和木头的味道，乘客们各自沉默。\n\n"
                "你望向窗外，夕阳将天空染成一片血红——一种不祥的红色。\n"
                "列车员微笑着递来一杯热茶：「旅途愉快，我们将在黎明抵达终点。」\n\n"
                "然而，当列车穿越一条长长的隧道后，窗外的景色变了。\n"
                "天空不再有星辰，只有一轮诡异的暗紫色月亮悬挂天际。\n"
                "远处的大地上，隐约可见巨大的暗影在蠕动……"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="警惕地观察四周（WIS检定 DC=12）",
                    result_text="你察觉到空气中弥漫着不祥的气息，这里绝非正常的世界。",
                    check_type="wis", dc=10,
                    success_text="你的感知异常敏锐——你注意到车厢末端有个黑影一闪而过，似乎有什么东西潜入了列车。",
                    failure_text="你四处张望，但车厢内光线昏暗，难以看清什么。",
                    critical_success_text="你的灵感瞬间爆发！你不仅察觉到了潜入列车的妖魔，还感知到了这个世界的本质——这里是被「绝夜」吞噬的失落领域。你还发现车厢地板下藏着一瓶圣水。",
                    critical_failure_text="你过度紧张，反而产生了幻觉。一个乘客的面孔在你眼中扭曲成了恶魔——你惊叫出声，引起了全车人的恐慌。",
                    xp_reward=20,
                    item_reward="圣水",
                    flags_set={"intro_approach": "cautious"},
                ),
                Choice(
                    text="与其他乘客交谈收集信息（CHA检定 DC=10）",
                    result_text="你开始与周围的乘客攀谈，试图了解情况。",
                    check_type="cha", dc=8,
                    success_text="一位老者告诉你古老的传说：每隔百年，会有一辆列车驶入「绝夜之境」。能回到黎明的人，将获得改写命运的资格。但这辆列车从未有人真正离开过……",
                    failure_text="乘客们似乎都陷入了恐慌，没人愿意和你多说。",
                    critical_success_text="你的魅力感染了整节车厢！乘客们纷纷将他们的护身符和补给品交给你。老者甚至将自己的祖传怀表赠予你——据说它能指引迷途者找到回家的路。",
                    critical_failure_text="你的询问引起了恐慌！乘客们陷入了混乱的骚动，甚至有两人因为争夺行李架上的物品打了起来。列车员愤怒地将你视为骚乱的源头。",
                    xp_reward=20,
                    item_reward="祖传怀表",
                    flags_set={"intro_approach": "social"},
                ),
                Choice(
                    text="前往驾驶室查看情况（STR检定 DC=10）",
                    result_text="你决定直接前往列车前方，弄清到底发生了什么。",
                    check_type="str", dc=8,
                    success_text="你用力推开了因变形而卡住的车厢门，来到驾驶室。列车长已经失踪，仪表盘上显示列车正以不可思议的速度驶向未知的坐标。你紧急拉下了制动闸——但列车并未减速。",
                    failure_text="车厢门因撞击而变形，你用尽全力也无法推开。",
                    critical_success_text="你不仅强行进入了驾驶室，还发现了列车长的日志：「第13次穿越——我们被困在循环中。如果能找到『暗夜之心』，也许能打破这诅咒……」与此同时，你发现了藏在驾驶座下的急救包。",
                    critical_failure_text="你猛烈撞击车门，却被反弹回来，撞翻了身后的乘客。你的手臂在冲击中受伤。HP -5。",
                    hp_change=-5,
                    xp_reward=20,
                    item_reward="急救包",
                    flags_set={"intro_approach": "direct"},
                ),
            ],
        ),

        # ===== 事件1: 列车上的初战 =====
        Event(
            event_id="c1_first_fight",
            title="👹 列车上的暗影",
            description=(
                "列车突然剧烈震动，灯光全部熄灭。\n\n"
                "黑暗中传来刺耳的尖叫——有什么东西正在车厢中移动！\n"
                "当应急灯亮起时，你看到车厢末端出现了几道扭曲的黑影。\n"
                "它们从阴影中凝聚成形——是「暗影狼」！\n\n"
                "「这些是什么东西？！」有乘客惊恐地喊道。\n"
                "你意识到必须站出来保护这节车厢的乘客。"
            ),
            event_type=EventType.COMBAT,
            choices=[
                Choice(
                    text="⚔️ 挺身而出，迎战暗影狼！",
                    result_text="你拔出武器，挡在乘客们面前。暗影狼发出低沉嘶哑的咆哮，朝你扑来！",
                    trigger_combat=True, combat_enemy="shadow_wolf",
                    xp_reward=30,
                    flags_set={"first_battle": "won"},
                ),
                Choice(
                    text="迅速组织乘客们撤离到下一节车厢（DEX检定 DC=13）",
                    result_text="你选择优先保护无辜的乘客。",
                    check_type="dex", dc=11,
                    success_text="你灵活地引导乘客们有序撤离，成功将所有人转移到了安全的车厢。暗影狼不敢追入明亮的区域。",
                    failure_text="撤离过程中秩序混乱，一名乘客在推搡中摔倒受伤。你感到内疚。",
                    critical_success_text="你以惊人的速度和精准的判断，不仅撤离了所有乘客，还在撤离过程中利用车厢的折叠座椅设下了简易陷阱——暗影狼冲过来时被撞得七荤八素！",
                    critical_failure_text="恐慌导致撤离完全失控！有乘客被暗影狼抓伤，你也受到了牵连。HP -12。",
                    hp_change=-12,
                    xp_reward=15,
                ),
            ],
        ),

        # ===== 事件2: 列车残骸 =====
        Event(
            event_id="c1_wreck",
            title="🚂 脱轨",
            description=(
                "列车发出一声金属撕裂的巨响——前方轨道竟是断裂的！\n\n"
                "蒸汽列车脱轨冲出，在荒芜的黑色大地上滑行了数百米后才停下。\n"
                "车厢严重变形，但万幸的是大部分乘客幸存了下来。\n\n"
                "你爬出残骸，环顾四周：\n"
                "天空是永恒的深紫色，没有太阳也没有真正的星辰。\n"
                "前方是一片散发着幽光的黑色森林，远处隐约可见一座阴森的城堡。\n\n"
                "「看来我们被困在这里了……」一位幸存者叹息道。\n"
                "「传说中，只有穿越绝夜之境，才能找到返回的路。」"
            ),
            event_type=EventType.STORY,
            choices=[
                Choice(
                    text="搜寻列车残骸中的资源（INT检定 DC=12）",
                    result_text="你在扭曲的金属中找到了一些还能用的物资。",
                    check_type="int", dc=10,
                    success_text="你从残骸中找出了医疗用品、食物和一张残破的地图。地图上标注着一条蜿蜒穿越森林的小路，通向远处的城堡。",
                    failure_text="残骸中大部分物资已经损毁，你只找到了一些零碎的东西。",
                    critical_success_text="你在列车长的座位下发现了一个上锁的铁箱！用工具撬开后，里面有一本记录详细的「绝夜探险日志」、三瓶治疗药水，以及一把闪烁着微光的附魔匕首。",
                    critical_failure_text="你在翻找时引发了燃油泄漏！爆炸的冲击波将你掀飞，HP -15。",
                    hp_change=-15,
                    xp_reward=25,
                    item_reward="附魔匕首",
                    flags_set={"found_map": True},
                ),
                Choice(
                    text="安抚受伤的幸存者（CHA检定 DC=13）",
                    result_text="你用温和的话语平复众人的恐惧。",
                    check_type="cha", dc=11,
                    success_text="你的话语给了幸存者们希望。一位受伤的旅客主动站出来：「我知道一些关于这片森林的事，我的祖父曾经来过这里……」",
                    failure_text="有些人听不进安慰，陷入了歇斯底里。",
                    critical_success_text="你的演说仿佛带有魔力！幸存者们不仅冷静下来，还自发组织成了互助小组。一位老猎人拿出他私藏的狩猎长弓送给你，表示愿意与你并肩作战。",
                    critical_failure_text="你的安抚被误解为居高临下的怜悯。一名愤怒的乘客指责你是这一切的元凶，气氛变得剑拔弩张。",
                    xp_reward=25,
                ),
                Choice(
                    text="侦察周围环境（DEX检定 DC=11）",
                    result_text="你悄悄绕到列车周围，探查这片陌生的大地。",
                    check_type="dex", dc=9,
                    success_text="你发现列车脱轨并非意外——铁轨被人为破坏！附近地上还有巨大的爪印，通往森林方向。你还在不远处发现了一处隐蔽的洞穴，似乎可以暂时栖身。",
                    failure_text="四周一片荒芜，除了远处的森林和城堡，你看不到更多有用的信息。",
                    critical_success_text="你的侦察能力发挥到了极致！你不仅发现了人为破坏铁轨的痕迹，还追踪到了破坏者的行踪——一群向城堡方向撤退的暗影生物。更重要的是，你找到了一条隐藏的捷径。",
                    critical_failure_text="你在黑暗中迷失了方向，不慎跌入一处暗坑。等你爬出来时，浑身是伤，并且完全迷失了方位。HP -10。",
                    hp_change=-10,
                    xp_reward=25,
                ),
            ],
        ),

        # ===== 事件3: 关键抉择 — 拯救 vs 追击 =====
        Event(
            event_id="c1_crossroad",
            title="⚡ 抉择时刻",
            description=(
                "离开列车残骸后，你们沿着血迹斑斑的小径前进。\n\n"
                "前方传来两种声音——\n"
                "左边不远处，有微弱的呼救声，似乎有幸存者被困；\n"
                "而前方的森林深处，暗影狼的嚎叫声正在迅速远去……\n\n"
                "「我们必须做出选择。」你意识到时间紧迫。\n"
                "救助被困的人，还是追击逃跑的狼群——两者无法兼顾。\n"
                "在这绝夜之境中，每个选择都将改变未来的道路。"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="🆘 拯救被困的幸存者（CHA检定 DC=12）",
                    result_text="你选择不放弃任何生命，转身奔向呼救声的来源。",
                    check_type="cha", dc=10,
                    success_text="你成功找到了一个被困在倒下的树木下的商人。他感激涕零：「谢谢你！我叫马库斯，可以在列车上为你提供补给。这是我欠你的。」",
                    failure_text="你花了不少时间才找到被困者，他的腿受了伤，但总算还活着。",
                    critical_success_text="你不仅救下了马库斯，还发现他是一名经验丰富的探险家！他提供了珍贵的绝夜之境情报，并将自己珍藏的「晨曦徽章」赠送给你。\n\n马库斯承诺在后续旅程中为你提供折扣补给。",
                    critical_failure_text="在你犹豫的时间里，被困者的声音变得越来越微弱……等你赶到时，一具尸体已经冰冷。你心中的愧疚挥之不去。HP -5。",
                    hp_change=-5,
                    xp_reward=30,
                    item_reward="晨曦徽章",
                    faction_reputation={"DAWN": 30},
                    flags_set={"chose_villagers": True, "met_marcus": True},
                ),
                Choice(
                    text="🐺 追击逃窜的暗影狼（DEX检定 DC=14）",
                    result_text="你决定追踪狼群——它们可能引领你发现更大的秘密。",
                    check_type="dex", dc=12,
                    success_text="你凭借敏捷的身手追上了狼群。它们逃入了一个隐蔽的洞穴——那是暗影生物的聚集地。你在洞穴口发现了一些宝贵的补给和装备。",
                    failure_text="狼群在森林中过于灵活，你没能追上它们，但至少发现了它们盘踞的大致方向。",
                    critical_success_text="你以惊人的速度截住了狼群！在击退头狼后，你找到了它守护的密宝——一枚散发着黑暗能量的「暗影之心」。它蕴含着强大的力量，但使用它需要付出代价……",
                    critical_failure_text="你在密林中追得太深，被狼群伏击！虽然击退了它们，但伤势不轻。HP -15。",
                    hp_change=-15,
                    xp_reward=35,
                    item_reward="破魔之弩",
                    faction_reputation={"SHADOW": 30},
                    flags_set={"chose_hunt": True},
                ),
            ],
        ),

        # ===== 事件3b: 分支 — 拯救线（仅 chose_villagers） =====
        Event(
            event_id="c1_villager_path",
            title="🤝 马库斯的回报",
            description=(
                "马库斯是一个游走于绝夜之境的商人。\n"
                "他在列车上经营着一个秘密商店，专门出售在黑暗中搜集到的稀有物品。\n\n"
                "「作为救命的回报，我愿意与你分享我的收藏。」\n"
                "「不过，我的商店需要在安全的环境下才能开放——等你回到列车上再说吧。」\n\n"
                "他递给你一张泛黄的地图：「这是通往城堡的捷径，比绕森林快得多。」\n"
                "「祝你好运，勇士。」"
            ),
            event_type=EventType.STORY,
            required_flags={"chose_villagers": True},
            choices=[
                Choice(
                    text="感谢马库斯，继续前行",
                    result_text="你收下了地图，继续向城堡进发。有了马库斯的指引，前方的路似乎清晰了不少。",
                    xp_reward=15,
                    gold_reward=30,
                    flags_set={"has_map_shortcut": True},
                ),
            ],
        ),

        # ===== 事件3c: 分支 — 追击线（仅 chose_hunt） =====
        Event(
            event_id="c1_hunt_path",
            title="🕳 暗影巢穴",
            description=(
                "你追踪狼群来到一处被黑暗笼罩的地下洞穴。\n"
                "洞壁上刻满了扭曲的符文，空气中弥漫着腐肉和硫磺的气味。\n"
                "这显然不只是狼群的巢穴——这里是暗影生物在森林中的据点。\n\n"
                "洞穴深处，你看到一道暗紫色的传送门，源源不断地涌出小型恶魔。\n"
                "「必须关闭这道传送门。」一个低沉的声音在你脑海中响起。"
            ),
            event_type=EventType.CHOICE,
            required_flags={"chose_hunt": True},
            choices=[
                Choice(
                    text="⚔️ 摧毁传送门（触发战斗）",
                    result_text="你握紧武器，冲向那道不断涌出恶魔的传送门！",
                    trigger_combat=True, combat_enemy="demon_imp",
                    xp_reward=40,
                    faction_reputation={"SHADOW": 15, "OBSERVER": 10},
                    flags_set={"closed_portal": True},
                ),
                Choice(
                    text="🧠 研究传送门的符文（INT检定 DC=14）",
                    result_text="你决定先弄清楚这道传送门的运作原理。",
                    check_type="int", dc=12,
                    success_text="你成功解读了符文——这是深渊领主布下的传送网络。你不仅关闭了它，还获得了关于深渊军团的重要情报。",
                    failure_text="符文太过古老和复杂，你无法完全理解它的含义。",
                    critical_success_text="你完全掌握了传送门的运作原理！不仅如此，你逆向操作，将传送门改造成了己用——周围的暗影能量被吸收，形成了一枚「暗影精华」储存在你体内。",
                    critical_failure_text="你触发了传送门的防御机制——一道暗影能量爆发，将你击退。HP -10。",
                    hp_change=-10,
                    xp_reward=35,
                    faction_reputation={"OBSERVER": 25},
                    shadow_essence=3,
                ),
            ],
        ),

        # ===== 事件3: 黑暗森林 =====
        Event(
            event_id="c1_forest",
            title="🌲 暗影森林",
            description=(
                "你带领幸存者们进入了那片散发着幽光的黑色森林。\n\n"
                "这里的树木扭曲而诡异，枝干像枯槁的手臂伸向天空。\n"
                "林间弥漫着淡紫色的雾气，远处不时传来令人毛骨悚然的嚎叫。\n\n"
                "走了许久，你们来到一个岔路口：\n"
                "左边的路宽敞平坦，但地上散落着破碎的骸骨；\n"
                "右边的路狭窄曲折，但隐约能听到水流声——水源意味着生机；\n"
                "中间则需要攀爬一段陡峭的岩壁，但那是通往城堡的最短路径。"
            ),
            event_type=EventType.CHOICE,
            choices=[
                Choice(
                    text="走左边——宽敞但危险的路（战斗）",
                    result_text="你选择了看似最容易走的路，但危险往往就潜伏在最显眼的地方。",
                    trigger_combat=True, combat_enemy="dark_spirit",
                    xp_reward=35,
                ),
                Choice(
                    text="走右边——寻找水源（WIS检定 DC=13）",
                    result_text="你跟随水声探索前进。",
                    check_type="wis", dc=11,
                    success_text="你成功找到了森林中的一处清泉！虽然泉水泛着微弱的荧光，但经过检测是无毒的。幸存者们补充了水分，体力恢复了不少。",
                    failure_text="你跟着水声走了很久，却发现那是一条干涸的河床——水声只是风声在岩石间穿梭的错觉。",
                    critical_success_text="你不仅找到了水源，还在泉水旁发现了一座古老的精灵祭坛。祭坛上的铭文揭示了黑暗的起源，同时祭坛本身散发出治愈的力量——全体恢复HP！HP +20。",
                    critical_failure_text="你找到的水源被黑暗力量污染了！所有饮用者都陷入短暂的虚弱状态。HP -5。",
                    hp_change=-5,
                    xp_reward=25,
                ),
                Choice(
                    text="走中间——攀爬岩壁捷径（STR检定 DC=14）",
                    result_text="你选择挑战陡峭的岩壁。",
                    check_type="str", dc=12,
                    success_text="虽然过程艰难，但你成功带领大家翻越了岩壁，节省了大量时间。前方，那座阴森的城堡已经清晰可见。",
                    failure_text="岩壁比你预想的更加湿滑。你爬到一半滑了下来，只能绕路前行。",
                    critical_success_text="你如壁虎般轻松攀上岩壁！在顶端你发现了俯瞰整片森林的绝佳视野——你不仅看到了通往城堡的最优路线，还发现了一处藏在岩缝中的宝箱，里面有一件「暗夜斗篷」。",
                    critical_failure_text="攀爬过程中岩壁崩裂！你重重摔下来，扭伤了脚踝。HP -12，且接下来的路程中DEX检定-2。",
                    hp_change=-12,
                    xp_reward=25,
                    item_reward="暗夜斗篷",
                ),
            ],
        ),

        # ===== 事件4: 堕落骑士（中Boss） =====
        Event(
            event_id="c1_midboss",
            title="🏰 城堡守卫",
            description=(
                "你们终于抵达了城堡大门前。\n\n"
                "这座城堡由黑色的石材筑成，尖塔直刺黑暗的天空。\n"
                "城门紧闭，门前伫立着一个身穿漆黑铠甲的高大身影。\n\n"
                "「来者止步！」低沉的声音从头盔中传出。\n"
                "「我是这座城堡的守护者——曾经的圣殿骑士。如今我只效忠于绝夜。」\n"
                "他缓缓拔出泛着黑光的长剑：「想要通过，就先击败我！」"
            ),
            event_type=EventType.COMBAT,
            choices=[
                Choice(
                    text="⚔️ 迎战堕落骑士！",
                    result_text="你握紧武器，准备迎接这位堕落骑士的挑战！",
                    trigger_combat=True, combat_enemy="corrupted_knight",
                    xp_reward=50,
                    flags_set={"defeated_knight": True},
                ),
                Choice(
                    text="尝试说服他回忆过去的荣耀（CHA检定 DC=16）",
                    result_text="你试图唤起骑士心中残存的良知。",
                    check_type="cha", dc=14,
                    success_text="你的话语触动了他内心深处的记忆。堕落骑士单膝跪地：「你……让我想起了我曾经守护的东西。请进吧，但请小心——城堡的主人是暗影巨龙，它的力量远超你的想象。」",
                    failure_text="堕落骑士只是冷笑：「我早已抛弃了那些无用的荣耀。」他向你发起了攻击！",
                    critical_success_text="你的言辞如阳光穿透黑暗！堕落骑士的黑甲崩裂，露出了下方金色的圣骑士铠甲。「我……想起了我的誓言。」他将「圣殿之剑」交给你，「它会帮助你对抗暗影巨龙。」",
                    critical_failure_text="你的话激怒了堕落骑士，他陷入了狂暴状态！HP -10，并且必须强制战斗。",
                    hp_change=-10,
                    xp_reward=30,
                    item_reward="圣殿之剑",
                ),
            ],
        ),

        # ===== 事件5: 暗影巨龙（第一章Boss） =====
        Event(
            event_id="c1_boss",
            title="🐉 暗影巨龙",
            description=(
                "你推开城堡最深处的巨门，一股灼热的暗影能量扑面而来。\n\n"
                "大厅的穹顶之下，堆积如山的金币与骸骨之上——\n"
                "盘踞着一头浑身覆盖暗紫色鳞片的巨龙！\n\n"
                "它的双眼如同燃烧的深渊，每一次呼吸都让空气扭曲。\n"
                "「又一批迷途的羔羊……」巨龙发出低沉的笑声。\n"
                "「你们的列车、你们的希望、你们的生命——都是我的。」\n\n"
                "暗影巨龙张开了遮天蔽日的双翼——\n"
                "第一章的最终战斗，即将开始！"
            ),
            event_type=EventType.BOSS,
            choices=[
                Choice(
                    text="⚔️ 挑战暗影巨龙！终结第一章！",
                    result_text="你紧握武器，冲向那头盘踞在黑暗王座之上的远古巨龙！决战的时刻到了！",
                    trigger_combat=True, combat_enemy="shadow_dragon",
                    xp_reward=200,
                    flags_set={"chapter1_complete": True},
                ),
            ],
            auto_next="c1_end",
        ),

        # ===== 事件6: 第一章结束 =====
        Event(
            event_id="c1_end",
            title="🌅 第一章 · 完",
            description=(
                "暗影巨龙发出最后的悲鸣，庞大的身躯轰然倒下。\n"
                "黑暗的能量从它体内逸散而出，消失在空气中。\n\n"
                "城堡的墙壁开始崩裂，露出一道通往外界的裂隙。\n"
                "但裂隙的另一端并非你们来时的世界……\n\n"
                "远处的铁轨上，一辆幽灵列车缓缓驶来，车灯照亮了黑暗。\n"
                "车门自动打开，仿佛在邀请你们继续前行。\n\n"
                "「看来，这只是开始……」\n"
                "你望向列车驶来的方向——更深的黑暗中，隐藏着更大的阴谋。\n\n"
                "【第一章「暗夜降临」· 完】\n"
                "下一章：第二章「幽影迷途」"
            ),
            event_type=EventType.TRAIN,
            choices=[
                Choice(
                    text="登上幽灵列车，继续前行",
                    result_text="你深吸一口气，踏上了幽灵列车。车门缓缓关闭，列车驶向更加深邃的黑暗……",
                    xp_reward=50,
                ),
            ],
        ),
    ]

    return Chapter(
        chapter_id=1,
        title="第一章",
        subtitle="暗夜降临",
        intro_text=(
            "当你睁开双眼时，窗外的世界已经不再是你所认识的那个世界。\n"
            "列车仍在铁轨上轰鸣前行，但天空的颜色变得陌生。\n"
            "暗紫色的月亮高悬在天际，永夜笼罩着这片神秘的大地。\n\n"
            "欢迎来到「绝夜之境」——一个被黑暗吞噬的失落领域。\n"
            "在这里，你将面对来自深渊的妖魔，揭开隐藏千年的秘密。\n"
            "你的每一个选择，每一次骰子的投掷，都将决定你的命运。\n\n"
            "第一章：暗夜降临 —— 现在开始。"
        ),
        events=events,
    )
