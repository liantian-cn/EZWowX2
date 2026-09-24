--[[
original: general\02_player_specialization.lua
uuid: 154ab0be-9c33-4935-8e57-531eb6bde99e
index: 2
摘要：在第一行第二个 Cell 中以灰度编码玩家当前专精索引。

描述：
    使用普通 Cell 承载通用专精字段，将构造函数加入 UIInitFuncs，沿用共享尺寸换算与背景扩宽。
    构造完成后立即刷新，并使用独立事件框架在登录、进入世界和玩家专精变化时刷新颜色。
    RGB 分量均为 specializationIndex / 255；没有返回专精索引时显示不透明黑色。

修改记录：
2026-09-08：按玩家专精通用 Cell 需求新增。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame -- 创建独立事件框架
local GetSpecialization = C_SpecializationInfo.GetSpecialization -- 使用新版 API 查询玩家当前专精索引
local insert = table.insert -- 注册 UI 初始化函数

--[[
C_SpecializationInfo.GetSpecialization：返回玩家当前专精的顺序索引。
来源：https://warcraft.wiki.gg/wiki/API:C_SpecializationInfo.GetSpecialization
签名：specializationIndex = C_SpecializationInfo.GetSpecialization(isInspect, isPet, specGroupIndex)
参数（均可省略，本文件无参数调用）：
    isInspect：boolean，可选。
    isPet：boolean，可选。
    specGroupIndex：number，可选，专精组索引。
返回值：
    specializationIndex：number，当前专精索引，本文件直接作为灰度值。
限制标记：SecretArguments = "AllowedWhenUntainted"。

核验日期：2026-09-08；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/SpecializationInfoDocumentation.lua。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell -- 复用普通 Cell 的构造与颜色接口
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸、背景和职业 Cell 初始化之后创建专精 Cell

--[[  logical code  ]]

local playerSpecializationCell -- 第一行的玩家专精 Cell，等待 UI 初始化后赋值
local eventFrame = CreateFrame("Frame") -- 独立监听登录、进入世界与玩家专精变化

local function RefreshPlayerSpecializationCell()
    if not playerSpecializationCell then -- 事件可能先于延迟 UI 初始化到达
        return
    end

    local specializationIndex = GetSpecialization() -- 直接读取玩家当前专精索引作为灰度值
    local gray = (specializationIndex or 0) / 255 -- 未返回专精索引时使用黑色
    playerSpecializationCell:setCellRGBA(gray, gray, gray) -- RGB 使用相同灰度，Cell 接口固定透明度为 1
end

local function InitializePlayerSpecializationCell()
    playerSpecializationCell = Cell:New({ x = 2, y = 1 }) -- 第一行第二个普通 Cell，自动计数并扩宽背景
    RefreshPlayerSpecializationCell() -- 构造后立即显示当前专精，补齐初始化前已发生的事件
end

eventFrame:RegisterEvent("PLAYER_LOGIN") -- 玩家登录时刷新
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 玩家进入世界时刷新
eventFrame:RegisterEvent("ACTIVE_PLAYER_SPECIALIZATION_CHANGED") -- 玩家当前专精变化时刷新
eventFrame:RegisterUnitEvent("PLAYER_SPECIALIZATION_CHANGED", "player") -- 只接收玩家自身的专精变化
eventFrame:SetScript("OnEvent", RefreshPlayerSpecializationCell) -- 四个事件共用同一刷新逻辑
insert(UIInitFuncs, InitializePlayerSpecializationCell) -- 沿用共享初始化顺序和缩放
