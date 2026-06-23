-- 插件内引用
local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config         -- 配置对象工厂
local ConfigRows = DejaVu.ConfigRows -- 配置行对象工厂

-- 示例配置对象
local slider_example_config = Config("slider_example_config")         -- 滑块配置项
local combo_example_config = Config("combo_example_config")           -- 下拉框配置项
local spell_list_example_config = Config("spell_list_example_config") -- 技能列表配置项

local function FormatCallbackValue(value)
    if type(value) ~= "table" then
        return tostring(value)
    end

    local spellIDs = {}
    for spellID, enabled in pairs(value) do
        if enabled then
            table.insert(spellIDs, tostring(spellID))
        end
    end

    table.sort(spellIDs)
    return "{" .. table.concat(spellIDs, ", ") .. "}"
end

local function RegisterPrintCallback(label, config)
    config:register_callback(function(value)
        print(label .. " changed:", FormatCallbackValue(value))
    end)
end

RegisterPrintCallback("slider", slider_example_config)
RegisterPrintCallback("combo", combo_example_config)
RegisterPrintCallback("spell_list", spell_list_example_config)



local slider_row = { -- 滑块示例行
    type = "slider", -- 设置类型
    key = "slider_example", -- 行标识
    name = "滑块示例", -- 标题文本
    tooltip = "这只是一个例子, 最小值0, 最大值100, 步进5, 默认值20", -- 提示信息
    min_value = 0, -- 最小值
    max_value = 100, -- 最大值
    step = 5, -- 步进
    default_value = 20, -- 默认值
    bind_config = slider_example_config, -- 绑定的配置对象
    -- callback = callback, -- 回调函数
} -- slider_row 结束

local combo_row = { -- 下拉框示例行
    type = "combo", -- 设置类型
    key = "combo_example", -- 行标识
    name = "下拉框例子", -- 标题文本
    tooltip = "这只是一个例子。", -- 提示信息
    default_value = "zhangsan", -- 默认选中值
    options = { -- 选项列表
        { k = "zhangsan", v = "张三" }, -- 选项1
        { k = "lisi", v = "李四" }, -- 选项2
    }, -- options 结束
    bind_config = combo_example_config, -- 绑定的配置对象
    -- callback = callback, -- 回调函数
} -- combo_row 结束

local spell_list_row = { -- 技能列表示例行
    type = "spell_list", -- 设置类型
    key = "spell_list_example", -- 行标识
    name = "技能图标例子", -- 标题文本
    tooltip = "这只是一个例子。 ", -- 提示信息
    default_value = { -- 默认技能集合
        [294929] = true, -- 示例技能1
        [5487] = true, -- 示例技能2
    }, -- default_value 结束
    bind_config = spell_list_example_config, -- 绑定的配置对象
    -- callback = callback, -- 回调函数
} -- spell_list_row 结束

table.insert(ConfigRows, slider_row) -- 写入滑块示例
table.insert(ConfigRows, combo_row) -- 写入下拉框示例
table.insert(ConfigRows, spell_list_row) -- 写入技能列表示例
