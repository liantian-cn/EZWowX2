local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local insert = table.insert

-- WoW 官方 API

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs

local spell_queue_window = Config("spell_queue_window") -- 滑块配置项

insert(ConfigRows, {
    type = "slider", -- 设置类型
    key = "spell_queue_window", -- 行标识
    name = "延迟窗口", -- 标题文本
    tooltip = "延迟窗口的时间, 单位ms, 这个值越小, 按键越晚", -- 提示信息
    min_value = 250, -- 最小值
    max_value = 550, -- 最大值
    step = 10, -- 步进
    default_value = 400, -- 默认值
    bind_config = spell_queue_window, -- 绑定的配置对象
})

-- 说明：配置变更时打印当前延迟窗口值。
-- 依赖事件更新：无
-- 依赖定时刷新：无
local function spell_queue_window_updater(value)
    print("延迟窗口设置为：" .. value)
end

spell_queue_window:register_callback(spell_queue_window_updater)

local function InitFrame()
    -- x:57 y:9
    -- 用途：显示延迟窗口配置值。
    -- 更新函数：updateSpellQueueWindow
    local cell = Cell:New(57, 9)
    cell:setCellRGBA(20 / 255)

    -- 说明：根据延迟窗口配置值更新延迟窗口显示强度。
    -- 依赖事件更新：无
    -- 依赖定时刷新：无
    local function updateSpellQueueWindow(value)
        local mean = (value / 10) / 255
        cell:setCellRGBA(mean)
    end

    spell_queue_window:register_callback(updateSpellQueueWindow)
end
insert(MartixInitFuncs, InitFrame)
