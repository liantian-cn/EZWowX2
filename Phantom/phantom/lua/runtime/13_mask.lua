--[[
original: runtime\13_mask.lua
uuid: 26c9c5ff-9919-443d-9893-e659bf72c847
runtime_index: 13
摘要：
    创建基板两侧的固定颜色与逐帧黑白交替色块，供后续检测屏幕亮度和抖动异常。

描述：
    将初始化函数登记到共享 UI 初始化队列，在背景创建后逐个构建八个独立框体及各自纹理。
    左侧从上到下为 Cyan、Magenta、Yellow、Flash，右侧从下到上为 Red、Green、Blue、Gray。
    每块边长为 SIZE.CELL，分别贴齐背景左上角或右下角，避开两处对角定位标记。
    Flash 初始为黑色，由局部 eventFrame 在每次 OnUpdate 时切换黑白。
    所有色块实例仅使用局部变量保存；本文件只提供检测用画面，不执行异常判断。

修改记录：
2026-09-20：检测色块统一使用 Marker 静态层级。
2026-09-07：新增八个检测色块及 Flash 逐帧黑白切换。

]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame -- 创建色块框体与更新驱动框体
local insert = table.insert     -- 登记 UI 初始化函数

--[[  variable reference  ]]

local FrameLevel = addonTable.FrameLevel   -- 共享框体层级
local SIZE = addonTable.SIZE               -- 初始化时读取 Cell 边长
local UIInitFuncs = addonTable.UIInitFuncs -- 按注册顺序执行的 UI 初始化队列

--[[  logical code  ]]

local function InitMaskFrames()                                                 -- 背景初始化后创建两侧检测色块
    local parent = addonTable.BackgroundFrame                                   -- 执行初始化时取得背景框体

    local cyanFrame = CreateFrame("Frame", nil, parent)                         -- 创建青色色块框体
    cyanFrame:SetSize(SIZE.CELL, SIZE.CELL)                                     -- 宽高均为一个 Cell
    cyanFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -1 * SIZE.CELL)         -- 按 Cell 边长换算锚点偏移
    cyanFrame:SetFrameStrata("TOOLTIP")                                         -- 与定位标记使用相同显示层
    cyanFrame:SetFrameLevel(FrameLevel.Marker)                                  -- 使用检测标记层级
    cyanFrame:Show()                                                            -- 显示青色色块框体

    local cyanTexture = cyanFrame:CreateTexture(nil, "ARTWORK")                 -- 创建此框体独有的青色纹理
    cyanTexture:SetAllPoints(cyanFrame)                                         -- 纹理铺满色块
    cyanTexture:SetColorTexture(0 / 255, 255 / 255, 255 / 255, 1)               -- 设置不透明青色
    cyanTexture:Show()                                                          -- 显示青色纹理

    local magentaFrame = CreateFrame("Frame", nil, parent)                      -- 创建洋红色色块框体
    magentaFrame:SetSize(SIZE.CELL, SIZE.CELL)                                  -- 宽高均为一个 Cell
    magentaFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -2 * SIZE.CELL)      -- 按 Cell 边长换算锚点偏移
    magentaFrame:SetFrameStrata("TOOLTIP")                                      -- 与定位标记使用相同显示层
    magentaFrame:SetFrameLevel(FrameLevel.Marker)                               -- 使用检测标记层级
    magentaFrame:Show()                                                         -- 显示洋红色色块框体

    local magentaTexture = magentaFrame:CreateTexture(nil, "ARTWORK")           -- 创建此框体独有的洋红色纹理
    magentaTexture:SetAllPoints(magentaFrame)                                   -- 纹理铺满色块
    magentaTexture:SetColorTexture(255 / 255, 0 / 255, 255 / 255, 1)            -- 设置不透明洋红色
    magentaTexture:Show()                                                       -- 显示洋红色纹理

    local yellowFrame = CreateFrame("Frame", nil, parent)                       -- 创建黄色色块框体
    yellowFrame:SetSize(SIZE.CELL, SIZE.CELL)                                   -- 宽高均为一个 Cell
    yellowFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -3 * SIZE.CELL)       -- 按 Cell 边长换算锚点偏移
    yellowFrame:SetFrameStrata("TOOLTIP")                                       -- 与定位标记使用相同显示层
    yellowFrame:SetFrameLevel(FrameLevel.Marker)                                -- 使用检测标记层级
    yellowFrame:Show()                                                          -- 显示黄色色块框体

    local yellowTexture = yellowFrame:CreateTexture(nil, "ARTWORK")             -- 创建此框体独有的黄色纹理
    yellowTexture:SetAllPoints(yellowFrame)                                     -- 纹理铺满色块
    yellowTexture:SetColorTexture(255 / 255, 255 / 255, 0 / 255, 1)             -- 设置不透明黄色
    yellowTexture:Show()                                                        -- 显示黄色纹理

    local flashFrame = CreateFrame("Frame", nil, parent)                        -- 创建黑白闪烁色块框体
    flashFrame:SetSize(SIZE.CELL, SIZE.CELL)                                    -- 宽高均为一个 Cell
    flashFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -4 * SIZE.CELL)        -- 按 Cell 边长换算锚点偏移
    flashFrame:SetFrameStrata("TOOLTIP")                                        -- 与定位标记使用相同显示层
    flashFrame:SetFrameLevel(FrameLevel.Marker)                                 -- 使用检测标记层级
    flashFrame:Show()                                                           -- 显示黑白闪烁色块框体

    local flashTexture = flashFrame:CreateTexture(nil, "ARTWORK")               -- 创建此框体独有的黑白闪烁纹理
    flashTexture:SetAllPoints(flashFrame)                                       -- 纹理铺满色块
    flashTexture:SetColorTexture(0, 0, 0, 1)                                    -- 设置不透明初始黑色
    flashTexture:Show()                                                         -- 显示黑白闪烁纹理

    local redFrame = CreateFrame("Frame", nil, parent)                          -- 创建红色色块框体
    redFrame:SetSize(SIZE.CELL, SIZE.CELL)                                      -- 宽高均为一个 Cell
    redFrame:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", 0, 1 * SIZE.CELL)   -- 按 Cell 边长换算锚点偏移
    redFrame:SetFrameStrata("TOOLTIP")                                          -- 与定位标记使用相同显示层
    redFrame:SetFrameLevel(FrameLevel.Marker)                                   -- 使用检测标记层级
    redFrame:Show()                                                             -- 显示红色色块框体

    local redTexture = redFrame:CreateTexture(nil, "ARTWORK")                   -- 创建此框体独有的红色纹理
    redTexture:SetAllPoints(redFrame)                                           -- 纹理铺满色块
    redTexture:SetColorTexture(255 / 255, 0 / 255, 0 / 255, 1)                  -- 设置不透明红色
    redTexture:Show()                                                           -- 显示红色纹理

    local greenFrame = CreateFrame("Frame", nil, parent)                        -- 创建绿色色块框体
    greenFrame:SetSize(SIZE.CELL, SIZE.CELL)                                    -- 宽高均为一个 Cell
    greenFrame:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", 0, 2 * SIZE.CELL) -- 按 Cell 边长换算锚点偏移
    greenFrame:SetFrameStrata("TOOLTIP")                                        -- 与定位标记使用相同显示层
    greenFrame:SetFrameLevel(FrameLevel.Marker)                                 -- 使用检测标记层级
    greenFrame:Show()                                                           -- 显示绿色色块框体

    local greenTexture = greenFrame:CreateTexture(nil, "ARTWORK")               -- 创建此框体独有的绿色纹理
    greenTexture:SetAllPoints(greenFrame)                                       -- 纹理铺满色块
    greenTexture:SetColorTexture(0 / 255, 255 / 255, 0 / 255, 1)                -- 设置不透明绿色
    greenTexture:Show()                                                         -- 显示绿色纹理

    local blueFrame = CreateFrame("Frame", nil, parent)                         -- 创建蓝色色块框体
    blueFrame:SetSize(SIZE.CELL, SIZE.CELL)                                     -- 宽高均为一个 Cell
    blueFrame:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", 0, 3 * SIZE.CELL)  -- 按 Cell 边长换算锚点偏移
    blueFrame:SetFrameStrata("TOOLTIP")                                         -- 与定位标记使用相同显示层
    blueFrame:SetFrameLevel(FrameLevel.Marker)                                  -- 使用检测标记层级
    blueFrame:Show()                                                            -- 显示蓝色色块框体

    local blueTexture = blueFrame:CreateTexture(nil, "ARTWORK")                 -- 创建此框体独有的蓝色纹理
    blueTexture:SetAllPoints(blueFrame)                                         -- 纹理铺满色块
    blueTexture:SetColorTexture(0 / 255, 0 / 255, 255 / 255, 1)                 -- 设置不透明蓝色
    blueTexture:Show()                                                          -- 显示蓝色纹理

    local grayFrame = CreateFrame("Frame", nil, parent)                         -- 创建灰色色块框体
    grayFrame:SetSize(SIZE.CELL, SIZE.CELL)                                     -- 宽高均为一个 Cell
    grayFrame:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", 0, 4 * SIZE.CELL)  -- 按 Cell 边长换算锚点偏移
    grayFrame:SetFrameStrata("TOOLTIP")                                         -- 与定位标记使用相同显示层
    grayFrame:SetFrameLevel(FrameLevel.Marker)                                  -- 使用检测标记层级
    grayFrame:Show()                                                            -- 显示灰色色块框体

    local grayTexture = grayFrame:CreateTexture(nil, "ARTWORK")                 -- 创建此框体独有的灰色纹理
    grayTexture:SetAllPoints(grayFrame)                                         -- 纹理铺满色块
    grayTexture:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)             -- 设置不透明灰色
    grayTexture:Show()                                                          -- 显示灰色纹理

    local flashIsWhite = false                                                  -- Flash 初始为黑色，记录当前黑白状态
    local eventFrame = CreateFrame("Frame", nil, parent)                        -- 跟随背景可见性驱动逐帧更新
    local elapsedTime = 0

    eventFrame:SetScript("OnUpdate", function(self, elapsed)
        elapsedTime = elapsedTime + elapsed

        if elapsedTime < 1 then
            return
        end

        elapsedTime = elapsedTime - 1

        -- 每秒切换一次黑白
        flashIsWhite = not flashIsWhite

        if flashIsWhite then
            flashTexture:SetColorTexture(1, 1, 1, 1)
        else
            flashTexture:SetColorTexture(0, 0, 0, 1)
        end
    end)
    eventFrame:Show() -- 启用逐帧更新
end

insert(UIInitFuncs, InitMaskFrames) -- 在背景创建完成后初始化检测色块
