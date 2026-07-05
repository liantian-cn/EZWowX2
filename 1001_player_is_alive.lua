-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local insert                = table.insert
local CreateFrame           = CreateFrame
local UnitIsDeadOrGhost     = UnitIsDeadOrGhost

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

--[[
简述：      玩家处于存活状态
分类：      玩家属性
分类索引：  1
位置：      1行1列

说明

使用UnitIsDeadOrGhost检测玩家是否死亡
    - True: 死亡
    - False: 存活

注意：因为没有检测玩家是否存活的直接函数，所以使用UnitIsDeadOrGhost来检测玩家是否死亡，取反后即可得到玩家是否存活的状态。

关于"秘密值"（Secret Value）：
在WoW 12.1中，很多API返回的值被标记为"secret"，不能直接用于逻辑判断或计算。
UnitIsDeadOrGhost返回的布尔值可能是secret的，取反操作可能无法正确执行。
因此，取反操作应该在解码端（即读取RGB值并解析的端）进行，而不是在插件端。

解码端的工作原理：
- 插件端：将UnitIsDeadOrGhost的结果（true/false）通过setCellBoolean设置到cell的B通道
- 解码端：读取cell的RGB值，根据B通道的值（0或1）判断玩家状态，然后进行取反操作
- 这样确保了数据传输的可靠性，避免了secret value带来的问题
]]

-- 分类定义
-- CELL_CLASSIFICATION: 表示这个cell属于"玩家状态"分类（值为5）
-- CELL_CLASSIFICATION_INDEX: 表示这是"玩家状态"分类下的第1个cell
-- CELL_POSITION_X/Y: 表示这个cell在矩阵中的位置（1行1列）
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 1
local CELL_POSITION_X = 1
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
-- 0表示黑色背景，用于初始化cell的颜色
local DEFAULT_VALUE = 0

-- 开始代码
local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    -- 创建cell实例
    -- 参数说明：
    -- x, y: cell在矩阵中的位置（以cell为单位）
    -- classification: cell的分类（R通道值）
    -- index: cell在分类中的索引（G通道值）
    -- default_value: cell的默认值（B通道值）
    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    -- 更新函数：设置cell的状态
    -- UnitIsDeadOrGhost("player") 返回：
    --   true  -> 玩家死亡或灵魂状态
    --   false -> 玩家存活状态
    -- setCellBoolean 会根据布尔值设置cell的颜色（trueColor或falseColor）
    local function updateCell()
        cell:setCellBoolean(UnitIsDeadOrGhost("player"))
    end

    -- 初始化时立即更新一次状态
    updateCell()

    -- 注册事件：当玩家状态变化时更新cell
    -- PLAYER_DEAD: 玩家死亡
    -- PLAYER_ALIVE: 玩家复活
    -- PLAYER_UNGHOST: 玩家从灵魂状态恢复
    eventFrame:RegisterEvent("PLAYER_DEAD")
    eventFrame:RegisterEvent("PLAYER_ALIVE")
    eventFrame:RegisterEvent("PLAYER_UNGHOST")

    -- 事件处理：所有事件都调用同一个更新函数
    -- 这种模式适用于多个事件触发相同处理逻辑的情况
    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCell()
    end)

    -- 如果需要为不同事件调用不同函数，可以使用路由分配模式：
    -- eventFrame:SetScript("OnEvent", function(self, event, ...)
    --     self[event](self, ...)
    -- end)
    --
    -- 然后为每个事件定义处理函数：
    -- function eventFrame:PLAYER_DEAD()
    --     -- 处理死亡事件
    -- end
    --
    -- function eventFrame:PLAYER_ALIVE()
    --     -- 处理复活事件
    -- end
end

-- 将初始化函数插入到全局初始化函数列表中，确保在插件加载时执行
-- 执行顺序：
-- 1. 所有文件加载，注册InitFrame到FrameInitFuncs
-- 2. 第二帧时执行所有FrameInitFuncs
-- 3. CreateMartixFrame先执行（在0005_matrix.lua中注册）
-- 4. 然后InitFrame执行（在本文件中注册）
insert(addonTable.FrameInitFuncs, InitFrame)
