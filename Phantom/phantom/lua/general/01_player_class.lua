--[[
original: general\01_player_class.lua
uuid: 0536bd34-e377-4274-a7ae-b80455dd359a
index: 1
摘要：在第一行首个 Cell 中以灰度编码玩家职业 ID。

描述：
    使用普通 Cell 承载通用职业字段，将构造函数加入 UIInitFuncs，沿用共享尺寸换算与背景扩宽。
    构造完成后立即刷新，并使用独立事件框架在登录和进入世界时刷新职业颜色。
    RGB 分量均为 classID / 255；没有返回职业 ID 时显示不透明黑色。

修改记录：
2026-09-08：按玩家职业通用 Cell 需求新增。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame -- 创建独立事件框架
local UnitClass = UnitClass -- 查询玩家职业名称、职业标识和职业 ID
local select = select -- 提取 UnitClass 的第三个返回值
local insert = table.insert -- 注册 UI 初始化函数

--[[
UnitClass（System: Unit）：返回指定单位的职业。
签名：className, classFilename, classID = UnitClass(unit)
参数：unit 为 UnitToken 字符串，本文件固定使用 "player"。
返回值：
    className：本地化职业名，例如 "Warrior" 或 "Guerrier"，标记 ConditionalSecret。
    classFilename：不随语言变化的职业标识，例如 "WARRIOR"。
    classID：number 类型的 ClassID，本文件直接作为灰度值。
限制标记：MayReturnNothing、SecretWhenUnitIdentityRestricted；
    SecretArguments = "AllowedWhenUntainted"。这些标记不表示可以解除 Secret 限制。

ID  className (enUS)  classFilename  引入版本（用户提供）
1   Warrior           WARRIOR
2   Paladin           PALADIN
3   Hunter            HUNTER
4   Rogue             ROGUE
5   Priest            PRIEST
6   Death Knight      DEATHKNIGHT   3.0.2
7   Shaman            SHAMAN
8   Mage              MAGE
9   Warlock           WARLOCK
10  Monk              MONK          5.0.4
11  Druid             DRUID
12  Demon Hunter      DEMONHUNTER   7.0.3
13  Evoker            EVOKER        10.0.0

核验日期：2026-09-08；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
事件定义：同目录 SystemDocumentation.lua。
官方用例：Interface/AddOns/Blizzard_SharedXML/UnitUtil.lua 使用玩家职业 ID。
用户提供页面版本为 12.1.5 (69594)，并列出 Classic 版本；不视为本地已验证版本。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell -- 复用普通 Cell 的构造与颜色接口
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景初始化之后创建职业 Cell

--[[  logical code  ]]

local playerClassCell -- 第一行的玩家职业 Cell，等待 UI 初始化后赋值
local eventFrame = CreateFrame("Frame") -- 独立监听玩家登录与进入世界事件

local function RefreshPlayerClassCell()
    if not playerClassCell then -- 登录事件可能先于延迟 UI 初始化到达
        return
    end

    local classID = select(3, UnitClass("player")) -- 职业 ID 即灰度值
    local gray = (classID or 0) / 255 -- 未返回职业 ID 时使用黑色
    playerClassCell:setCellRGBA(gray, gray, gray) -- RGB 使用相同灰度，Cell 接口固定透明度为 1
end

local function InitializePlayerClassCell()
    playerClassCell = Cell:New({ x = 1, y = 1 }) -- 第一行首个普通 Cell，自动计数并扩宽背景
    RefreshPlayerClassCell() -- 补齐初始化前已发生的登录事件，立即显示当前职业
end

eventFrame:RegisterEvent("PLAYER_LOGIN") -- 玩家登录时刷新
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 玩家进入世界时刷新
eventFrame:SetScript("OnEvent", RefreshPlayerClassCell) -- 两个事件共用同一刷新逻辑
insert(UIInitFuncs, InitializePlayerClassCell) -- 沿用共享初始化顺序和缩放
