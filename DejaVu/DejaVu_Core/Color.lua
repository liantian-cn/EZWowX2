--[[
文件定位:




状态:
  draft
]]
-- 插件入口
local addonName, DejaVu_Core = ...

-- WoW 官方 API
local CreateColor = CreateColor

DejaVu_Core.COLOR = {
    RED = CreateColor(255 / 255, 0, 0, 1),                                          -- 红色
    GREEN = CreateColor(0, 255 / 255, 0, 1),                                        -- 绿色
    BLUE = CreateColor(0, 0, 255 / 255, 1),                                         -- 蓝色
    BLACK = CreateColor(0, 0, 0, 1),                                                -- 黑色
    WHITE = CreateColor(1, 1, 1, 1),                                                -- 白色
    TRANSPARENT = CreateColor(0, 0, 0, 0),                                          -- 透明
    SPELL_TYPE = {                                                                  -- 技能类型颜色表
        MAGIC = CreateColor(60 / 255, 100 / 255, 220 / 255, 1),                     -- 魔法
        CURSE = CreateColor(100 / 255, 0, 120 / 255, 1),                            -- 诅咒
        DISEASE = CreateColor(160 / 255, 120 / 255, 60 / 255, 1),                   -- 疾病
        POISON = CreateColor(154 / 255, 205 / 255, 50 / 255, 1),                    -- 中毒
        ENRAGE = CreateColor(230 / 255, 120 / 255, 20 / 255, 1),                    -- 激怒
        BLEED = CreateColor(80 / 255, 0, 20 / 255, 1),                              -- 流血
        DEBUFF_ON_FRIENDLY = CreateColor(255 / 255, 60 / 255, 60 / 255, 1),         -- 在友方身上的减益
        BUFF_ON_FRIENDLY = CreateColor(80 / 255, 220 / 255, 120 / 255, 1),          -- 在友方身上的增益
        PLAYER_SPELL = CreateColor(64 / 255, 158 / 255, 210 / 255, 1),              -- 友方施法
        ENEMY_SPELL_INTERRUPTIBLE = CreateColor(255 / 255, 255 / 255, 60 / 255, 1), -- 可打断
        ENEMY_SPELL_NOT_INTERRUPTIBLE = CreateColor(200 / 255, 0, 0, 1),            -- 不可打断
        DEBUFF_ON_ENEMY = CreateColor(105 / 255, 105 / 255, 210 / 255, 1),          -- 在敌方身上的减益
        NONE = CreateColor(0, 0, 0, 0),                                             -- 无
    },
    MARK_POINT = {                                                                  -- 标记点颜色表
        NEAR_BLACK_1 = CreateColor(15 / 255, 25 / 255, 20 / 255, 1),                -- 接近黑色
        NEAR_BLACK_2 = CreateColor(25 / 255, 15 / 255, 20 / 255, 1),                -- 接近黑色
    },
    C0 = CreateColor(0, 0, 0, 1),                                                   -- 黑色
    C100 = CreateColor(100 / 255, 100 / 255, 100 / 255, 1),                         -- 灰色
    C150 = CreateColor(150 / 255, 150 / 255, 150 / 255, 1),
    C200 = CreateColor(200 / 255, 200 / 255, 200 / 255, 1),
    C250 = CreateColor(250 / 255, 250 / 255, 250 / 255, 1),
    C255 = CreateColor(255 / 255, 255 / 255, 255 / 255, 1),
    ROLE = {                                                      -- 角色颜色表
        TANK = CreateColor(180 / 255, 80 / 255, 20 / 255, 1),     -- 坦克
        HEALER = CreateColor(120 / 255, 200 / 255, 255 / 255, 1), -- 治疗
        DAMAGER = CreateColor(230 / 255, 200 / 255, 50 / 255, 1), -- 伤害输出
        NONE = CreateColor(0, 0, 0, 1),                           -- 无角色
    },
    SPELL_BOOLEAN = {                                             -- 技能布尔值颜色表
        -- IS_USABLE = CreateColor(169 / 255, 208 / 255, 142 / 255, 1),     -- 可施放
        -- IS_KNOWN = CreateColor(0 / 255, 176 / 255, 80 / 255, 1),         -- 已知
        -- IS_HIGH_LIGHTED = CreateColor(0 / 255, 176 / 255, 240 / 255, 1), -- 高亮
        IS_USABLE = CreateColor(0, 1, 0, 1),                           -- 可施放
        IS_KNOWN = CreateColor(0, 1, 0, 1),                            -- 已知
        IS_HIGH_LIGHTED = CreateColor(0, 1, 0, 1),                     -- 高亮
    },
    CLASS = {                                                          -- 职业颜色表
        WARRIOR = CreateColor(199 / 255, 86 / 255, 36 / 255, 1),       -- 战士
        PALADIN = CreateColor(245 / 255, 140 / 255, 186 / 255, 1),     -- 圣骑士
        HUNTER = CreateColor(163 / 255, 203 / 255, 66 / 255, 1),       -- 猎人
        ROGUE = CreateColor(255 / 255, 245 / 255, 105 / 255, 1),       -- 潜行者
        PRIEST = CreateColor(196 / 255, 207 / 255, 207 / 255, 1),      -- 牧师
        DEATHKNIGHT = CreateColor(125 / 255, 125 / 255, 215 / 255, 1), -- 死亡骑士
        SHAMAN = CreateColor(64 / 255, 148 / 255, 255 / 255, 1),       -- 萨满祭司
        MAGE = CreateColor(64 / 255, 158 / 255, 210 / 255, 1),         -- 法师
        WARLOCK = CreateColor(105 / 255, 105 / 255, 210 / 255, 1),     -- 术士
        MONK = CreateColor(0 / 255, 255 / 255, 150 / 255, 1),          -- 武僧
        DRUID = CreateColor(255 / 255, 125 / 255, 10 / 255, 1),        -- 德鲁伊
        DEMONHUNTER = CreateColor(163 / 255, 48 / 255, 201 / 255, 1),  -- 恶魔猎手
        EVOKER = CreateColor(108 / 255, 191 / 255, 246 / 255, 1)       -- 唤魔师
    },
    STATUS_BOOLEAN = {
        -- EXISTS = CreateColor(228 / 255, 70 / 255, 44 / 255, 1),                    -- 存在
        -- IS_ALIVE = CreateColor(61 / 255, 143 / 255, 141 / 255, 1),                 -- 存活
        -- IS_ENEMY = CreateColor(68 / 255, 157 / 255, 209 / 255, 1),                 -- 敌对
        -- CAN_ATTACK = CreateColor(90 / 255, 162 / 255, 73 / 255, 1),                -- 可攻击
        -- IS_IN_RANGED_RANGE = CreateColor(83 / 255, 171 / 255, 67 / 255, 1),        -- 在远程范围内
        -- IS_IN_MELEE_RANGE = CreateColor(141 / 255, 98 / 255, 124 / 255, 1),        -- 在近战范围内
        -- IS_IN_COMBAT = CreateColor(18 / 255, 166 / 255, 115 / 255, 1),             -- 在战斗中
        -- IS_TARGET = CreateColor(122 / 255, 35 / 255, 253 / 255, 1),                -- 是当前目标                                                        -- 玩家状态颜色表
        -- IS_MOVING = CreateColor(242 / 255, 197 / 255, 44 / 255, 1),                -- 在移动
        -- IS_MOUNTED = CreateColor(104 / 255, 198 / 255, 122 / 255, 1),              -- 在坐骑
        -- IS_EMPOWERING = CreateColor(197 / 255, 87 / 255, 210 / 255, 1),            -- 在蓄力
        -- USE_MOUSE = CreateColor(211 / 255, 185 / 255, 37 / 255, 1),                -- 正在使用鼠标
        -- IS_CHAT_INPUT_ACTIVE = CreateColor(220 / 255, 105 / 255, 202 / 255, 1),    -- 正在聊天输入
        -- IS_SPELL_TARGETING = CreateColor(232 / 255, 223 / 255, 83 / 255, 1),       -- 正在选择目标
        -- IS_IN_GROUP_OR_RAID = CreateColor(138 / 255, 63 / 255, 22 / 255, 1),       -- 在队伍/团队中
        -- HAS_BIG_DEFENSE = CreateColor(245 / 255, 54 / 255, 187 / 255, 1),          -- 有大减伤
        -- HAS_DISPELLABLE_DEBUFF = CreateColor(179 / 255, 75 / 255, 127 / 255, 1),   -- 有可驱散减益
        -- TRINKET_1_USABLE = CreateColor(15 / 255, 27 / 255, 193 / 255, 1),          -- 饰品 1 可用
        -- TRINKET_2_USABLE = CreateColor(76 / 255, 60 / 255, 160 / 255, 1),          -- 饰品 2 可用
        -- HEALTHSTONE_USABLE = CreateColor(22 / 255, 233 / 255, 229 / 255, 1),       -- 治疗石可用
        -- HEALING_POTION_USABLE = CreateColor(97 / 255, 165 / 255, 227 / 255, 1),    -- 治疗药水可用
        -- IS_WAITING_DELAYED_UPDATE = CreateColor(122 / 255, 238 / 255, 1 / 255, 1), -- 在等待延迟更新
        EXISTS = CreateColor(0, 1, 0, 1),                    -- 存在
        IS_ALIVE = CreateColor(0, 1, 0, 1),                  -- 存活
        IS_ENEMY = CreateColor(0, 1, 0, 1),                  -- 敌对
        CAN_ATTACK = CreateColor(0, 1, 0, 1),                -- 可攻击
        IS_IN_RANGED_RANGE = CreateColor(0, 1, 0, 1),        -- 在远程范围内
        IS_IN_MELEE_RANGE = CreateColor(0, 1, 0, 1),         -- 在近战范围内
        IS_IN_COMBAT = CreateColor(0, 1, 0, 1),              -- 在战斗中
        IS_TARGET = CreateColor(0, 1, 0, 1),                 -- 是当前目标                                                        -- 玩家状态颜色表
        IS_MOVING = CreateColor(0, 1, 0, 1),                 -- 在移动
        IS_MOUNTED = CreateColor(0, 1, 0, 1),                -- 在坐骑
        IS_EMPOWERING = CreateColor(0, 1, 0, 1),             -- 在蓄力
        USE_MOUSE = CreateColor(0, 1, 0, 1),                 -- 正在使用鼠标
        IS_CHAT_INPUT_ACTIVE = CreateColor(0, 1, 0, 1),      -- 正在聊天输入
        IS_SPELL_TARGETING = CreateColor(0, 1, 0, 1),        -- 正在选择目标
        IS_IN_GROUP_OR_RAID = CreateColor(0, 1, 0, 1),       -- 在队伍/团队中
        HAS_BIG_DEFENSE = CreateColor(0, 1, 0, 1),           -- 有大减伤
        HAS_DISPELLABLE_DEBUFF = CreateColor(0, 1, 0, 1),    -- 有可驱散减益
        TRINKET_1_USABLE = CreateColor(0, 1, 0, 1),          -- 饰品 1 可用
        TRINKET_2_USABLE = CreateColor(0, 1, 0, 1),          -- 饰品 2 可用
        HEALTHSTONE_USABLE = CreateColor(0, 1, 0, 1),        -- 治疗石可用
        HEALING_POTION_USABLE = CreateColor(0, 1, 0, 1),     -- 治疗药水可用
        IS_WAITING_DELAYED_UPDATE = CreateColor(0, 1, 0, 1), -- 在等待延迟更新
    }
}
