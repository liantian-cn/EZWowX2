--[[
original: examples\07_player_cast.lua
uuid: {{uuid}}
index: 7
摘要：在第四行第 1 个 IconTile 中显示玩家当前施法图标。

描述：
    通过 UIInitFuncs 创建图标并立即刷新，之后由玩家施法事件更新。
    优先读取普通施法，再读取引导或蓄力施法；只用 NeverSecret 哨兵判断是否存在施法。
    施法期间显示 PLAYER_SPELL 角标；没有施法时清空图标和角标，保留黑底。
    图标纹理直接交给 IconTile，不在 Lua 中检查秘密纹理或技能名称。

修改记录：
2026-09-11：按解码开发前的 Lua 示例需求新增玩家施法 IconTile。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame         -- 创建本例独立事件框架
local UnitCastingInfo = UnitCastingInfo -- 获取普通施法图标及非秘密存在哨兵
local UnitChannelInfo = UnitChannelInfo -- 获取引导或蓄力图标及非秘密存在哨兵
local insert = table.insert             -- 注册 UI 初始化函数

--[[
UnitCastingInfo：返回指定单位当前普通施法的信息，无施法时没有可用的施法返回值。
来源：https://warcraft.wiki.gg/wiki/API_UnitCastingInfo
签名：name, displayName, textureID, startTimeMs, endTimeMs, isTradeskill, castID,
    notInterruptible, castingSpellID, castBarID, delayTimeMs = UnitCastingInfo(unit)
参数：unit 为单位标识，本例使用 UNIT_TOKEN。
返回值：name 为技能名称；displayName 为显示名称；textureID 为技能图标；
    startTimeMs、endTimeMs 为开始与结束的毫秒时间，与 GetTime() * 1000 对应；
    isTradeskill 为是否商业技能（NeverSecret）；castID 为本次施法 GUID；
    notInterruptible 为可空 boolean，true 表示不可打断；castingSpellID 为技能 ID；
    castBarID 为可空施法条 ID（NeverSecret）；delayTimeMs 为累计推迟毫秒数（NeverSecret）。
    第 11 项 delayTimeMs 在有效施法中不可空，使用 ~= nil 判断，不检查秘密名称或纹理。

UnitChannelInfo：返回指定单位当前引导或蓄力施法的信息。
来源：https://warcraft.wiki.gg/wiki/API_UnitChannelInfo
签名：name, displayName, textureID, startTimeMs, endTimeMs, isTradeskill,
    notInterruptible, spellID, isEmpowered, numEmpowerStages, castBarID = UnitChannelInfo(unit)
参数：unit 为单位标识；普通施法查询未命中后再查询引导。
返回值：前六项含义同普通施法；第 7 项 notInterruptible 为可空的不可打断标记；
    第 8 项 spellID 为技能 ID；第 9 项 isEmpowered 表示是否蓄力（NeverSecret）；
    第 10 项 numEmpowerStages 为蓄力阶段数（NeverSecret）；第 11 项 castBarID 为可空 ID（NeverSecret）。
    有效引导的 isEmpowered 不可空；false 仍表示存在普通引导，必须使用 ~= nil 判断。
共同限制：SecretWhenUnitSpellCastRestricted；SecretArguments = "AllowedWhenUntainted"。
    图标纹理和可打断标记可能为秘密值；仅使用明确的 NeverSecret 哨兵判断施法是否存在。

核验日期：2026-09-11；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/ 下的
    UnitDocumentation.lua、CurveUtilDocumentation.lua、SimpleTextureAPIDocumentation.lua。
Wiki 在线访问返回 403；说明依据用户提供的 Wiki 内容与本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local IconTile = addonTable.IconTile       -- 复用现有图标与角标接口
local COLOR = addonTable.COLOR             -- 共享施法类型颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建图标

--[[  logical code  ]]

-- 类型：IconTile，仅作说明；以下参数供未来插件替换。
local POSITION_X = 1        -- 第 1 个图标，紧接左侧检测列
local UNIT_TOKEN = "player" -- 只读取玩家的施法状态

local playerCastTile                    -- 等待 UI 初始化创建的图标
local eventFrame = CreateFrame("Frame") -- 本例独立的事件框架

local function RefreshCastTile()
    if not playerCastTile then -- 初始化前的事件不访问尚未创建的图标
        return
    end

    -- delayTimeMs 是有效普通施法必有的 NeverSecret 哨兵，避免检查秘密纹理或名称。
    local _, _, castingTexture, _, _, _, _, _, _, _, castDelayTimeMs = UnitCastingInfo(UNIT_TOKEN)
    if castDelayTimeMs ~= nil then
        playerCastTile:SetIcon(castingTexture)
        playerCastTile:SetBorderColor(COLOR.SPELL_TYPE.PLAYER_SPELL)
        return
    end

    -- isEmpowered 是有效引导必有的 NeverSecret 哨兵，false 也代表正在引导。
    local _, _, channelTexture, _, _, _, _, _, isEmpowered = UnitChannelInfo(UNIT_TOKEN)
    if isEmpowered ~= nil then
        playerCastTile:SetIcon(channelTexture)
        playerCastTile:SetBorderColor(COLOR.SPELL_TYPE.PLAYER_SPELL)
        return
    end

    playerCastTile:Clear() -- 没有普通施法或引导时露出黑底并隐藏角标
end

local function InitializeCastTile()
    playerCastTile = IconTile:New(POSITION_X)
    RefreshCastTile() -- 立即读取当前状态，补齐初始化前可能发生的事件
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步当前施法状态
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
eventFrame:SetScript("OnEvent", RefreshCastTile) -- 每次事件重新查询当前状态，不读取事件中的秘密载荷
insert(UIInitFuncs, InitializeCastTile) -- 沿用共享布局、计数和缩放
