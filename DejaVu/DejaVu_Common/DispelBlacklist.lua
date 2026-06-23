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

-- 创建配置对象
local dispel_blacklist = Config("dispel_blacklist") -- 驱散黑名单配置项
local MAX_COUNT = 10                                -- 最大数量
local POS_X = 64                                    -- X轴位置
local POS_Y = 15                                    -- Y轴位置
local BADGE_COLOR = COLOR.SPELL_TYPE.MAGIC          -- 图标颜色
local MartixInitFuncs = DejaVu.MartixInitFuncs

table.insert(ConfigRows, {
    type = "spell_list", -- 设置类型
    key = "dispel_blacklist", -- 行标识
    name = "驱散黑名单", -- 标题文本
    tooltip = "不可以自动驱散的减益效果列表。", -- 提示信息
    default_value = { -- 默认技能集合
        [1284627] = true, -- 魔导师平台  幽影裂片
    }, -- default_value 结束
    bind_config = dispel_blacklist -- 绑定的配置对象
})
local function InitFrame()
    local cells = {}
    for i = 1, MAX_COUNT do         -- 预创建固定数量的槽位
        local x = POS_X - 2 + 2 * i -- 计算当前槽位 x 坐标
        local y = POS_Y             -- 当前槽位 y 坐标

        -- x:POS_X - 2 + 2 * i y:POS_Y
        -- 用途：显示驱散黑名单中的减益图标。
        -- 更新函数：updateCell
        local icon = BadgeCell:New(x, y)
        insert(cells, icon)
    end

    -- 说明：根据驱散黑名单配置刷新所有图标槽位。
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

    dispel_blacklist:register_callback(updateCell)

    updateCell(dispel_blacklist:get_value() or {}) -- 初始化时根据当前配置值刷新图标槽位
end
insert(MartixInitFuncs, InitFrame)
