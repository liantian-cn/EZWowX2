--[[
original: examples\06_spell_charges.lua
uuid: {{uuid}}
index: 6
摘要：在第三行第 1 条 ValueBar 中显示技能当前充能层数。

描述：
    按候选 ID 顺序选择首个出现在玩家法术书中的技能，进入世界或法术书变化时重新选择。
    通过 UIInitFuncs 创建宽度为 2 的 ValueBar，将范围固定为 0 到宽度并立即刷新。
    充能变化时把 currentCharges 直接交给数值条；未选中技能或没有充能信息时显示 0。

修改记录：
2026-09-11：按解码开发前的 Lua 示例需求新增技能充能 ValueBar。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame                         -- 创建本例独立事件框架
local IsSpellInSpellBook = C_SpellBook.IsSpellInSpellBook -- 查询候选技能是否在玩家法术书中
local GetSpellCharges = C_Spell.GetSpellCharges          -- 获取当前充能信息
local ipairs = ipairs                                  -- 按候选 ID 顺序查找技能
local insert = table.insert                            -- 注册 UI 初始化函数

--[[
C_SpellBook.IsSpellInSpellBook：查询技能是否应出现在法术书中。
来源：https://warcraft.wiki.gg/wiki/API_C_SpellBook.IsSpellInSpellBook
签名：isInSpellBook = C_SpellBook.IsSpellInSpellBook(spellID, spellBank, includeOverrides)
参数：spellID 为技能 ID；spellBank 默认 Player；includeOverrides 默认 true。
返回值：非秘密 boolean；可能包含天赋光环授予的替代技能，不等同于严格已学会状态。
限制标记：SecretArguments = "AllowedWhenUntainted"。

C_Spell.GetSpellCharges：返回可累积充能技能的充能信息，未找到技能或技能不使用充能时可能返回 nil。
来源：https://warcraft.wiki.gg/wiki/API_C_Spell.GetSpellCharges
签名：chargeInfo = C_Spell.GetSpellCharges(spellIdentifier)
参数：spellIdentifier 为 SpellIdentifier，本例使用选中的技能 ID。
返回值：SpellChargeInfo 表；字段如下：
    currentCharges：当前可用充能层数，可能为秘密值，直接交给 ValueBar:setValue。
    maxCharges：最大充能层数，NeverSecret；本例范围由固定 WIDTH 决定，不动态采用此字段。
    cooldownStartTime：最近一次充能冷却开始的时间；未冷却时为 0。
    cooldownDuration：恢复一层充能所需的秒数。
    chargeModRate：冷却 UI 的更新速率。
    isActive：是否正在恢复充能，NeverSecret。
限制标记：MayReturnNothing；SecretWhenCooldownsRestricted；SecretArguments = "AllowedWhenTainted"。
    只判断返回表是否存在，不比较或计算 currentCharges。

核验日期：2026-09-11；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/ 下的
    SpellBookDocumentation.lua、SpellDocumentation.lua、SpellSharedDocumentation.lua、
    SimpleStatusBarAPIDocumentation.lua（SetValue 接受秘密参数）。
Wiki 在线访问返回 403；说明依据用户提供的 Wiki 内容与本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local ValueBar = addonTable.ValueBar       -- 复用现有数值条构造与更新接口
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建数值条

--[[  logical code  ]]

-- 技能名称：血液沸腾；类型：ValueBar。名称和类型仅作说明，以下参数供未来插件替换。
local SPELL_IDS = { 50841, 50842 } -- 按优先顺序排列的候选技能 ID
local POSITION_X = 1              -- 第 1 条数值条，包含左侧分隔的占位起点
local WIDTH = 2                   -- 内容宽度，同时作为最大充能层数
local REVERSE = false             -- 是否反向填充

local chargeBar                        -- 等待 UI 初始化创建的数值条
local selectedSpellID                  -- 当前选中的首个法术书技能 ID
local eventFrame = CreateFrame("Frame") -- 本例独立的事件框架

local function SelectSpell()
    selectedSpellID = nil                   -- 清除旧选择，避免技能移除后继续查询旧 ID
    for _, spellID in ipairs(SPELL_IDS) do
        if IsSpellInSpellBook(spellID) then -- 仅对非秘密的法术书查询结果分支
            selectedSpellID = spellID
            return
        end
    end
end

local function RefreshChargeBar()
    if not chargeBar then -- 初始化前的事件不访问尚未创建的数值条
        return
    end

    if not selectedSpellID then -- 全部候选不在法术书中
        chargeBar:setValue(0)
        return
    end

    local chargeInfo = GetSpellCharges(selectedSpellID)
    if chargeInfo then
        chargeBar:setValue(chargeInfo.currentCharges) -- 可能为秘密值，直接交给 StatusBar 渲染
    else
        chargeBar:setValue(0) -- 无技能或无充能信息时清空填充
    end
end

local function InitializeChargeBar()
    chargeBar = ValueBar:New(POSITION_X, WIDTH, REVERSE)
    chargeBar:setMinMaxValues(0, WIDTH) -- 最大值与内容宽度一致，不采用运行期 maxCharges
    SelectSpell()
    RefreshChargeBar()                 -- 立即替换构造器的默认半满状态
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时重新选择技能并刷新
eventFrame:RegisterEvent("SPELL_UPDATE_CHARGES")  -- 充能数量或恢复状态变化
eventFrame:RegisterEvent("SPELL_UPDATE_USES")     -- 技能可用次数变化
eventFrame:RegisterEvent("SPELLS_CHANGED")        -- 法术书变化时重新选择候选技能
eventFrame:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_ENTERING_WORLD" or event == "SPELLS_CHANGED" then
        SelectSpell()
    end
    RefreshChargeBar()
end)
insert(UIInitFuncs, InitializeChargeBar) -- 沿用共享布局、计数和缩放
