--[[
original: ../conditions/focus_cast_icon@dev/template.lua
uuid: {{uuid}}
plugin: focus_cast_icon@dev
摘要：焦点当前施法图标。
描述：
    秘密纹理通过 IconTile:SetIcon 直接显示，不消费 SetTexture 返回值；角标不表示打断许可。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-18：事件统一延至下一帧刷新。
2026-09-18：按已确认计划新增焦点条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local UnitExists = UnitExists -- 单位存在前置
local After = C_Timer.After             -- 事件后延至下一帧刷新
local CreateFrame = CreateFrame         -- 创建本实例事件或显示框架
local insert = table.insert             -- 注册 UI 初始化回调
local UnitCastingInfo = UnitCastingInfo -- 使用普通施法的非秘密哨兵及图标
local UnitChannelInfo = UnitChannelInfo -- 使用通道的非秘密蓄力哨兵及图标

--[[
用途与签名：UnitCastingInfo/UnitChannelInfo("focus") 第 3 项返回可能秘密的 textureID；用 NeverSecret 的 delayTimeMs/isEmpowered 判断状态。
业务限制：秘密纹理直接送给 Texture:SetTexture；空槽返回空字符串，其他为内部 6×6 RGB hash。
核验日期：2026-09-18；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 来源与查询入口（2026-09-18 已获取 UnitCastingInfo/UnitChannelInfo 页面；其他链接为查询入口）：
    https://warcraft.wiki.gg/wiki/API_UnitCastingInfo
    https://warcraft.wiki.gg/wiki/API_UnitChannelInfo
2026-09-19 纠正：SimpleTextureBaseAPIDocumentation.lua 的 Texture:SetTexture(texture) 允许秘密参数
（AllowedWhenTainted），返回 success: bool；未标记 SecretReturns 不保证返回值可供普通 Lua 判断。
沿用玩家的 IconTile:SetIcon 显示路径，不消费返回值；单位消失或无施法时清空图标和角标，
不保证设置失败时同步隐藏角标，也不保证异步资源最终加载成功；实际客户端仍待验收。
Wiki：https://warcraft.wiki.gg/wiki/API:TextureBase_SetTexture （2026-09-18 获取，提示返回值可能始终 true）。
]]

--[[  variable reference  ]]
local IconTile = addonTable.IconTile       -- 第四行图标区域
local COLOR = addonTable.COLOR             -- 本项目共享黑白及施法颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local UNIT_TOKEN = "focus" -- 本版本固定焦点单位

local display
local eventFrame = CreateFrame("Frame")

local function showTexture(texture)
    display:SetIcon(texture) -- 沿用玩家显示路径，不消费可能秘密的 SetTexture 返回值
    display:SetBorderColor(COLOR.SPELL_TYPE.PLAYER_SPELL)
end

local function update()
    if not display then return end
    if not UnitExists(UNIT_TOKEN) then display:Clear(); return end
    local _, _, castingTexture, _, _, _, _, _, _, _, castDelayTimeMs = UnitCastingInfo(UNIT_TOKEN)
    if castDelayTimeMs ~= nil then -- NeverSecret 哨兵，不比较施法名称或纹理
        showTexture(castingTexture)
        return
    end
    local _, _, channelTexture, _, _, _, _, _, isEmpowered = UnitChannelInfo(UNIT_TOKEN)
    if isEmpowered ~= nil then -- false 也是有效的普通通道哨兵
        showTexture(channelTexture)
        return
    end
    display:Clear()
end

local function initialize()
    display = IconTile:New(POSITION_X)
    update()
end

eventFrame:RegisterEvent("PLAYER_FOCUS_CHANGED")
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)

insert(UIInitFuncs, initialize)
