local addonName, addonTable             = ... -- 插件入口固定写法

-- Lua 原生函数
local insert                            = table.insert
-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DRUID" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是德鲁伊则停止
if currentSpec ~= 3 then return end -- 不是守护专精则停止

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


do
    local guardian_aoe_enemy_count = Config("guardian_aoe_enemy_count")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_aoe_enemy_count",
        name = "AOE敌人数量",
        tooltip = "设置判定为AOE条件的敌人数量",
        min_value = 2,
        max_value = 10,
        step = 1,
        default_value = 4,
        bind_config = guardian_aoe_enemy_count,
    })

    local function InitFrame()
        -- x:55 y:12
        -- 用途：显示守护德鲁伊 AOE 敌人数量阈值配置。
        -- 更新函数：set_guardian_aoe_enemy_count
        local guardian_aoe_enemy_count_cell = Cell:New(55, 12)

        -- 说明：根据 AOE 敌人数量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_aoe_enemy_count(value)
            guardian_aoe_enemy_count_cell:setCellRGBA(value * 10 / 255)
        end

        guardian_aoe_enemy_count:register_callback(set_guardian_aoe_enemy_count)

        set_guardian_aoe_enemy_count(guardian_aoe_enemy_count:get_value() or 4)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_opener_time = Config("guardian_opener_time")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_opener_time",
        name = "起手时间判定",
        tooltip = "即脱离战斗后多长时间内再次进入战斗时认为是起手阶段",
        min_value = 5,
        max_value = 45,
        step = 5,
        default_value = 10,
        bind_config = guardian_opener_time,
    })
    local function InitFrame()
        -- x:56 y:12
        -- 用途：显示守护德鲁伊起手时间判定配置。
        -- 更新函数：set_guardian_opener_time
        local guardian_opener_time_cell = Cell:New(56, 12)

        -- 说明：根据起手时间判定配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_opener_time(value)
            guardian_opener_time_cell:setCellRGBA(value / 255)
        end

        guardian_opener_time:register_callback(set_guardian_opener_time)

        set_guardian_opener_time(guardian_opener_time:get_value() or 10)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_frenzied_regeneration_threshold = Config("guardian_frenzied_regeneration_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_frenzied_regeneration_threshold",
        name = "狂暴回复阈值",
        tooltip = "当玩家生命值低于该值时优先使用狂暴回复",
        min_value = 30,
        max_value = 70,
        step = 2,
        default_value = 50,
        bind_config = guardian_frenzied_regeneration_threshold,
    })

    local function InitFrame()
        -- x:57 y:12
        -- 用途：显示狂暴回复生命值阈值配置。
        -- 更新函数：set_guardian_frenzied_regeneration_threshold
        local guardian_frenzied_regeneration_threshold_cell = Cell:New(57, 12)

        -- 说明：根据狂暴回复生命值阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_frenzied_regeneration_threshold(value)
            guardian_frenzied_regeneration_threshold_cell:setCellRGBA(value / 255)
        end

        guardian_frenzied_regeneration_threshold:register_callback(set_guardian_frenzied_regeneration_threshold)

        set_guardian_frenzied_regeneration_threshold(guardian_frenzied_regeneration_threshold:get_value() or 50)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_barkskin_threshold = Config("guardian_barkskin_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_barkskin_threshold",
        name = "树皮阈值",
        tooltip = "当玩家生命值低于该值时优先使用树皮术",
        min_value = 20,
        max_value = 60,
        step = 2,
        default_value = 40,
        bind_config = guardian_barkskin_threshold,
    })

    local function InitFrame()
        -- x:58 y:12
        -- 用途：显示树皮术生命值阈值配置。
        -- 更新函数：set_guardian_barkskin_threshold
        local guardian_barkskin_threshold_cell = Cell:New(58, 12)

        -- 说明：根据树皮术生命值阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_barkskin_threshold(value)
            guardian_barkskin_threshold_cell:setCellRGBA(value / 255)
        end

        guardian_barkskin_threshold:register_callback(set_guardian_barkskin_threshold)

        set_guardian_barkskin_threshold(guardian_barkskin_threshold:get_value() or 40)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_survival_instincts_threshold = Config("guardian_survival_instincts_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_survival_instincts_threshold",
        name = "生存本能阈值",
        tooltip = "当玩家生命值低于该值时优先使用生存本能",
        min_value = 10,
        max_value = 50,
        step = 2,
        default_value = 30,
        bind_config = guardian_survival_instincts_threshold,
    })

    local function InitFrame()
        -- x:59 y:12
        -- 用途：显示生存本能生命值阈值配置。
        -- 更新函数：set_guardian_survival_instincts_threshold
        local guardian_survival_instincts_threshold_cell = Cell:New(59, 12)

        -- 说明：根据生存本能生命值阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_survival_instincts_threshold(value)
            guardian_survival_instincts_threshold_cell:setCellRGBA(value / 255)
        end

        guardian_survival_instincts_threshold:register_callback(set_guardian_survival_instincts_threshold)

        set_guardian_survival_instincts_threshold(guardian_survival_instincts_threshold:get_value() or 30)
    end
    insert(MartixInitFuncs, InitFrame)
end

-- do
--     local guardian_rage_overflow_threshold = Config("guardian_rage_overflow_threshold")
--     insert(ConfigRows, {
--         type = "slider",
--         key = "guardian_rage_overflow_threshold",
--         name = "怒气溢出阈值",
--         tooltip = "高于该怒气时，不再使用攒怒技能。",
--         min_value = 60,
--         max_value = 120,
--         step = 5,
--         default_value = 100,
--         bind_config = guardian_rage_overflow_threshold,
--     })

--     local function InitFrame()
--         -- x:60 y:12
--         -- 用途：显示怒气溢出阈值配置。
--         -- 更新函数：set_guardian_rage_overflow_threshold
--         local guardian_rage_overflow_threshold_cell = Cell:New(60, 12)

--         -- 说明：根据怒气溢出阈值配置更新显示强度。
--         -- 依赖事件更新：无
--         -- 依赖定时刷新：无
--         local function set_guardian_rage_overflow_threshold(value)
--             guardian_rage_overflow_threshold_cell:setCellRGBA(value / 255)
--         end

--         guardian_rage_overflow_threshold:register_callback(set_guardian_rage_overflow_threshold)

--         set_guardian_rage_overflow_threshold(guardian_rage_overflow_threshold:get_value() or 100)
--     end
--     insert(MartixInitFuncs, InitFrame)
-- end

-- do
-- local guardian_rage_maul_threshold = Config("guardian_rage_maul_threshold")
-- insert(ConfigRows, {
--     type = "slider",
--     key = "guardian_rage_maul_threshold",
--     name = "重殴怒气下限",
--     tooltip = "当玩家怒气高于该值时，才会使用重殴泄怒",
--     min_value = 90,
--     max_value = 130,
--     step = 5,
--     default_value = 120,
--     bind_config = guardian_rage_maul_threshold,
-- })

-- local function InitFrame()
--     -- x:61 y:12
--     -- 用途：显示重殴怒气下限配置。
--     -- 更新函数：set_guardian_rage_maul_threshold
--     local guardian_rage_maul_threshold_cell = Cell:New(61, 12)

--     -- 说明：根据重殴怒气下限配置更新显示强度。
--     -- 依赖事件更新：无
--     -- 依赖定时刷新：无
--     local function set_guardian_rage_maul_threshold(value)
--         guardian_rage_maul_threshold_cell:setCellRGBA(value / 255)
--     end

--     guardian_rage_maul_threshold:register_callback(set_guardian_rage_maul_threshold)

--     set_guardian_rage_maul_threshold(guardian_rage_maul_threshold:get_value() or 120)
-- end
-- insert(MartixInitFuncs, InitFrame)
-- end

do
    local guardian_interrupt_logic = Config("guardian_interrupt_logic")
    insert(ConfigRows, {
        type = "combo",
        key = "guardian_interrupt_logic",
        name = "打断逻辑",
        tooltip = "选择打断逻辑",
        default_value = "blacklist",
        options = {
            { k = "blacklist", v = "使用黑名单" },
            { k = "all", v = "任意打断" }
        },
        bind_config = guardian_interrupt_logic,
    })

    local function InitFrame()
        -- x:62 y:12
        -- 用途：显示守护德鲁伊打断逻辑配置。
        -- 更新函数：set_guardian_interrupt_logic
        local guardian_interrupt_logic_cell = Cell:New(62, 12)

        -- 说明：根据打断逻辑配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_interrupt_logic(value)
            if value == "blacklist" then
                guardian_interrupt_logic_cell:setCellRGBA(255 / 255)
            else
                guardian_interrupt_logic_cell:setCellRGBA(127 / 255)
            end
        end

        guardian_interrupt_logic:register_callback(set_guardian_interrupt_logic)

        set_guardian_interrupt_logic(guardian_interrupt_logic:get_value() or "blacklist")
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_incarnation_logic = Config("guardian_incarnation_logic")
    insert(ConfigRows, {
        type = "combo",
        key = "guardian_incarnation_logic",
        name = "化身逻辑",
        tooltip = "手动模式: 完全不施放化身：乌索克的守护者\n爆发模式: 仅在爆发阶段施放化身：乌索克的守护者\n战斗时间模式: 根据战斗时间，在开怪期间自动施放化身：乌索克的守护者。",
        default_value = "burst_mode",
        options = {
            { k = "manual", v = "手动" },
            { k = "burst_mode", v = "爆发模式" },
            { k = "combat_mode", v = "战斗时间模式" }
        },
        bind_config = guardian_incarnation_logic,
    })

    local function InitFrame()
        -- x:63 y:12
        -- 用途：显示化身逻辑配置。
        -- 更新函数：set_guardian_incarnation_logic
        local guardian_incarnation_logic_cell = Cell:New(63, 12)

        -- 说明：根据化身逻辑配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_incarnation_logic(value)
            if value == "manual" then
                guardian_incarnation_logic_cell:setCellRGBA(255 / 255)
            elseif value == "burst_mode" then
                guardian_incarnation_logic_cell:setCellRGBA(127 / 255)
            else
                guardian_incarnation_logic_cell:setCellRGBA(0 / 255)
            end
        end

        guardian_incarnation_logic:register_callback(set_guardian_incarnation_logic)

        set_guardian_incarnation_logic(guardian_incarnation_logic:get_value() or "burst_mode")
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_ironfur_logic = Config("guardian_ironfur_logic")
    insert(ConfigRows, {
        type = "combo",
        key = "guardian_ironfur_logic",
        name = "铁鬃逻辑",
        tooltip = "保持1层: 实际铁鬃覆盖1-2层\n保持2层: 实际铁鬃覆盖1-3层\n无限堆叠: 除了保留狂暴回复的怒气外，全部打铁鬃。",
        default_value = "two",
        options = {
            { k = "bypass", v = "优先毁灭" },
            { k = "one", v = "保持1层" },
            { k = "two", v = "保持2层" },
            { k = "more", v = "无限堆叠" }
        },
        bind_config = guardian_ironfur_logic,
    })

    local function InitFrame()
        -- x:64 y:12
        -- 用途：显示铁鬃逻辑配置。
        -- 更新函数：set_guardian_ironfur_logic
        local guardian_ironfur_logic_cell = Cell:New(64, 12)

        -- 说明：根据铁鬃逻辑配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_ironfur_logic(value)
            if value == "one" then
                guardian_ironfur_logic_cell:setCellRGBA(127 / 255)
            elseif value == "two" then
                guardian_ironfur_logic_cell:setCellRGBA(63 / 255)
            elseif value == "bypass" then
                guardian_ironfur_logic_cell:setCellRGBA(191 / 255)
            else
                guardian_ironfur_logic_cell:setCellRGBA(0 / 255)
            end
        end

        guardian_ironfur_logic:register_callback(set_guardian_ironfur_logic)

        set_guardian_ironfur_logic(guardian_ironfur_logic:get_value() or "bypass")
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local guardian_rage_limit = Config("guardian_rage_limit")
    insert(ConfigRows, {
        type = "slider",
        key = "guardian_rage_limit",
        name = "怒气上限",
        tooltip = "当前的怒气上限, 这点将影响Terminal的计算",
        min_value = 100,
        max_value = 140,
        step = 5,
        default_value = 120,
        bind_config = guardian_rage_limit,
    })

    local function InitFrame()
        -- x:65 y:12
        -- 用途：显示怒气上限配置。
        -- 更新函数：set_guardian_rage_limit
        local guardian_rage_limit_cell = Cell:New(65, 12)

        -- 说明：根据怒气上限配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_guardian_rage_limit(value)
            guardian_rage_limit_cell:setCellRGBA(value / 255)
        end

        guardian_rage_limit:register_callback(set_guardian_rage_limit)

        set_guardian_rage_limit(guardian_rage_limit:get_value() or 120)
    end
    insert(MartixInitFuncs, InitFrame)
end
