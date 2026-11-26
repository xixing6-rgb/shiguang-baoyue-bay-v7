---@id dfacf592-c757-4758-95fa-bf000f4bd97c
---@referenceName blackboard-dialogue-engine.lua
---@displayName 黑板规则对话、Tracery流行语展开与程序语音变调引擎
---@start
---@var DefaultVoiceMode:string="dual"
---@name 默认声道模式
---@desc dual(按居民人设自动切换软萌/机械) / animalese / mech_tts
---@group 语音
---@var RuleCooldownSeconds:number=180
---@name 台词防复读冷却
---@desc 同一条黑板规则两次触发之间的最小间隔秒数
---@group 对话规则
---@var MaxTraceryDepth:number=5
---@name Tracery递归上限
---@desc 生成语法最大展开深度，防止循环引用
---@group 对话规则
---@var SyllableInterval:number=0.075
---@name 音节基准间隔
---@desc 动物语/机械音节打字机每个音素的基准时长（秒）
---@group 语音
---@end

local Time = CS.UnityEngine.Time
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("blackboard-dialogue")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 平台官方动作与表现白名单校验表（严禁手指精细动作、面部嘴型动画、跳跃攀爬）
local ALLOWED_ACTIONS = {
  walk = true,
  run = true,
  greet = true,
  wave = true,
  sit = true,
  clap = true,
  cheer = true,
  dance = true,
  photo = true,
  water_bend = true,
  turn_to_player = true,
  hop_bounce = true,
  nod_tilt = true,
  hover_bob = true,
  door_open = true,
  pivot_spin = true,
  paper_pet_squash = true,
  bubble_yellow = true,
  bubble_orange = true,
  bubble_pink = true,
  bubble_purple = true,
  fx_heart = true,
  fx_sparkle = true,
  fx_petal = true,
  fx_ripple = true,
  fx_firefly = true,
  voice_soft = true,
  voice_mech = true,
}

local VOICE_PROFILES = {
  C01 = { mode = "animalese", basePitch = 0.78, sizeOffset = -0.10, speed = 0.90 },
  C02 = { mode = "animalese", basePitch = 1.32, sizeOffset = 0.12, speed = 1.10 },
  C03 = { mode = "mech_tts",  basePitch = 0.95, sizeOffset = 0.00, speed = 0.88 },
  C04 = { mode = "animalese", basePitch = 1.12, sizeOffset = 0.04, speed = 1.22 },
  C05 = { mode = "mech_tts",  basePitch = 1.04, sizeOffset = 0.08, speed = 0.84 },
  C06 = { mode = "animalese", basePitch = 0.92, sizeOffset = -0.03, speed = 0.95 },
  C07 = { mode = "animalese", basePitch = 1.20, sizeOffset = 0.05, speed = 1.28 },
  C08 = { mode = "mech_tts",  basePitch = 0.98, sizeOffset = 0.00, speed = 1.08 },
  C09 = { mode = "animalese", basePitch = 1.26, sizeOffset = 0.06, speed = 0.96 },
}

local MOOD_PITCH_OFFSET = {
  neutral = 0.00,
  happy = 0.12,
  shy = 0.06,
  surprised = 0.18,
  deadpan = -0.05,
}

local TRACERY_GRAMMAR = {
  origin = { "#newsHeadline#", "#gossipBit#", "#bottleEcho#" },
  newsHeadline = {
    "【风铃湾整点怪闻】今日 #resident# 在 #facility# 一本正经地宣布：“全岛最新风尚是 #lingo#！” #quirkReaction#",
    "【海风速报】据 #resident# 观测，昨晚有人对着 #facility# 连喊三声“#lingo#”，海浪当场多回响了一秒！",
    "【微光夜市食评】#resident# 认真表示：把烤面包配着“#lingo#”一起吃，幸福感提升 25%！",
  },
  gossipBit = {
    "我刚才路过 #facility#，看见 #resident# 正和纸片宠物“#petName#”深情对视，两秒后一起慢拍鼓掌。",
    "听说 #resident# 偷偷在 #facility# 练习怎么念“#lingo#”，结果把海鸥都逗笑了。",
    "今天 #weatherMood#，#resident# 想在 #facility# 旁边升起写着“#flagTitle#”的小旗子。",
  },
  bottleEcho = {
    "漂流纸条写着：‘无论世界多吵，风铃湾允许你只做 #lingo# 这一件微不足道的小事。’",
    "星砂漂流书屋摘录：‘把旧友画成纸片宠物 #petName#，海风吹过 #facility# 时他们就一直还在。’",
  },
  concertLyric = {
    "♪ 晚霞落在潮汐线，大家一起把 #lingo# 挂上 #flagTitle# 飘起来 ♪",
    "♪ #petName# 摇摇摆摆跟着散步，风铃湾把未寄出的信唱给远方 ♪",
  },
  resident = { "阿木", "绵绵", "阿橘", "奶包", "墨羽", "阿澈", "团团", "咔哒", "绒绒" },
  facility = { "心愿喷泉", "风铃旧邮局", "微光夜市烤包炉", "白昼号灯船", "记忆温室图书馆", "古樟星穹台", "潮汐回声剧场" },
  quirkReaction = {
    "阿橘面无表情地鼓了两下掌表示认可。",
    "咔哒立刻掏出直尺确认该姿势完全垂直于地面。",
    "墨羽原地悬浮升高了五厘米以示敬意。",
    "绵绵害羞得用垂耳朵把整张脸盖住了。",
    "团团一激动从兜里掉出了三封去年的旧明信片。",
  },
  weatherMood = { "暖阳奶油绿正好", "琥珀晚霞斜照", "星夜碎灯初亮", "微雨沙沙拍打木廊" },
  lingo = { "慢一点也没关系" },
  petName = { "小白喵" },
  flagTitle = { "风铃湾小鱼旗" },
}

-- Valve 式黑板规则库全量 86 条（与 narrative-db.json 100% 同步）
local BLACKBOARD_RULES = {
  { id = "BB01", residentId = "C02", cond = { chapter = "prologue", zone = "Zone0" }, prio = 90, act = "wave", bub = nil, txt = "呀，渡船靠岸的声音比平时轻呢——欢迎来到时光小筑，今天想先去看看花圃还是主木屋呀？" },
  { id = "BB02", residentId = "C01", cond = { chapter = "prologue", facilityId = "F04" }, prio = 92, act = "greet", bub = nil, txt = "主木屋的门感应到你会自己打开，没有房贷也没有倒计时，想在壁炉旁坐多久都可以。" },
  { id = "BB03", residentId = "C03", cond = { chapter = "prologue", facilityId = "F11" }, prio = 88, act = "clap", bub = nil, txt = "……啪、啪。这就是我能给出的最大热情欢迎了。黑板写歪的事一会儿记得自己看看。" },
  { id = "BB04", residentId = "C04", cond = { chapter = "prologue", facilityId = "F12" }, prio = 85, act = "cheer", bub = "bubble_yellow", txt = "刚出炉的海风可颂！趁现在还没被阿澈抢走最后一块，快尝一口吧！" },
  { id = "BB05", residentId = "C05", cond = { chapter = "prologue", facilityId = "F15" }, prio = 84, act = "hover_bob", bub = nil, txt = "从风车塔顶往下看，西海角那座黑着灯的旧灯塔，好像还留着当年的一点点棱镜反光。" },
  { id = "BB06", residentId = "C06", cond = { chapter = "prologue", facilityId = "F02" }, prio = 86, act = "sit", bub = nil, txt = "鱼今天大概也在休假……别盯着我的草帽看，我只是顺便晒晒太阳。" },
  { id = "BB07", residentId = "C01", cond = { facilityId = "F16", timeSlot = "dusk" }, prio = 95, act = "photo", bub = nil, txt = "傍晚站在望远镜前，西边灯塔、东边白昼号、北边玻璃温室和南边回声拱门刚好同时映进眼睛。" },
  { id = "BB08", residentId = "C02", cond = { yesterdayAction = "watered_flower", weather = "sunny" }, prio = 98, act = "hop_bounce", bub = nil, txt = "听说你昨天顶着大太阳给孟德尔花圃连浇了三遍水！今天清晨居然冒出了亮晶晶的花苞呢！" },
  { id = "BB09", residentId = "C02", cond = { yesterdayAction = "watered_flower", weather = "rain" }, prio = 100, act = "water_bend", bub = nil, txt = "昨天明明下着小雨你还是来花圃照顾花朵了，它们偷偷跟我说它们今天特别精神。" },
  { id = "BB10", residentId = "C03", cond = { yesterdayAction = "nudged_resident" }, prio = 96, act = "clap", bub = "bubble_purple", txt = "昨天有人把我整只拎起来放在咖啡桌上。我考虑了三秒，决定面无表情地鼓掌回敬你。" },
  { id = "BB11", residentId = "C04", cond = { yesterdayAction = "fed_bun" }, prio = 94, act = "dance", bub = "bubble_yellow", txt = "昨天那只烤包香气我记到今天早上！顺便说我的大胃王饱腹槽今天还空着五格哦！" },
  { id = "BB12", residentId = "C06", cond = { yesterdayAction = "fished_at_pier" }, prio = 93, act = "nod_tilt", bub = nil, txt = "听说你昨天在栈桥坐了好久也没钓到鱼。别灰心，这说明海里的鱼很信任你不会打扰它们。" },
  { id = "BB13", residentId = "C01", cond = { yesterdayAction = "changed_flag" }, prio = 92, act = "greet", bub = nil, txt = "昨天主庭院旗杆换上的新 12×12 像素小旗，被阿橘偷偷抄进他的《奇怪但时髦小报》里了。" },
  { id = "BB14", residentId = "C03", cond = { yesterdayAction = "changed_chalkboard" }, prio = 95, act = "turn_to_player", bub = nil, txt = "黑板上昨天新写的“#lingo#”，我已经一字不差背下来了。今天全岛都会严肃复读这句话。" },
  { id = "BB15", residentId = "C05", cond = { timeSlot = "afternoon", quirk = "levitating_night_owl" }, prio = 82, act = "hover_bob", bub = nil, txt = "午后两点重力太重，所以我选择离地二十五厘米打盹。有事请找黄昏后的我。" },
  { id = "BB16", residentId = "C05", cond = { timeSlot = "night" }, prio = 90, act = "hover_bob", bub = "bubble_pink", txt = "星夜模式上线。现在全镇的灯串和荧光都已经对准了你的散步路线。" },
  { id = "BB17", residentId = "C04", cond = { timeSlot = "night", zone = "ZoneE" }, prio = 96, act = "cheer", bub = "bubble_yellow", txt = "欢迎来到星夜微光夜市！晚间 65% 的街坊都会被烤包窑炉吸过来，绝不让你一个人逛夜街！" },
  { id = "BB18", residentId = "C02", cond = { facilityId = "F06" }, prio = 88, act = "water_bend", bub = nil, txt = "记住啦，如果只给孤零零一株蓝玫瑰浇水、周围不放配对花朵，它会触发无性克隆留住纯正基因哦。" },
  { id = "BB19", residentId = "C07", cond = { chapter = "ch1", zone = "ZoneW" }, prio = 95, act = "hop_bounce", bub = "bubble_orange", txt = "呜哇对不起对不起！风铃旧邮局里的信封被海风吹散了，你能帮我一起找回抽屉里的记忆吗？" },
  { id = "BB20", residentId = "C03", cond = { chapter = "ch1", facilityId = "F19" }, prio = 98, act = "turn_to_player", bub = nil, txt = "被发现了么……这些写给别人却没敢寄出的卡片，我觉得丢进海里太可惜，就顺手帮大家按颜色收着了。" },
  { id = "BB21", residentId = "C07", cond = { facilityId = "F20" }, prio = 90, act = "wave", bub = nil, txt = "这个阶梯信箱画廊每一格都对应一个人没说出口的小小心事——连阿橘都有一整排自己的贴纸呢！" },
  { id = "BB22", residentId = "C05", cond = { chapter = "ch1", facilityId = "F22" }, prio = 99, act = "hover_bob", bub = nil, txt = "黄铜棱镜装回去了。当灯塔暖光每十二秒扫过海湾一次，旧年的约定就像被海风重新熨平一样。" },
  { id = "BB23", residentId = "C07", cond = { facilityId = "F42" }, prio = 94, act = "cheer", bub = nil, txt = "铛铛！薄荷绿邮差单车驿站开通啦！以后横跨四个片区再也不怕走断腿，只需 1.5 秒伴着铃声直达！" },
  { id = "BB24", residentId = "C01", cond = { chapter = "ch1", timeSlot = "dusk" }, prio = 88, act = "nod_tilt", bub = nil, txt = "西岬灯塔重新亮起来那刻，我看见阿澈在东边栈桥上悄悄把草帽摘下来看了一眼。" },
  { id = "BB25", residentId = "C06", cond = { chapter = "ch1", timeSlot = "dusk" }, prio = 91, act = "turn_to_player", bub = nil, txt = "西边那束光扫过来挺刺眼的……好吧，其实也挺暖和的，比黑着强多了。" },
  { id = "BB26", residentId = "C07", cond = { zone = "ZoneW", weather = "breeze" }, prio = 85, act = "wave", bub = nil, txt = "风铃长廊一刮海风就会叮叮当当响，我每次路过都会忘记自己原本要去送哪封信。" },
  { id = "BB27", residentId = "C03", cond = { zone = "ZoneW", affectionMin = 60 }, prio = 92, act = "clap", bub = nil, txt = "既然你帮我守住了秘密抽屉，允许你在我的纸条末尾添一句你的口癖“#lingo#”。" },
  { id = "BB28", residentId = "C02", cond = { zone = "ZoneW", facilityId = "F24" }, prio = 89, act = "sit", bub = nil, txt = "西滩的漂流木篝火角特别适合看西拱桥方向的落日，好像整个世界的节奏都慢了半拍。" },
  { id = "BB29", residentId = "C07", cond = { quirk = "absentminded_drop" }, prio = 80, act = "hop_bounce", bub = "bubble_purple", txt = "等等——我刚才手里明明攥着一把邮局钥匙，怎么一眨眼只剩一块饼干屑了？！" },
  { id = "BB30", residentId = "C04", cond = { zone = "ZoneW" }, prio = 84, act = "greet", bub = nil, txt = "听说邮局旁边那条路风吹过来特别香，我是顺着团团兜里掉出来的黄油饼干屑摸过来的！" },
  { id = "BB31", residentId = "C05", cond = { facilityId = "F21" }, prio = 86, act = "hover_bob", bub = nil, txt = "透过风铃长廊的木框刚好框住远处的西岬灯塔，这就叫绘本视角里的窥视构图。" },
  { id = "BB32", residentId = "C07", cond = { affectionMin = 100 }, prio = 95, act = "greet", bub = "bubble_pink", txt = "现在就算我把信弄混了，大家也都会笑着拆开然后说‘正好替远方朋友打个招呼’呢。" },
  { id = "BB33", residentId = "C08", cond = { chapter = "ch2", zone = "ZoneE" }, prio = 96, act = "nod_tilt", bub = "bubble_purple", txt = "站住！东湾路牌歪了 `1.5°`，先让我掏出木工尺把它扶正再跟你打招呼！咔哒咔哒！" },
  { id = "BB34", residentId = "C06", cond = { chapter = "ch2", facilityId = "F27" }, prio = 99, act = "turn_to_player", bub = nil, txt = "别用那种眼神看白昼号。我用木楔把它卡在浅滩，只是因为不想再送走任何一个人了。" },
  { id = "BB35", residentId = "C04", cond = { chapter = "ch2", facilityId = "F25" }, prio = 98, act = "dance", bub = "bubble_yellow", txt = "炉火点着了！全镇今晚都要来我这儿吃刚出炉的蜜瓜包！阿澈船长也别想躲在甲板上发呆！" },
  { id = "BB36", residentId = "C08", cond = { facilityId = "F26" }, prio = 92, act = "nod_tilt", bub = nil, txt = "我把白昼号的跳板斜度修到 `11.5°`，就算不靠跳跃也能稳稳当当走上甲板敲响铜钟！" },
  { id = "BB37", residentId = "C06", cond = { facilityId = "F40" }, prio = 94, act = "wave", bub = nil, txt = "这艘摇橹小渡船虽小，从老镇码头划到南屿或东湾只要两秒钟，上来坐稳了，别晃。" },
  { id = "BB38", residentId = "C02", cond = { chapter = "ch2", facilityId = "F06" }, prio = 95, act = "cheer", bub = nil, txt = "成功啦！！孟德尔花圃绽放出第一株杂交蓝玫瑰了！北麓溪谷的花藤拱门正朝我们打开呢！" },
  { id = "BB39", residentId = "C08", cond = { zone = "ZoneE", weather = "sunny" }, prio = 86, act = "greet", bub = nil, txt = "阳光下的东湾浅水池 L-0.5 不会太深，只漫过脚踝十厘米，走起来哗啦哗啦真解压。" },
  { id = "BB40", residentId = "C04", cond = { facilityId = "F25", timeSlot = "dusk" }, prio = 90, act = "cheer", bub = nil, txt = "黄昏刚到我就开始预热红砖面包窑，方圆四十米很快就会飘满黄油麦芽香。" },
  { id = "BB41", residentId = "C06", cond = { facilityId = "F28" }, prio = 88, act = "water_bend", bub = nil, txt = "潮间带退潮后会留下很多打磨光滑的海玻璃，每一块都像别人忘在沙滩的一句晚安。" },
  { id = "BB42", residentId = "C08", cond = { quirk = "symmetry_ocd" }, prio = 85, act = "nod_tilt", bub = "bubble_purple", txt = "你看，夜市的三排串灯我特意调成了等腰三角形，看着是不是整只浣熊都神清气爽了？" },
  { id = "BB43", residentId = "C03", cond = { zone = "ZoneE", timeSlot = "night" }, prio = 91, act = "clap", bub = nil, txt = "真受不了这群吵闹的家伙，全挤在烤包炉子前面……不过奶包烤的鱼肉包确实还不赖。" },
  { id = "BB44", residentId = "C05", cond = { zone = "ZoneE", timeSlot = "night" }, prio = 89, act = "hover_bob", bub = nil, txt = "白昼号桅杆那盏大灯点亮以后，连东海面的雾都变成了柔和的奶橘色。" },
  { id = "BB45", residentId = "C07", cond = { zone = "ZoneE" }, prio = 84, act = "wave", bub = nil, txt = "我把单车驿站也修到微光夜市旁边啦！买完烤包骑两圈就能回老镇！" },
  { id = "BB46", residentId = "C06", cond = { affectionMin = 100 }, prio = 97, act = "greet", bub = "bubble_pink", txt = "其实白昼号重新亮起桅灯那晚，我觉得就算大家不急着出海，能这样彼此守着海湾也很棒。" },
  { id = "BB47", residentId = "C09", cond = { chapter = "ch3", zone = "ZoneN" }, prio = 96, act = "dance", bub = "bubble_orange", txt = "呀！被你发现了……只要握着画笔我就停不下来走台步，请、请千万别笑话我的纸片线条！" },
  { id = "BB48", residentId = "C01", cond = { chapter = "ch3", facilityId = "F31" }, prio = 98, act = "greet", bub = nil, txt = "欢迎踏入第二座室内空间——记忆温室图书馆。雨声落在弧形玻璃顶上的声音，能让人一口气读完一整章年谱。" },
  { id = "BB49", residentId = "C09", cond = { facilityId = "F18" }, prio = 94, act = "paper_pet_squash", bub = nil, txt = "当年离开的老朋友害怕被忘记，就把宠物剪成带奶油白边的 2D 纸片牌留在时光石旁陪我们散步。" },
  { id = "BB50", residentId = "C01", cond = { facilityId = "F33" }, prio = 92, act = "nod_tilt", bub = nil, txt = "水车磨坊旁的旧留声亭支持插入收集到的黑胶唱片，换一首曲子，整片森林的呼吸就变柔和一分。" },
  { id = "BB51", residentId = "C09", cond = { facilityId = "F35" }, prio = 93, act = "cheer", bub = nil, txt = "咔哒刚修好的林间快速木滑道太好玩了！辛苦走盘山坡上去后，只要坐上去五秒就能咻地滑回山下！" },
  { id = "BB52", residentId = "C02", cond = { zone = "ZoneN", weather = "rain" }, prio = 91, act = "hop_bounce", bub = nil, txt = "下雨的时候躲进 F31 玻璃温室里面看苗床发芽，暖黄的灯光透过玻璃雾气简直像在绘本里！" },
  { id = "BB53", residentId = "C05", cond = { zone = "ZoneN", timeSlot = "night" }, prio = 95, act = "hover_bob", bub = nil, txt = "萤火浅溪晚上会有萤火虫沿着木拱桥飘出来，那也是黑夜环境色里最温柔的导航线。" },
  { id = "BB54", residentId = "C08", cond = { facilityId = "F32" }, prio = 89, act = "nod_tilt", bub = nil, txt = "这两座横跨萤火浅溪的木拱桥我特意将坡度压在 `12°` 以内，散步绝不费鞋。" },
  { id = "BB55", residentId = "C01", cond = { facilityId = "F36" }, prio = 96, act = "photo", bub = nil, txt = "西北角树洞邮筒里藏着三十年前的旧合照，它们见证了时光小筑从一座孤单渡口长成现在的样子。" },
  { id = "BB56", residentId = "C09", cond = { quirk = "shy_runway_walk" }, prio = 86, act = "dance", bub = "bubble_yellow", txt = "刚、刚才画完新纸片宠物太激动了，不知不觉又沿着长椅走了一个 T 台回旋……好丢人但好爽！" },
  { id = "BB57", residentId = "C03", cond = { zone = "ZoneN" }, prio = 87, act = "clap", bub = nil, txt = "图书馆很安静，很适合我一个人待着……除了羊绒绒突然开始走猫步的时候。" },
  { id = "BB58", residentId = "C04", cond = { zone = "ZoneN" }, prio = 84, act = "greet", bub = nil, txt = "听说北坡滑道滑下来正好能接上咖啡香，那我每天要从山上滑下来三次！" },
  { id = "BB59", residentId = "C07", cond = { zone = "ZoneN" }, prio = 85, act = "wave", bub = nil, txt = "我在图书馆外面也停了一辆薄荷单车！不过图书馆里禁止按车铃，我把铃铛用棉花包起来了。" },
  { id = "BB60", residentId = "C09", cond = { affectionMin = 100 }, prio = 97, act = "greet", bub = "bubble_pink", txt = "谢谢你没有觉得粗糙手绘的纸片小兽和 3D 世界格格不入，画得笨拙才更有我们的体温呀。" },
  { id = "BB61", residentId = "C05", cond = { chapter = "ch4", facilityId = "F34" }, prio = 100, act = "hover_bob", bub = nil, txt = "站在全岛最高点古樟星穹台往下望——中轴线直指星砂小屿的回声拱门，所有线头今天都在这里汇合了。" },
  { id = "BB62", residentId = "C08", cond = { chapter = "ch4", facilityId = "F37" }, prio = 96, act = "cheer", bub = nil, txt = "弧形西跨海木拱桥合龙！东踏石礁道也在退潮后全线贯通，现在环湾山海大环可以一口气走完！" },
  { id = "BB63", residentId = "C06", cond = { chapter = "ch4", facilityId = "F39" }, prio = 98, act = "wave", bub = nil, txt = "从南屿风铃拱门回望核心老镇和主木屋，感觉像第一次站在画框外面看自己的家一样。" },
  { id = "BB64", residentId = "C04", cond = { chapter = "ch4", facilityId = "F39" }, prio = 95, act = "dance", bub = "bubble_yellow", txt = "回声音乐会开始啦！我带了九人份的窑烤蜜瓜包来当全场观众席零嘴！" },
  { id = "BB65", residentId = "C03", cond = { chapter = "ch4", facilityId = "F39" }, prio = 97, act = "clap", bub = nil, txt = "……啪、啪、啪。今天我决定多鼓掌一下。你们唱的那句“#lingo#”，回声听着竟然还不赖。" },
  { id = "BB66", residentId = "C09", cond = { facilityId = "F41" }, prio = 95, act = "greet", bub = nil, txt = "迷你漂流书屋里收着远方访客留下的短句，抽一张出来读一读，好像突然多了位没谋面的好友。" },
  { id = "BB67", residentId = "any", cond = { directorSoftBias = true }, prio = 91, act = "greet", bub = nil, txt = "咦，真巧呀——我正好顺路散步来这片区域看看海风和松果，没想到会撞见你！" },
  { id = "BB68", residentId = "any", cond = { playerAbsentLong = true }, prio = 99, act = "wave", bub = "bubble_pink", txt = "好久不见啦！这里的好感度永远不会因为你忙碌而掉分，草坪上的花朵和我们一直按原样等你回来。" },
  { id = "BB69", residentId = "any", cond = { affectionMin = 150 }, prio = 95, act = "photo", bub = "bubble_pink", txt = "和你相处久了以后，连海风吹过耳边的节奏都变得熟悉。这张裱好的纪念照送给你留作记忆吧！" },
  { id = "BB70", residentId = "any", cond = { weather = "sunny", timeSlot = "afternoon" }, prio = 65, act = "walk", bub = nil, txt = "午后两点的高明度阳光洒在奶油绿草地上，整个人大脑里的杂音一下子安静下来了。" },
  { id = "BB71", residentId = "any", cond = { weather = "breeze", timeSlot = "dusk" }, prio = 68, act = "wave", bub = nil, txt = "傍晚五点半琥珀色的晚霞刚好斜斜打在主木屋窗格上，风铃都在替我们吹号角。" },
  { id = "BB72", residentId = "any", cond = { weather = "rain" }, prio = 74, act = "water_bend", bub = nil, txt = "下雨了也不用赶回室内任务，听听雨水打在草坪和栈桥上的声音，就是最好的背景白噪音。" },
  { id = "BB73", residentId = "any", cond = { weather = "starlight", timeSlot = "night" }, prio = 75, act = "hover_bob", bub = nil, txt = "星夜雾气柔柔地裹着灯塔与夜市暖灯，每走十米就有小路灯给你指路。" },
  { id = "BB74", residentId = "any", cond = { bubble = "bubble_yellow" }, prio = 78, act = "hop_bounce", bub = "bubble_yellow", txt = "突然好想吃点香喷喷的东西或者换个新气象——你觉得今天的流行语“#lingo#”配什么甜点？" },
  { id = "BB75", residentId = "any", cond = { bubble = "bubble_orange" }, prio = 79, act = "turn_to_player", bub = "bubble_orange", txt = "刚才有件事一直想找街坊聊聊但有点不好意思开口……你能轻推我一把或帮我递句话吗？" },
  { id = "BB76", residentId = "any", cond = { bubble = "bubble_pink" }, prio = 82, act = "greet", bub = "bubble_pink", txt = "今天的海风太温柔了，忍不住想和你约定一个只有我们知道的暗号：“#lingo#”！" },
  { id = "BB77", residentId = "any", cond = { bubble = "bubble_purple" }, prio = 83, act = "nod_tilt", bub = "bubble_purple", txt = "奇怪……刚才绕着长椅转了两圈以后突然忘记自己为什么站在这里，可能是海风把内存吹跑了！" },
  { id = "BB78", residentId = "any", cond = { asyncVisitMemory = true }, prio = 92, act = "greet", bub = nil, txt = "对了，昨天有位远方的串门旅人路过老镇，夸你挂在旗杆上的 12×12 像素小画特别有灵气呢！" },
  { id = "BB79", residentId = "C01", cond = { chapter = "epilogue" }, prio = 86, act = "greet", bub = nil, txt = "回声音乐会虽然散场了，但《时光小筑年谱》只要你每天来散五分钟步，就会永远有新故事写上去。" },
  { id = "BB80", residentId = "C02", cond = { chapter = "epilogue" }, prio = 86, act = "hop_bounce", bub = nil, txt = "现在四个海岬全部打通啦，今天要不要一起骑薄荷单车去东山梯田看茶花、再坐摇橹船回老镇？" },
  { id = "BB81", residentId = "C03", cond = { chapter = "epilogue" }, prio = 86, act = "clap", bub = nil, txt = "全镇 26 件记忆碎片如果收集齐了，我也不会放烟花，顶多再给你严肃地拍五下爪子。" },
  { id = "BB82", residentId = "C04", cond = { chapter = "epilogue" }, prio = 86, act = "cheer", bub = nil, txt = "没有主线期限以后最快乐啦！我打算把 465 种食物味道全都做成迷你试吃盘摆满心愿广场！" },
  { id = "BB83", residentId = "C06", cond = { chapter = "epilogue" }, prio = 86, act = "wave", bub = nil, txt = "白昼号的船钟随时欢迎你来敲响，只要大家都在，这座月牙湾就是永远不用返航的港湾。" },
  { id = "BB84", residentId = "C08", cond = { chapter = "epilogue" }, prio = 86, act = "nod_tilt", bub = nil, txt = "所有的桥都修得笔直又顺滑——好吧，为了纪念小羊的自由涂鸦，我特许这面 12×12 小旗歪着飘。" },
  { id = "BB85", residentId = "C09", cond = { chapter = "epilogue" }, prio = 86, act = "paper_pet_squash", bub = nil, txt = "不管纸片小宠物“#petName#”以后跟着你走多远，记得每隔几天回时光石前拍一张新合照哦！" },
  { id = "BB86", residentId = "C07", cond = { chapter = "epilogue" }, prio = 86, act = "hop_bounce", bub = nil, txt = "邮局以后只寄‘慢慢来也没关系’的慢递明信片！今天你要给哪位怪友发一封呢？" },
}
local ruleCooldowns = {}
local customRules = {}

local function getHost()
  if runtimeScope ~= nil then
    local host = runtimeScope:GetRuntimeHostScript("narrative-host.lua")
    if host ~= nil then return host end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.narrativeHost or nil
end

local function isActionSafe(actionName)
  return type(actionName) == "string" and ALLOWED_ACTIONS[actionName] == true
end

function RegisterDialogueRule(rule)
  if type(rule) ~= "table" or type(rule.txt) ~= "string" then return false end
  table.insert(customRules, rule)
  return true
end

local function chooseRandom(arr)
  if type(arr) ~= "table" or #arr == 0 then return "" end
  return arr[math.random(1, #arr)]
end

-- Tracery 递归模板展开器（含玩家注入流行语/宠物名/像素旗名）
function ExpandTracery(input, overrides, depth)
  local d = depth or 0
  if d >= MaxTraceryDepth or type(input) ~= "string" then
    return tostring(input or "")
  end
  local host = getHost()
  local snap = host ~= nil and host.GetStateSnapshot() or nil

  local replaced = string.gsub(input, "#([A-Za-z0-9_]+)#", function(symbol)
    if overrides ~= nil and overrides[symbol] ~= nil then
      return tostring(overrides[symbol])
    end
    if symbol == "lingo" and snap ~= nil and snap.lingoPool ~= nil and #snap.lingoPool > 0 then
      return chooseRandom(snap.lingoPool)
    end
    if symbol == "petName" and snap ~= nil and snap.petName ~= nil then
      return tostring(snap.petName)
    end
    if symbol == "flagTitle" and snap ~= nil and snap.flagTitle ~= nil then
      return tostring(snap.flagTitle)
    end
    local pool = TRACERY_GRAMMAR[symbol]
    if pool ~= nil then
      return ExpandTracery(chooseRandom(pool), overrides, d + 1)
    end
    return symbol
  end)
  return replaced
end

local function evaluateRuleMatch(rule, residentId, facts, affection)
  if rule.residentId ~= "any" and rule.residentId ~= residentId then
    return false, 0
  end
  local cond = rule.cond or {}
  local matchCount = (rule.residentId == residentId) and 1 or 0
  for k, expected in pairs(cond) do
    if k == "affectionMin" then
      if (affection or 25) < expected then return false, 0 end
      matchCount = matchCount + 1
    else
      if facts[k] ~= expected then return false, 0 end
      matchCount = matchCount + 1
    end
  end
  return true, matchCount
end

-- 按最多命中条件数 -> 优先级 -> 冷却防复读选出最佳 Valve 黑板台词
function QueryDialogue(residentId, extraContext, mood)
  local host = getHost()
  local facts = {}
  if host ~= nil and type(host.GetAllFacts) == "function" then
    for k, v in pairs(host.GetAllFacts()) do
      facts[k] = v
    end
  end
  if type(extraContext) == "table" then
    for k, v in pairs(extraContext) do
      facts[k] = v
    end
  end
  local affection = host ~= nil and host.GetAffection(residentId) or 25
  local now = Time.time or 0.0

  local bestRule = nil
  local bestScore = -1

  local function scanList(list)
    for _, r in ipairs(list) do
      local lastAt = ruleCooldowns[r.id] or -9999.0
      if (now - lastAt) >= RuleCooldownSeconds then
        local ok, count = evaluateRuleMatch(r, residentId, facts, affection)
        if ok then
          local score = count * 1000 + (r.prio or 50)
          if score > bestScore then
            bestScore = score
            bestRule = r
          end
        end
      end
    end
  end

  scanList(customRules)
  scanList(BLACKBOARD_RULES)

  local rawText = "#gossipBit#"
  local act = "greet"
  local bub = nil
  if bestRule ~= nil then
    ruleCooldowns[bestRule.id] = now
    rawText = bestRule.txt
    act = isActionSafe(bestRule.act) and bestRule.act or "greet"
    if bestRule.bub ~= nil and isActionSafe(bestRule.bub) then
      bub = bestRule.bub
    end
  end

  local finalText = ExpandTracery(rawText, extraContext, 0)
  local voiceSeq = ComputeVoiceSequence(finalText, residentId, mood or "neutral")
  local voiceCue = (voiceSeq.voiceMode == "mech_tts") and "voice_mech" or "voice_soft"

  return {
    ruleId = bestRule ~= nil and bestRule.id or "FALLBACK_TRACERY",
    residentId = residentId,
    text = finalText,
    action = act,
    bubble = bub,
    voiceCue = isActionSafe(voiceCue) and voiceCue or "voice_soft",
    voiceSequence = voiceSeq,
  }
end

-- 零插件 Animalese / 机械音节 Pitch 实时调制参数生成器
function ComputeVoiceSequence(text, residentId, mood)
  local profile = VOICE_PROFILES[residentId] or { mode = "animalese", basePitch = 1.0, sizeOffset = 0.0, speed = 1.0 }
  local mode = profile.mode
  if DefaultVoiceMode == "animalese" or DefaultVoiceMode == "mech_tts" then
    mode = DefaultVoiceMode
  end
  local moodDelta = MOOD_PITCH_OFFSET[mood or "neutral"] or 0.0
  local syllables = {}
  local str = tostring(text or "")
  local byteIdx = 1
  local len = #str

  while byteIdx <= len do
    local b = string.byte(str, byteIdx)
    local charBytes = 1
    if b >= 240 then charBytes = 4
    elseif b >= 224 then charBytes = 3
    elseif b >= 192 then charBytes = 2
    end
    local token = string.sub(str, byteIdx, math.min(len, byteIdx + charBytes - 1))
    byteIdx = byteIdx + charBytes

    -- 跳过标点符号仅拉长停顿，保留“スキマ”呼吸间隔
    if token == " " or token == "，" or token == "。" or token == "、" or token == "！" or token == "？" then
      table.insert(syllables, {
        clipIndex = 0,
        pitch = 1.0,
        delay = (SyllableInterval * 1.4) / math.max(0.5, profile.speed),
        pause = true,
      })
    else
      local hash = (b * 31 + byteIdx * 17) % 16
      local clipIndex = (hash % 12) + 1
      local pitchJitter = ((hash - 7.5) / 7.5) * (mode == "mech_tts" and 0.04 or 0.14)
      local finalPitch = math.max(0.55, math.min(1.85, profile.basePitch + profile.sizeOffset + moodDelta + pitchJitter))
      table.insert(syllables, {
        clipIndex = clipIndex,
        pitch = finalPitch,
        delay = SyllableInterval / math.max(0.5, profile.speed),
        pause = false,
      })
    end
    if #syllables >= 48 then break end
  end

  return {
    voiceMode = mode,
    voiceCue = (mode == "mech_tts") and "voice_mech" or "voice_soft",
    syllableCount = #syllables,
    syllables = syllables,
  }
end

function GenerateIslandNews()
  local headline = ExpandTracery("#newsHeadline#", nil, 0)
  local host = getHost()
  if host ~= nil then
    host.SetFact("lastNews", headline)
  end
  return headline
end

function Start()
  math.randomseed(os.time())
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "blackboard-dialogue-engine 未取得 RuntimeScope", runtimeScopeReason)
  end
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.dialogueEngine = {
    QueryDialogue = QueryDialogue,
    ExpandTracery = ExpandTracery,
    ComputeVoiceSequence = ComputeVoiceSequence,
    GenerateIslandNews = GenerateIslandNews,
    RegisterDialogueRule = RegisterDialogueRule,
    IsActionAllowed = isActionSafe,
  }
  logger:info(string.format("黑板规则对话引擎就绪（内置规则=%d，白名单动作锁定）", #BLACKBOARD_RULES))
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.dialogueEngine = nil
  end
end
