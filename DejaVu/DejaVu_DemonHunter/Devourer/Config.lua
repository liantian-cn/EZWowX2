local addonName, addonTable             = ... -- 插件入口固定写法

-- Lua 原生函数
local insert                            = table.insert

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEMONHUNTER" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是恶魔猎手则停止
if currentSpec ~= 3 then return end -- 不是噬灭专精则停止

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs

-- 1. 恶魔之怒最大值配置
do
    local fury_max_config = Config("fury_max")
    insert(ConfigRows, {
        type = "slider",
        key = "fury_max",
        name = "最大恶魔之怒",
        tooltip = "设置识别器的最大能量参考值（通常为 100 或 120）",
        min_value = 100,
        max_value = 120,
        step = 10,
        default_value = 120,
        bind_config = fury_max_config,
    })

    local function InitFrame()
        -- 对应识别位置 x:55 y:12
        local fury_max_cell = Cell:New(55, 12)

        local function set_fury_max(value)
            -- 将配置值映射到 RGBA 输出，供外部程序读取
            fury_max_cell:setCellRGBA(value / 255)
        end

        fury_max_config:register_callback(set_fury_max)
        set_fury_max(fury_max_config:get_value() or 120) -- 初始化时根据当前配置值更新显示
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local dh_interrupt_mode = Config("dh_interrupt_mode")
    insert(ConfigRows, {
        type = "combo",
        key = "dh_interrupt_mode",
        name = "打断模式",
        tooltip = "选择打断模式",
        default_value = "blacklist",
        options = {
            { k = "blacklist", v = "使用黑名单" },
            { k = "all", v = "任意打断" }
        },
        bind_config = dh_interrupt_mode,
    })

    local function InitFrame()
        -- x:56 y:12
        -- 用途：显示噬灭恶魔猎手打断模式配置。
        -- 更新函数：set_dh_interrupt_mode
        local dh_interrupt_mode_cell = Cell:New(56, 12)

        -- 说明：根据打断模式配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_dh_interrupt_mode(value)
            if value == "blacklist" then
                dh_interrupt_mode_cell:setCellRGBA(255 / 255)
            else
                dh_interrupt_mode_cell:setCellRGBA(127 / 255)
            end
        end

        dh_interrupt_mode:register_callback(set_dh_interrupt_mode)

        set_dh_interrupt_mode(dh_interrupt_mode:get_value() or "blacklist")
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local phase_shift_threshold = Config("phase_shift_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "phase_shift_threshold",
        name = "开启减伤阈值", -- 修改名称
        tooltip = "当前生命值低于该百分比时, 使用疾影", -- 修改描述
        min_value = 0,
        max_value = 120,
        step = 5,
        default_value = 60, -- 设为您的目标值 72
        bind_config = phase_shift_threshold,
    })

    local function InitFrame()
        -- 保持坐标 x:57 y:12 不变，方便外部读取
        local phase_shift_threshold_cell = Cell:New(57, 12)

        -- 更新函数逻辑
        local function set_phase_shift_threshold(value)
            -- 将 0-100 的数值映射为颜色深度输出
            phase_shift_threshold_cell:setCellRGBA(value / 255)
        end

        phase_shift_threshold:register_callback(set_phase_shift_threshold)
        set_phase_shift_threshold(phase_shift_threshold:get_value() or 60)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local void_Ray_fury_overflow_threshold = Config("void_Ray_fury_overflow_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "void_Ray_fury_overflow_threshold",
        name = "虚空射线泄能阈值",
        tooltip = "当前恶魔之怒高于该值时, 使用虚空射线避免浪费",
        min_value = 0,
        max_value = 120,
        step = 10,
        default_value = 100,
        bind_config = void_Ray_fury_overflow_threshold,
    })

    local function InitFrame()
        -- x:58 y:12
        -- 用途：显示虚空射线泄能阈值配置。
        -- 更新函数：set_void_Ray_fury_overflow_threshold
        local void_Ray_fury_overflow_threshold_cell = Cell:New(58, 12)

        -- 说明：根据虚空射线泄能阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_void_Ray_fury_overflow_threshold(value)
            void_Ray_fury_overflow_threshold_cell:setCellRGBA(value / 255)
        end

        void_Ray_fury_overflow_threshold:register_callback(set_void_Ray_fury_overflow_threshold)

        set_void_Ray_fury_overflow_threshold(void_Ray_fury_overflow_threshold:get_value() or 100)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    local slider_enemy_health_threshold = Config("slider_enemy_health_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "slider_enemy_health_threshold",
        name = "收割血量阈值",
        tooltip = "当敌人生命值低于此值时, 就不会再使用坍缩之星，立即使用根除",
        min_value = 5,
        max_value = 30,
        step = 10,
        default_value = 15,
        bind_config = slider_enemy_health_threshold,
    })

    local function InitFrame()
        -- x:59 y:12
        -- 用途：显示坍缩之星血量阈值配置。
        -- 更新函数：set_slider_enemy_health_threshold
        local slider_enemy_health_threshold_cell = Cell:New(59, 12)

        -- 说明：根据坍缩之星血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_slider_enemy_health_threshold(value)
            slider_enemy_health_threshold_cell:setCellRGBA(value / 255)
        end

        slider_enemy_health_threshold:register_callback(set_slider_enemy_health_threshold)

        set_slider_enemy_health_threshold(slider_enemy_health_threshold:get_value() or 15)
    end
    insert(MartixInitFuncs, InitFrame)
end
