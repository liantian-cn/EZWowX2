--[[
original: ../conditions/interrupt_blacklist_icons@dev/template.lua
uuid: {{uuid}}
摘要：固定十槽的游戏面板打断黑名单图标。
描述：共享配置按档案保存，排序选槽后渲染；失败不补位，不改变配置，不循环请求。
修改记录：2026-09-18：按已确认契约新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 监听数据加载结果
local After = C_Timer.After -- 事件下一帧刷新
local GetSpellTexture = C_Spell.GetSpellTexture -- 按普通配置 ID 获取图标
local RequestLoadSpellData = C_Spell.RequestLoadSpellData -- 请求普通配置法术数据
local insert = table.insert -- 注册面板行和初始化
local sort = table.sort -- ID 数值排序
local pairs = pairs -- 遍历非秘密配置
local type = type -- 配置字段检查
local tonumber = tonumber -- 兼容面板保存的数值键
local floor = math.floor -- 验证正整数技能 ID
--[[
C_Spell.GetSpellTexture(spellIdentifier) 返回 iconID、originalIconID、conditionalIconID，可能无值；
C_Spell.RequestLoadSpellData(spellID) 无返回值，完成后 SPELL_DATA_LOAD_RESULT(spellID, success)。
仅查询用户配置的普通 ID，不从当前施法读取秘密 ID。Texture:SetTexture(texture) 返回成功布尔，
失败清空图标与角标；不使用 panel 的备用问号纹理。
2026-09-18：12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；
Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellDocumentation.lua、SimpleTextureBaseAPIDocumentation.lua。
Wiki：https://warcraft.wiki.gg/wiki/API_C_Spell.GetSpellTexture
https://warcraft.wiki.gg/wiki/API_C_Spell.RequestLoadSpellData；2026-09-18 已获取页面，以目标 build 本地源码为准。
]]
--[[  variable reference  ]]
local Config = addonTable.Config -- 同键共享配置，档案切换自动通知
local ConfigRows = addonTable.ConfigRows -- 必须在加载期登记
local IconTile = addonTable.IconTile -- 固定第四行图标槽
local COLOR = addonTable.COLOR -- 黄色类别角标
local UIInitFuncs = addonTable.UIInitFuncs -- panel 默认值初始化完成后创建槽
--[[  logical code  ]]
local POSITIONS = { {{x1}}, {{x2}}, {{x3}}, {{x4}}, {{x5}}, {{x6}}, {{x7}}, {{x8}}, {{x9}}, {{x10}} }
local SLOT_COUNT = 10
local CONFIG_KEY = "interrupt_blacklist"
local DEFAULT_IDS = { [468962] = true, [1248327] = true, [1254669] = true,
    [1258436] = true, [1262510] = true, [1262526] = true }
local config = Config(CONFIG_KEY)
local displays = {}
local configured = {}
local selected = {}
local eventFrame = CreateFrame("Frame")

-- 每份循环只声明一次；默认值仅交由 panel 应用，不重复调用 set_default。
insert(ConfigRows, {
    type = "spell_list", name = "打断黑名单", bind_config = config, default_value = DEFAULT_IDS,
    tooltip = "按技能 ID 升序显示前十项；黄色角标仅表示黑名单图标类别。",
})

local function render()
    for index = 1, SLOT_COUNT do
        local display = displays[index]
        if display then
            display:Clear()
            local spellID = selected[index]
            if spellID then
                local texture = GetSpellTexture(spellID)
                if texture and display.Icon:SetTexture(texture) then
                    display.Icon:Show()
                    display:SetBorderColor(COLOR.SPELL_TYPE.INTERRUPTIBLE)
                end
            end
        end
    end
end

local function refreshConfiguration()
    configured = {}
    selected = {}
    local values = config:get_value()
    if type(values) == "table" then
        for rawID, enabled in pairs(values) do
            local spellID = tonumber(rawID)
            if enabled and spellID and spellID > 0 and spellID == floor(spellID) and not configured[spellID] then
                configured[spellID] = true
                insert(selected, spellID)
            end
        end
    end
    sort(selected)
    -- 所有配置项请求一次；显示始终按已排序 ID 的前十项固定，不按加载成功数补位。
    for index = 1, #selected do RequestLoadSpellData(selected[index]) end
    render()
end

config:register_callback(refreshConfiguration)
local function initialize()
    for index = 1, SLOT_COUNT do displays[index] = IconTile:New(POSITIONS[index]) end
    refreshConfiguration() -- set_default/register_callback 不会立即通知，必须主动初始渲染
end
eventFrame:RegisterEvent("SPELL_DATA_LOAD_RESULT")
eventFrame:SetScript("OnEvent", function(_, _, spellID, success)
    if success and configured[spellID] then
        After(0, function()
            if configured[spellID] then render() end -- 删除或切档案后的迟到事件不恢复旧图标
        end)
    end
end)
insert(UIInitFuncs, initialize)
