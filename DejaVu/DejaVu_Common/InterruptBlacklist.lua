local addonName, addonTable = ...

local pairs = pairs
local insert = table.insert -- 表插入

-- WoW 官方 API
local GetSpellTexture = C_Spell.GetSpellTexture
local GetSpellName = C_Spell.GetSpellName

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local COLOR = DejaVu.COLOR
local BadgeCell = DejaVu.BadgeCell
local MartixInitFuncs = DejaVu.MartixInitFuncs

-- 创建配置对象
local interrupt_blacklist = Config("interrupt_blacklist")      -- 驱散黑名单配置项
local MAX_COUNT = 19                                           -- 最大数量
local POS_X = 43                                               -- X轴位置
local POS_Y = 17                                               -- Y轴位置
local BADGE_COLOR = COLOR.SPELL_TYPE.ENEMY_SPELL_INTERRUPTIBLE -- 图标颜色

table.insert(ConfigRows, {
    type = "spell_list", -- 设置类型
    key = "interrupt_blacklist", -- 行标识
    name = "打断黑名单", -- 标题文本
    tooltip = "不可以自动打断的技能列表。", -- 提示信息
    default_value = { -- 默认技能集合
        [1254669] = true, -- 示例技能1
        [1258436] = true, -- 示例技能2
        [1248327] = true, -- 示例技能3
        [1262510] = true, -- 示例技能4
        [468962] = true, -- 示例技能5
        [1262526] = true, -- 示例技能6
    }, -- default_value 结束
    bind_config = interrupt_blacklist -- 绑定的配置对象
})

local function InitFrame()
    local cells = {}
    for i = 1, MAX_COUNT do         -- 预创建固定数量的槽位
        local x = POS_X - 2 + 2 * i -- 计算当前槽位 x 坐标
        local y = POS_Y             -- 当前槽位 y 坐标

        -- x:POS_X - 2 + 2 * i y:POS_Y
        -- 用途：显示打断黑名单中的法术图标。
        -- 更新函数：updateCell
        local icon = BadgeCell:New(x, y)
        insert(cells, icon)
    end

    -- 说明：根据打断黑名单配置刷新所有图标槽位。
    -- 依赖事件更新：无
    -- 依赖定时刷新：无
    local function updateCell(tableValue)
        local i = 1
        for spellID in pairs(tableValue) do
            if i > MAX_COUNT then
                break
            end

            local cell = cells[i]
            cell:setCell(GetSpellTexture(spellID), BADGE_COLOR, GetSpellName(spellID))
            i = i + 1
        end

        for j = i, MAX_COUNT do
            local cell = cells[j]
            cell:clearCell()
        end
    end

    interrupt_blacklist:register_callback(updateCell)

    updateCell(interrupt_blacklist:get_value() or {}) -- 初始化时根据当前配置值刷新图标槽位
end
insert(MartixInitFuncs, InitFrame)
