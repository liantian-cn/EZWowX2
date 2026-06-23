local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random = math.random
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame
local IsMouselooking = _G.IsMouselooking
local IsMouseButtonDown = _G.IsMouseButtonDown

local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    -- x:58 y:9
    -- 用途：显示玩家当前是否正在使用鼠标。
    -- 更新函数：updateCell
    local cell = Cell:New(58, 9)

    -- 说明：根据鼠标转向和鼠标按键状态刷新鼠标使用标记。
    -- 依赖事件更新：PLAYER_STARTED_TURNING、PLAYER_STOPPED_TURNING。
    -- 依赖定时刷新：0.1 秒。
    local function updateCell()
        local useMouse = IsMouselooking()
            or IsMouseButtonDown("LeftButton")
            or IsMouseButtonDown("RightButton")
            or IsMouseButtonDown("MiddleButton")
            or IsMouseButtonDown("Button4")
            or IsMouseButtonDown("Button5")
        cell:setCellBoolean(useMouse, COLOR.STATUS_BOOLEAN.USE_MOUSE, COLOR.BLACK)
    end

    -- PLAYER_STARTED_TURNING
    -- 事件说明：玩家开始转向时立即刷新鼠标使用状态。
    -- 对应函数：updateCell
    eventFrame:RegisterEvent("PLAYER_STARTED_TURNING")
    function eventFrame:PLAYER_STARTED_TURNING()
        updateCell()
    end

    -- PLAYER_STOPPED_TURNING
    -- 事件说明：玩家停止转向时立即刷新鼠标使用状态。
    -- 对应函数：updateCell
    eventFrame:RegisterEvent("PLAYER_STOPPED_TURNING")
    function eventFrame:PLAYER_STOPPED_TURNING()
        updateCell()
    end

    -- 定时路由：每 0.1 秒轮询鼠标按键状态，补足事件无法覆盖的输入。
    local fastTimeElapsed = -random()
    -- local lowTimeElapsed = -random() -- 当前未使用，保留 0.5 秒刷新档位结构。
    -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构。
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateCell()
        end
        -- lowTimeElapsed = lowTimeElapsed + elapsed
        -- if lowTimeElapsed > 0.5 then
        --     lowTimeElapsed = lowTimeElapsed - 0.5
        --     updateCell()
        -- end
        -- superLowTimeElapsed = superLowTimeElapsed + elapsed
        -- if superLowTimeElapsed > 2 then
        --     superLowTimeElapsed = superLowTimeElapsed - 2
        --     updateCell()
        -- end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)

    -- 首次刷新
    updateCell()
end
insert(MartixInitFuncs, InitFrame)
