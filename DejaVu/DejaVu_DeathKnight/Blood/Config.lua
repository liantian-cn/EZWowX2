local addonName, addonTable             = ... -- 插件入口固定写法

-- Lua 原生函数
local insert                            = table.insert

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEATHKNIGHT" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是死亡骑士则停止
if currentSpec ~= 1 then return end -- 不是鲜血专精则停止

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


do
    local runic_power_max = Config("runic_power_max")
    insert(ConfigRows, {
        type = "slider",
        key = "runic_power_max",
        name = "最大符文能量",
        tooltip = "设置最大符文能量值",
        min_value = 100,
        max_value = 140,
        step = 5,
        default_value = 125,
        bind_config = runic_power_max,
    })

    local function InitFrame()
        -- x:55 y:12
        -- 用途：显示最大符文能量配置。
        -- 更新函数：set_runic_power_max
        local runic_power_max_cell = Cell:New(55, 12)

        -- 说明：根据最大符文能量配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_runic_power_max(value)
            runic_power_max_cell:setCellRGBA(value / 255)
        end

        runic_power_max:register_callback(set_runic_power_max)

        set_runic_power_max(runic_power_max:get_value() or 125)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local dk_interrupt_mode = Config("dk_interrupt_mode")
    insert(ConfigRows, {
        type = "combo",
        key = "dk_interrupt_mode",
        name = "打断模式",
        tooltip = "选择打断模式",
        default_value = "blacklist",
        options = {
            { k = "blacklist", v = "使用黑名单" },
            { k = "all", v = "任意打断" }
        },
        bind_config = dk_interrupt_mode,
    })

    local function InitFrame()
        -- x:56 y:12
        -- 用途：显示鲜血死亡骑士打断模式配置。
        -- 更新函数：set_dk_interrupt_mode
        local dk_interrupt_mode_cell = Cell:New(56, 12)

        -- 说明：根据打断模式配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_dk_interrupt_mode(value)
            if value == "blacklist" then
                dk_interrupt_mode_cell:setCellRGBA(255 / 255)
            else
                dk_interrupt_mode_cell:setCellRGBA(127 / 255)
            end
        end

        dk_interrupt_mode:register_callback(set_dk_interrupt_mode)

        set_dk_interrupt_mode(dk_interrupt_mode:get_value() or "blacklist")
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local blood_death_strike_health_threshold = Config("blood_death_strike_health_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "blood_death_strike_health_threshold",
        name = "死亡打击生命值阈值",
        tooltip = "当前生命值低于该百分比时, 使用死亡打击",
        min_value = 40,
        max_value = 70,
        step = 5,
        default_value = 55,
        bind_config = blood_death_strike_health_threshold,
    })

    local function InitFrame()
        -- x:57 y:12
        -- 用途：显示死亡打击生命值阈值配置。
        -- 更新函数：set_blood_death_strike_health_threshold
        local blood_death_strike_health_threshold_cell = Cell:New(57, 12)

        -- 说明：根据死亡打击生命值阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_blood_death_strike_health_threshold(value)
            blood_death_strike_health_threshold_cell:setCellRGBA(value / 255)
        end

        blood_death_strike_health_threshold:register_callback(set_blood_death_strike_health_threshold)

        set_blood_death_strike_health_threshold(blood_death_strike_health_threshold:get_value() or 55)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local blood_death_strike_runic_power_overflow_threshold = Config("blood_death_strike_runic_power_overflow_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "blood_death_strike_runic_power_overflow_threshold",
        name = "死亡打击泄能阈值",
        tooltip = "当前符文能量高于该值时, 使用死亡打击避免浪费",
        min_value = 80,
        max_value = 120,
        step = 10,
        default_value = 100,
        bind_config = blood_death_strike_runic_power_overflow_threshold,
    })

    local function InitFrame()
        -- x:58 y:12
        -- 用途：显示死亡打击泄能阈值配置。
        -- 更新函数：set_blood_death_strike_runic_power_overflow_threshold
        local blood_death_strike_runic_power_overflow_threshold_cell = Cell:New(58, 12)

        -- 说明：根据死亡打击泄能阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_blood_death_strike_runic_power_overflow_threshold(value)
            blood_death_strike_runic_power_overflow_threshold_cell:setCellRGBA(value / 255)
        end

        blood_death_strike_runic_power_overflow_threshold:register_callback(set_blood_death_strike_runic_power_overflow_threshold)

        set_blood_death_strike_runic_power_overflow_threshold(blood_death_strike_runic_power_overflow_threshold:get_value() or 100)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local reaper_mark_health_threshold = Config("reaper_mark_health_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "reaper_mark_health_threshold",
        name = "死神印记血量阈值",
        tooltip = "当敌人生命值低于此值时, 就不会再使用死神印记",
        min_value = 0,
        max_value = 40,
        step = 10,
        default_value = 20,
        bind_config = reaper_mark_health_threshold,
    })

    local function InitFrame()
        -- x:59 y:12
        -- 用途：显示死神印记血量阈值配置。
        -- 更新函数：set_reaper_mark_health_threshold
        local reaper_mark_health_threshold_cell = Cell:New(59, 12)

        -- 说明：根据死神印记血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_reaper_mark_health_threshold(value)
            reaper_mark_health_threshold_cell:setCellRGBA(value / 255)
        end

        reaper_mark_health_threshold:register_callback(set_reaper_mark_health_threshold)

        set_reaper_mark_health_threshold(reaper_mark_health_threshold:get_value() or 20)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local dancing_rune_mode = Config("dancing_rune_mode")
    insert(ConfigRows, {
        type = "combo",
        key = "dancing_rune_mode",
        name = "符文刃舞模式",
        tooltip = "手动模式: 完全不施放符文刃舞\n爆发模式: 仅在爆发阶段施放符文刃舞\n战斗时间模式: 根据战斗时间，开开怪期间自动施放符文刃舞。",
        default_value = "manual",
        options = {
            { k = "manual", v = "手动" },
            { k = "burst_mode", v = "爆发模式" },
            { k = "combat_mode", v = "战斗时间模式" }
        },
        bind_config = dancing_rune_mode,
    })

    local function InitFrame()
        -- x:60 y:12
        -- 用途：显示符文刃舞模式配置。
        -- 更新函数：set_dancing_rune_mode
        local dancing_rune_mode_cell = Cell:New(60, 12)

        -- 说明：根据符文刃舞模式配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_dancing_rune_mode(value)
            if value == "manual" then
                dancing_rune_mode_cell:setCellRGBA(255 / 255)
            elseif value == "burst_mode" then
                dancing_rune_mode_cell:setCellRGBA(127 / 255)
            else
                dancing_rune_mode_cell:setCellRGBA(0 / 255)
            end
        end

        dancing_rune_mode:register_callback(set_dancing_rune_mode)

        set_dancing_rune_mode(dancing_rune_mode:get_value())
    end
    insert(MartixInitFuncs, InitFrame)
end
