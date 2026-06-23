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
if currentSpec ~= 4 then return end -- 不是恢复专精则停止

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs

-- 全局变量。设置窗体数不够，这些修改较少的，放在变量里。
local WILD_GROWTH_COUNT_THRESHOLD = 2





do
    -- x:55 y:12
    -- 铁木树皮血量 min:30 max:70 default:50 step:5
    -- 对低于该血量的非坦克玩家使用铁木树皮的阈值。\n 针对坦克玩家，请手动释放。
    local restoration_ironbark_hp_threshold = Config("restoration_ironbark_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_ironbark_hp_threshold",
        name = "铁木树皮血量",
        tooltip = "对低于该血量的非坦克玩家使用铁木树皮的阈值。\n针对坦克玩家，请手动释放。",
        min_value = 30,
        max_value = 70,
        step = 5,
        default_value = 50,
        bind_config = restoration_ironbark_hp_threshold,
    })

    local function InitFrame()
        -- x:55 y:12
        -- 用途：显示铁木树皮血量阈值配置。
        -- 更新函数：set_restoration_ironbark_hp_threshold
        local restoration_ironbark_hp_threshold_cell = Cell:New(55, 12)

        -- 说明：根据铁木树皮血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_ironbark_hp_threshold(value)
            restoration_ironbark_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_ironbark_hp_threshold:register_callback(set_restoration_ironbark_hp_threshold)
        set_restoration_ironbark_hp_threshold(restoration_ironbark_hp_threshold:get_value() or 50)
    end
    insert(MartixInitFuncs, InitFrame)
end
do
    -- x:56 y:12
    -- 树皮术血量 min:40 max:90 default:65 step:5
    -- 对自己使用树皮术的阈值。
    local restoration_barkskin_hp_threshold = Config("restoration_barkskin_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_barkskin_hp_threshold",
        name = "树皮术血量",
        tooltip = "对自己使用树皮术的阈值。",
        min_value = 40,
        max_value = 90,
        step = 5,
        default_value = 65,
        bind_config = restoration_barkskin_hp_threshold,
    })

    local function InitFrame()
        -- x:56 y:12
        -- 用途：显示树皮术血量阈值配置。
        -- 更新函数：set_restoration_barkskin_hp_threshold
        local restoration_barkskin_hp_threshold_cell = Cell:New(56, 12)

        -- 说明：根据树皮术血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_barkskin_hp_threshold(value)
            restoration_barkskin_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_barkskin_hp_threshold:register_callback(set_restoration_barkskin_hp_threshold)
        set_restoration_barkskin_hp_threshold(restoration_barkskin_hp_threshold:get_value() or 65)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:57 y:12
    -- 万灵队伍血量 min:40 max:80 default:60 step:5
    -- 当队伍平均血量低于该值时，使用万灵
    local restoration_convoke_party_hp_threshold = Config("restoration_convoke_party_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_convoke_party_hp_threshold",
        name = "万灵队伍血量",
        tooltip = "当队伍平均血量低于该值时，使用万灵",
        min_value = 40,
        max_value = 80,
        step = 5,
        default_value = 60,
        bind_config = restoration_convoke_party_hp_threshold,
    })

    local function InitFrame()
        -- x:57 y:12
        -- 用途：显示万灵队伍血量阈值配置。
        -- 更新函数：set_restoration_convoke_party_hp_threshold
        local restoration_convoke_party_hp_threshold_cell = Cell:New(57, 12)

        -- 说明：根据万灵队伍血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_convoke_party_hp_threshold(value)
            restoration_convoke_party_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_convoke_party_hp_threshold:register_callback(set_restoration_convoke_party_hp_threshold)
        set_restoration_convoke_party_hp_threshold(restoration_convoke_party_hp_threshold:get_value() or 60)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:58 y:12
    -- 万灵单体血量 min:20 max:40 default:25 step:5
    -- 当某人血量低于该值时，使用万灵
    local restoration_convoke_single_hp_threshold = Config("restoration_convoke_single_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_convoke_single_hp_threshold",
        name = "万灵单体血量",
        tooltip = "当某人血量低于该值时，使用万灵",
        min_value = 20,
        max_value = 40,
        step = 5,
        default_value = 25,
        bind_config = restoration_convoke_single_hp_threshold,
    })

    local function InitFrame()
        -- x:58 y:12
        -- 用途：显示万灵单体血量阈值配置。
        -- 更新函数：set_restoration_convoke_single_hp_threshold
        local restoration_convoke_single_hp_threshold_cell = Cell:New(58, 12)

        -- 说明：根据万灵单体血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_convoke_single_hp_threshold(value)
            restoration_convoke_single_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_convoke_single_hp_threshold:register_callback(set_restoration_convoke_single_hp_threshold)
        set_restoration_convoke_single_hp_threshold(restoration_convoke_single_hp_threshold:get_value() or 25)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:59 y:12
    -- 野性成长血量 min:75 max:95 default:95 step:5
    -- 当至少{WILD_GROWTH_COUNT_THRESHOLD}个玩家的血量低于该值时，使用野性成长。
    local restoration_wild_growth_hp_threshold = Config("restoration_wild_growth_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_wild_growth_hp_threshold",
        name = "野性成长血量",
        tooltip = "当至少" .. WILD_GROWTH_COUNT_THRESHOLD .. "个玩家的血量低于该值时，使用野性成长。",
        min_value = 75,
        max_value = 95,
        step = 5,
        default_value = 95,
        bind_config = restoration_wild_growth_hp_threshold,
    })

    local function InitFrame()
        -- x:59 y:12
        -- 用途：显示野性成长血量阈值配置。
        -- 更新函数：set_restoration_wild_growth_hp_threshold
        local restoration_wild_growth_hp_threshold_cell = Cell:New(59, 12)

        -- 说明：根据野性成长血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_wild_growth_hp_threshold(value)
            restoration_wild_growth_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_wild_growth_hp_threshold:register_callback(set_restoration_wild_growth_hp_threshold)
        set_restoration_wild_growth_hp_threshold(restoration_wild_growth_hp_threshold:get_value() or 95)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:60 y:12
    -- 宁静队血 min:40 max:70 default:50 step:5
    -- 队伍平均血量低于该值时，使用宁静。
    local restoration_tranquility_party_hp_threshold = Config("restoration_tranquility_party_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_tranquility_party_hp_threshold",
        name = "宁静队血",
        tooltip = "队伍平均血量低于该值时，使用宁静。",
        min_value = 40,
        max_value = 70,
        step = 5,
        default_value = 50,
        bind_config = restoration_tranquility_party_hp_threshold,
    })

    local function InitFrame()
        -- x:60 y:12
        -- 用途：显示宁静队伍血量阈值配置。
        -- 更新函数：set_restoration_tranquility_party_hp_threshold
        local restoration_tranquility_party_hp_threshold_cell = Cell:New(60, 12)

        -- 说明：根据宁静队伍血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_tranquility_party_hp_threshold(value)
            restoration_tranquility_party_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_tranquility_party_hp_threshold:register_callback(set_restoration_tranquility_party_hp_threshold)
        set_restoration_tranquility_party_hp_threshold(restoration_tranquility_party_hp_threshold:get_value() or 50)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:61 y:12
    -- 自然迅捷血量 min:50 max:70 default:60 step:5
    -- 当非坦克玩家血量低于此值时，使用自然迅捷。
    local restoration_nature_swiftness_hp_threshold = Config("restoration_nature_swiftness_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_nature_swiftness_hp_threshold",
        name = "自然迅捷血量",
        tooltip = "当非坦克玩家血量低于此值时，使用自然迅捷。",
        min_value = 50,
        max_value = 70,
        step = 5,
        default_value = 60,
        bind_config = restoration_nature_swiftness_hp_threshold,
    })

    local function InitFrame()
        -- x:61 y:12
        -- 用途：显示自然迅捷血量阈值配置。
        -- 更新函数：set_restoration_nature_swiftness_hp_threshold
        local restoration_nature_swiftness_hp_threshold_cell = Cell:New(61, 12)

        -- 说明：根据自然迅捷血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_nature_swiftness_hp_threshold(value)
            restoration_nature_swiftness_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_nature_swiftness_hp_threshold:register_callback(set_restoration_nature_swiftness_hp_threshold)
        set_restoration_nature_swiftness_hp_threshold(restoration_nature_swiftness_hp_threshold:get_value() or 60)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:62 y:12
    -- 迅捷治愈血量 min:70 max:100 default:90 step:5
    -- 统计低于该血量的，身上有2个hot的人数。
    local restoration_swiftmend_hp_threshold = Config("restoration_swiftmend_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_swiftmend_hp_threshold",
        name = "迅捷治愈血量",
        tooltip = "统计低于该血量的，身上有2个hot的人数。",
        min_value = 70,
        max_value = 100,
        step = 5,
        default_value = 90,
        bind_config = restoration_swiftmend_hp_threshold,
    })

    local function InitFrame()
        -- x:62 y:12
        -- 用途：显示迅捷治愈血量阈值配置。
        -- 更新函数：set_restoration_swiftmend_hp_threshold
        local restoration_swiftmend_hp_threshold_cell = Cell:New(62, 12)

        -- 说明：根据迅捷治愈血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_swiftmend_hp_threshold(value)
            restoration_swiftmend_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_swiftmend_hp_threshold:register_callback(set_restoration_swiftmend_hp_threshold)
        set_restoration_swiftmend_hp_threshold(restoration_swiftmend_hp_threshold:get_value() or 90)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:63 y:12
    -- 迅捷治愈人数 min:1 max:5 default:2 step:1
    -- 满足迅捷治愈血量的人数，大于等于此值，则释放迅捷治愈。
    local restoration_swiftmend_count_threshold = Config("restoration_swiftmend_count_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_swiftmend_count_threshold",
        name = "迅捷治愈人数",
        tooltip = "满足迅捷治愈血量的人数，大于等于此值，则释放迅捷治愈。",
        min_value = 1,
        max_value = 5,
        step = 1,
        default_value = 2,
        bind_config = restoration_swiftmend_count_threshold,
    })

    local function InitFrame()
        -- x:63 y:12
        -- 用途：显示迅捷治愈人数阈值配置。
        -- 更新函数：set_restoration_swiftmend_count_threshold
        local restoration_swiftmend_count_threshold_cell = Cell:New(63, 12)

        -- 说明：根据迅捷治愈人数阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_swiftmend_count_threshold(value)
            restoration_swiftmend_count_threshold_cell:setCellRGBA(value * 20 / 255)
        end

        restoration_swiftmend_count_threshold:register_callback(set_restoration_swiftmend_count_threshold)
        set_restoration_swiftmend_count_threshold(restoration_swiftmend_count_threshold:get_value() or 2)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:64 y:12
    -- 愈合血量  min:70 max:95 default:85 step:5
    -- 低于该血量，且身上有1个hot的目标会被愈合。
    local restoration_regrowth_hp_threshold = Config("restoration_regrowth_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_regrowth_hp_threshold",
        name = "愈合血量",
        tooltip = "低于该血量，且身上有1个hot的目标会被愈合。",
        min_value = 70,
        max_value = 95,
        step = 5,
        default_value = 85,
        bind_config = restoration_regrowth_hp_threshold,
    })

    local function InitFrame()
        -- x:64 y:12
        -- 用途：显示愈合血量阈值配置。
        -- 更新函数：set_restoration_regrowth_hp_threshold
        local restoration_regrowth_hp_threshold_cell = Cell:New(64, 12)

        -- 说明：根据愈合血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_regrowth_hp_threshold(value)
            restoration_regrowth_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_regrowth_hp_threshold:register_callback(set_restoration_regrowth_hp_threshold)
        set_restoration_regrowth_hp_threshold(restoration_regrowth_hp_threshold:get_value() or 85)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:65 y:12
    -- 回春血量  min:85 max:99 default:97 step:1
    -- 低于该血量，会释放回春。
    local restoration_rejuvenation_hp_threshold = Config("restoration_rejuvenation_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_rejuvenation_hp_threshold",
        name = "回春血量",
        tooltip = "低于该血量，会释放回春。",
        min_value = 85,
        max_value = 99,
        step = 1,
        default_value = 97,
        bind_config = restoration_rejuvenation_hp_threshold,
    })

    local function InitFrame()
        -- x:65 y:12
        -- 用途：显示回春血量阈值配置。
        -- 更新函数：set_restoration_rejuvenation_hp_threshold
        local restoration_rejuvenation_hp_threshold_cell = Cell:New(65, 12)

        -- 说明：根据回春血量阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_rejuvenation_hp_threshold(value)
            restoration_rejuvenation_hp_threshold_cell:setCellRGBA(value / 255)
        end

        restoration_rejuvenation_hp_threshold:register_callback(set_restoration_rejuvenation_hp_threshold)
        set_restoration_rejuvenation_hp_threshold(restoration_rejuvenation_hp_threshold:get_value() or 97)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:66 y:12
    -- 丰饶保持  min:0 max:10 default:5 step:1
    -- 针对5人小队，非爆发阶段要保持多少丰饶（回春预铺）
    local restoration_abundance_stack_threshold = Config("restoration_abundance_stack_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_abundance_stack_threshold",
        name = "丰饶保持",
        tooltip = "针对5人小队，非爆发阶段要保持多少丰饶（回春预铺）",
        min_value = 0,
        max_value = 10,
        step = 1,
        default_value = 5,
        bind_config = restoration_abundance_stack_threshold,
    })

    local function InitFrame()
        -- x:66 y:12
        -- 用途：显示丰饶层数阈值配置。
        -- 更新函数：set_restoration_abundance_stack_threshold
        local restoration_abundance_stack_threshold_cell = Cell:New(66, 12)

        -- 说明：根据丰饶层数阈值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_abundance_stack_threshold(value)
            restoration_abundance_stack_threshold_cell:setCellRGBA(value * 20 / 255)
        end

        restoration_abundance_stack_threshold:register_callback(set_restoration_abundance_stack_threshold)
        set_restoration_abundance_stack_threshold(restoration_abundance_stack_threshold:get_value() or 5)
    end
    insert(MartixInitFuncs, InitFrame)
end

do
    -- x:67 y:12
    -- 该数值没用了。
    -- 坦克缺口忽略  min:0 max:50 default:15 step:1
    -- 计算坦克的血量时，当坦克的血量缺口小于这个百分比时，认为坦克是满血的
    -- local restoration_tank_deficit_ignore_percent = Config("restoration_tank_deficit_ignore_percent")
    -- insert(ConfigRows, {
    --     type = "slider",
    --     key = "restoration_tank_deficit_ignore_percent",
    --     name = "坦克缺口忽略",
    --     tooltip = "计算坦克的血量时，当坦克的血量缺口小于这个百分比时，认为坦克是满血的",
    --     min_value = 0,
    --     max_value = 50,
    --     step = 1,
    --     default_value = 15,
    --     bind_config = restoration_tank_deficit_ignore_percent,
    -- })

    -- After(2, function() -- 2 秒后执行，确保 DejaVu 核心已加载完成
    --     -- x:67 y:12
    --     -- 用途：显示坦克缺口忽略百分比配置。
    --     -- 更新函数：set_restoration_tank_deficit_ignore_percent
    --     local restoration_tank_deficit_ignore_percent_cell = Cell:New(67, 12)
    --     -- 说明：根据坦克缺口忽略百分比配置更新显示强度。
    --     -- 依赖事件更新：无
    --     -- 依赖定时刷新：无
    --     local function set_restoration_tank_deficit_ignore_percent(value)
    --         restoration_tank_deficit_ignore_percent_cell:setCellRGBA(value / 255)
    --     end
    --     restoration_tank_deficit_ignore_percent:register_callback(set_restoration_tank_deficit_ignore_percent)
    --     set_restoration_tank_deficit_ignore_percent(restoration_tank_deficit_ignore_percent:get_value())
    -- end)
end

do
    -- x:68 y:12
    -- hot等效  min:0 max:4 default:2 step:0.1
    -- 每个hot等效的生命值
    local restoration_hot_hp_threshold = Config("restoration_hot_hp_threshold")
    insert(ConfigRows, {
        type = "slider",
        key = "restoration_hot_hp_threshold",
        name = "hot等效",
        tooltip = "每个hot等效的生命值",
        min_value = 0,
        max_value = 4,
        step = 0.1,
        default_value = 2,
        bind_config = restoration_hot_hp_threshold,
    })

    local function InitFrame()
        -- x:68 y:12
        -- 用途：显示 hot 等效生命值配置。
        -- 更新函数：set_restoration_hot_hp_threshold
        local restoration_hot_hp_threshold_cell = Cell:New(68, 12)

        -- 说明：根据 hot 等效生命值配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_restoration_hot_hp_threshold(value)
            restoration_hot_hp_threshold_cell:setCellRGBA(value * 20 / 255)
        end

        restoration_hot_hp_threshold:register_callback(set_restoration_hot_hp_threshold)
        set_restoration_hot_hp_threshold(restoration_hot_hp_threshold:get_value() or 2)
    end
    insert(MartixInitFuncs, InitFrame)
end
