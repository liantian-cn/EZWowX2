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
local spell_stop_list = Config("spell_stop_list")                  -- 驱散黑名单配置项
local MAX_COUNT = 10                                               -- 最大数量
local POS_X = 43                                                   -- X轴位置
local POS_Y = 26                                                   -- Y轴位置
local BADGE_COLOR = COLOR.SPELL_TYPE.ENEMY_SPELL_NOT_INTERRUPTIBLE -- 哪些技能一定是无法打断的。

table.insert(ConfigRows, {
    type = "spell_list", -- 设置类型
    key = "spell_stop_list", -- 行标识
    name = "终止施法技能清单", -- 标题文本
    tooltip = "那些会打断施法的怪物技能", -- 提示信息
    default_value = { -- 默认技能集合
        [377004] = true, -- 示例技能1
    }, -- default_value 结束
    bind_config = spell_stop_list -- 绑定的配置对象
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

    -- 说明：根据终止施法技能清单配置刷新所有图标槽位。
    -- 依赖事件更新：无
    -- 依赖定时刷新：无
    local function updateCell(tableValue)
        tableValue = tableValue or {}
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

    spell_stop_list:register_callback(updateCell)

    updateCell(spell_stop_list:get_value() or {}) -- 初始化时根据当前配置值刷新图标槽位
end
insert(MartixInitFuncs, InitFrame)
