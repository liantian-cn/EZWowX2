local addonName, addonTable = ...                       -- 插件名称与共享表

local format = string.format                            -- 字符串格式化
local max = math.max                                    -- 数学最大值
local insert = table.insert                             -- 表插入
local floor = math.floor                                -- 向下取整
local find = string.find                                -- 字符查找
local sub = string.sub                                  -- 字符截取
-- WoW 官方 API
local CreateColor = CreateColor                         -- 创建颜色对象
local CreateFrame = CreateFrame                         -- 创建框体
local GameTooltip = GameTooltip                         -- 游戏提示框
local UIParent = UIParent                               -- 游戏主界面父框体
local GetSpellDescription = C_Spell.GetSpellDescription -- 获取技能描述
local GetSpellName = C_Spell.GetSpellName               -- 获取技能名
local GetSpellTexture = C_Spell.GetSpellTexture         -- 获取技能图标
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local GetUIScaleFactor = DejaVu.GetUIScaleFactor -- UI 缩放计算
local Config = DejaVu.Config                     -- 配置对象工厂
local ConfigRows = DejaVu.ConfigRows             -- 配置行对象工厂
local logging = DejaVu.Logging
logging(addonName .. " loaded.")

-- 面板模块主表
local Panel = {}                                                       -- 面板模块主表
local FontPath = "Interface\\Addons\\" .. addonName .. "\\DejaVu.ttf"  -- 自定义字体路径
local Rows = {}                                                        -- 面板行配置容器（在加载期写入, 在第二帧构建 UI）
local SIZE = {}                                                        -- 尺寸表（在创建面板时初始化）
local COLOR = {}                                                       -- 面板配色表
local UI = {}                                                          -- UI 工具集合
local OnUpdateFuncs = {}                                               -- 更新函数容器
local DefaultApplied = {}                                              -- 记录已 set_default 的 key, 确保只执行一次

COLOR = {                                                              -- 面板配色表
    Black           = CreateColor(0 / 255, 0 / 255, 0 / 255, 1),       -- 纯黑
    WindowBg        = CreateColor(30 / 255, 30 / 255, 30 / 255, 1),    -- 窗口背景色
    WindowText      = CreateColor(0 / 255, 0 / 255, 0 / 255, 1),       -- 窗口文字色（备用）
    WindowBorder    = CreateColor(83 / 255, 88 / 255, 91 / 255, 1),    -- 窗口边框色
    Base            = CreateColor(255 / 255, 255 / 255, 255 / 255, 1), -- 基础白
    ButtonBorder    = CreateColor(52 / 255, 52 / 255, 52 / 255, 1),    -- 按钮边框色
    ButtonHighlight = CreateColor(86 / 255, 86 / 255, 86 / 255, 1),    -- 按钮悬停高亮
    ButtonMouseUp   = CreateColor(43 / 255, 43 / 255, 43 / 255, 1),    -- 按钮正常底色
    ButtonMouseDown = CreateColor(37 / 255, 37 / 255, 37 / 255, 1),    -- 按钮按下底色
    SliderLeft      = CreateColor(73 / 255, 179 / 255, 234 / 255, 1),  -- 滑块已填充色
    SliderRight     = CreateColor(159 / 255, 159 / 255, 159 / 255, 1), -- 滑块未填充色
    RowHover        = CreateColor(50 / 255, 50 / 255, 50 / 255, 1),    -- 行悬停色
    Text            = CreateColor(230 / 255, 230 / 255, 230 / 255, 1), -- 文本颜色
    DropdownBg      = CreateColor(34 / 255, 34 / 255, 34 / 255, 1),    -- 下拉列表背景色
}                                                                      -- COLOR 结束

local eventFrame = CreateFrame("Frame")
local timeElapsed = 0
eventFrame:HookScript("OnUpdate", function(self, elapsed)
    timeElapsed = timeElapsed + elapsed
    if timeElapsed > 0.1 then
        timeElapsed = 0
        for updaterIndex = 1, #OnUpdateFuncs do
            local updater = OnUpdateFuncs[updaterIndex]
            updater()
        end
    end
end)


-- 尺寸表（在创建面板时初始化）

local function InitializeSize()                                   -- 初始化尺寸（与 EZPanel 数值一致）
    SIZE = {                                                      -- 尺寸表主体
        MainFrame = {                                             -- 主框体尺寸
            Width = GetUIScaleFactor(400),                        -- 主框体宽度
            Height = GetUIScaleFactor(16) + GetUIScaleFactor(36), -- 主框体单行高度
            Border = GetUIScaleFactor(1),                         -- 主框体边框
            Spacing = GetUIScaleFactor(8),                        -- 内边距/间距
        },                                                        -- MainFrame 结束
        BUTTON = {                                                -- 按钮尺寸
            Width = GetUIScaleFactor(110),                        -- 按钮宽度
            Height = GetUIScaleFactor(36),                        -- 按钮高度
            Border = GetUIScaleFactor(2),                         -- 按钮边框
            IconBorder = GetUIScaleFactor(8),                     -- 图标边框
        },                                                        -- BUTTON 结束
        SETTING_LINE = {                                          -- 设置行尺寸
            Height = GetUIScaleFactor(36),                        -- 行高
            Spacing = GetUIScaleFactor(8),                        -- 行间距
            TitleWidth = GetUIScaleFactor(172),                   -- 标题宽度
            WidgetWidth = GetUIScaleFactor(204),                  -- 控件宽度
            SliderBarHeight = GetUIScaleFactor(6),                -- 滑块条高度
            SliderSquareHeight = GetUIScaleFactor(16),            -- 滑块方块高度
            SliderValueWidth = GetUIScaleFactor(48),              -- 滑块数值区宽度
        }                                                         -- SETTING_LINE 结束
    }                                                             -- SIZE 结束
end                                                               -- InitializeSize 结束



function UI.ApplyBorderAndFill(frame, borderColor, fillColor, borderSize) -- 边框+填充
    local bg = frame:CreateTexture(nil, "BACKGROUND") -- 边框纹理
    bg:SetAllPoints(frame) -- 贴满父框体
    bg:SetColorTexture(borderColor:GetRGBA()) -- 边框色

    local art = frame:CreateTexture(nil, "ARTWORK") -- 填充纹理
    art:SetPoint("TOPLEFT", frame, "TOPLEFT", borderSize, -borderSize) -- 内缩边距
    art:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -borderSize, borderSize) -- 内缩边距
    art:SetColorTexture(fillColor:GetRGBA()) -- 填充色

    return bg, art -- 返回两个纹理
end -- ApplyBorderAndFill 结束

function UI.BindRowHover(row, hoverTexture, title, tooltip) -- 行悬停与提示
    local function OnEnter(self) -- 鼠标进入
        hoverTexture:SetColorTexture(COLOR.RowHover:GetRGBA()) -- 高亮背景
        if tooltip and tooltip ~= "" then -- 有提示则显示
            GameTooltip:SetOwner(self, "ANCHOR_RIGHT", SIZE.MainFrame.Spacing, 0) -- 位置
            GameTooltip:SetFrameStrata("TOOLTIP") -- 层级
            GameTooltip:SetFrameLevel(1000) -- 层级
            GameTooltip:SetText(title, 1, 1, 1, 1, true) -- 标题
            GameTooltip:AddLine(tooltip, 0.8, 0.8, 0.8, true) -- 内容
            GameTooltip:Show() -- 显示
        end -- 提示判断结束
    end -- OnEnter 结束

    local function OnLeave() -- 鼠标离开
        hoverTexture:SetColorTexture(0, 0, 0, 0) -- 清除高亮
        if tooltip and tooltip ~= "" then -- 有提示则隐藏
            GameTooltip:Hide() -- 隐藏提示
        end -- 提示判断结束
    end -- OnLeave 结束

    row:SetScript("OnEnter", OnEnter) -- 绑定进入事件
    row:SetScript("OnLeave", OnLeave) -- 绑定离开事件
end -- BindRowHover 结束

function UI.ToggleFrame(frame) -- 显示/隐藏切换
    if frame:IsShown() then -- 如果已显示
        frame:Hide() -- 隐藏
    else -- 否则
        frame:Show() -- 显示
    end -- 显示判断结束
end -- ToggleFrame 结束

function UI.CreateButton(parent, slug, x_pos, y_pos, buttonWidth, buttonHeight, buttonText) -- 标准按钮
    local button = CreateFrame("Button", addonName .. slug, parent) -- 创建按钮
    button:SetPoint("TOPLEFT", parent, "TOPLEFT", x_pos, y_pos) -- 定位
    button:SetSize(buttonWidth, buttonHeight) -- 尺寸
    button:EnableMouse(true) -- 可点击

    button.bg = button:CreateTexture(nil, "BACKGROUND") -- 边框
    button.bg:SetAllPoints() -- 填满
    button.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA()) -- 边框色

    button.art = button:CreateTexture(nil, "ARTWORK") -- 填充
    button.art:SetPoint("TOPLEFT", button, "TOPLEFT", SIZE.BUTTON.Border, -SIZE.BUTTON.Border) -- 内缩
    button.art:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -SIZE.BUTTON.Border, SIZE.BUTTON.Border) -- 内缩
    button.art:SetColorTexture(COLOR.ButtonMouseUp:GetRGBA()) -- 默认底色

    button.text = button:CreateFontString(nil, "OVERLAY") -- 按钮文字
    button.text:SetPoint("CENTER", button, "CENTER") -- 居中
    button.text:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    button.text:SetJustifyH("CENTER") -- 水平居中
    button.text:SetJustifyV("MIDDLE") -- 垂直居中
    button.text:SetTextColor(1, 1, 1) -- 文字颜色
    button.text:SetText(buttonText) -- 文案

    button:SetScript("OnMouseDown", function() -- 按下效果
        button.art:SetColorTexture(COLOR.ButtonMouseDown:GetRGBA()) -- 深色
    end) -- 按下回调结束
    button:SetScript("OnMouseUp", function() -- 抬起效果
        button.art:SetColorTexture(COLOR.ButtonMouseUp:GetRGBA()) -- 恢复
    end) -- 抬起回调结束
    button:SetScript("OnEnter", function() -- 悬停
        button.bg:SetColorTexture(COLOR.ButtonHighlight:GetRGBA()) -- 高亮边框
    end) -- 悬停回调结束
    button:SetScript("OnLeave", function() -- 离开
        button.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA()) -- 恢复边框
    end) -- 离开回调结束
    return button -- 返回按钮
end -- CreateButton 结束

local function CreateSettingRow(title, tooltip) -- 创建一行设置项
    local panelFrame = Panel.Frame -- 面板容器
    if not panelFrame then -- 容器不存在
        return nil -- 直接返回
    end -- 容器判断结束

    if not panelFrame._rowCount then -- 初始化行计数
        panelFrame._rowCount = 0 -- 行计数
        panelFrame._contentHeight = SIZE.MainFrame.Spacing * 2 -- 内容高度
    end -- 行计数初始化结束

    local rowIndex = panelFrame._rowCount -- 当前行索引
    local topOffset = panelFrame._topOffset or 0 -- 额外顶部偏移
    local rowY = -SIZE.MainFrame.Spacing - topOffset - rowIndex * (SIZE.SETTING_LINE.Height + SIZE.SETTING_LINE.Spacing) -- 行 Y

    local row = CreateFrame("Frame", addonName .. "settingRow" .. rowIndex, panelFrame) -- 行框体
    row:SetPoint("TOPLEFT", panelFrame, "TOPLEFT", SIZE.MainFrame.Spacing, rowY) -- 左上
    row:SetPoint("TOPRIGHT", panelFrame, "TOPRIGHT", -SIZE.MainFrame.Spacing, rowY) -- 右上
    row:SetHeight(SIZE.SETTING_LINE.Height) -- 行高
    row:EnableMouse(true) -- 可响应鼠标

    row.bg = row:CreateTexture(nil, "BACKGROUND") -- 行背景
    row.bg:SetAllPoints(row) -- 填满
    row.bg:SetColorTexture(0, 0, 0, 0) -- 默认透明

    row.title = row:CreateFontString(nil, "OVERLAY") -- 标题文本
    row.title:SetPoint("LEFT", row, "LEFT", 0, 0) -- 左对齐
    row.title:SetSize(SIZE.SETTING_LINE.TitleWidth, SIZE.SETTING_LINE.Height) -- 标题区域
    row.title:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    row.title:SetJustifyH("LEFT") -- 左对齐
    row.title:SetJustifyV("MIDDLE") -- 垂直居中
    row.title:SetTextColor(COLOR.Text:GetRGBA()) -- 文字色
    row.title:SetText(title) -- 标题

    UI.BindRowHover(row, row.bg, title, tooltip) -- 绑定悬停效果

    panelFrame._rowCount = rowIndex + 1 -- 行数 +1
    panelFrame._contentHeight = SIZE.MainFrame.Spacing * 2 -- 基础高度
        + (panelFrame._topOffset or 0) -- 顶部偏移
        + panelFrame._rowCount * SIZE.SETTING_LINE.Height -- 行高总和
        + max(0, panelFrame._rowCount - 1) * SIZE.SETTING_LINE.Spacing -- 行间距
    panelFrame:SetHeight(panelFrame._contentHeight) -- 自适应高度

    return row -- 返回行框体
end -- CreateSettingRow 结束

local function CreatePanelFrame() -- 创建控制条与设置面板
    if Panel.ControlFrame then -- 已创建则跳过
        return -- 直接退出
    end -- 已创建判断结束

    InitializeSize() -- 初始化尺寸（第二帧时 UI 缩放准确）

    local spacing = SIZE.MainFrame.Spacing -- 通用间距
    local areaWidth = (SIZE.MainFrame.Width - spacing * 4) / 3 -- 三等分区域宽度

    local controlFrame = CreateFrame("Frame", addonName .. "controlFrame", UIParent) -- 控制条
    controlFrame:SetPoint("BOTTOMLEFT", UIParent, "BOTTOMLEFT", 0, 0) -- 居中
    controlFrame:SetSize(SIZE.MainFrame.Width, SIZE.MainFrame.Height) -- 尺寸
    controlFrame:SetFrameStrata("TOOLTIP") -- 层级
    controlFrame:SetFrameLevel(900) -- 层级
    controlFrame:SetMovable(true) -- 可拖动
    controlFrame:EnableMouse(true) -- 可交互
    controlFrame:RegisterForDrag("LeftButton") -- 左键拖动
    controlFrame:SetClampedToScreen(true) -- 限制屏幕内
    controlFrame:SetScript("OnDragStart", controlFrame.StartMoving) -- 开始拖动
    controlFrame:SetScript("OnDragStop", controlFrame.StopMovingOrSizing) -- 结束拖动
    controlFrame:Show() -- 显示

    controlFrame.bg, controlFrame.art = UI.ApplyBorderAndFill(controlFrame, COLOR.WindowBorder, COLOR.WindowBg, SIZE.MainFrame.Border) -- 边框

    local toggleButton = UI.CreateButton(controlFrame, "toggleButton", spacing, -spacing, areaWidth, SIZE.BUTTON.Height, "已停止") -- 启停按钮

    local statusArea = CreateFrame("Frame", addonName .. "statusArea", controlFrame) -- 状态区域容器
    statusArea:SetPoint("TOPLEFT", controlFrame, "TOPLEFT", spacing * 2 + areaWidth, -spacing) -- 位置
    statusArea:SetSize(areaWidth, SIZE.BUTTON.Height) -- 尺寸

    local statusIcon = CreateFrame("Frame", addonName .. "statusIcon", statusArea) -- 状态图标
    statusIcon:SetPoint("LEFT", statusArea, "LEFT", 0, 0) -- 左对齐
    statusIcon:SetSize(SIZE.BUTTON.Height, SIZE.BUTTON.Height) -- 尺寸
    statusIcon.bg = statusIcon:CreateTexture(nil, "BACKGROUND") -- 图标边框
    statusIcon.bg:SetPoint("TOPLEFT", statusIcon, "TOPLEFT", SIZE.BUTTON.IconBorder / 2, -SIZE.BUTTON.IconBorder / 2) -- 内缩
    statusIcon.bg:SetPoint("BOTTOMRIGHT", statusIcon, "BOTTOMRIGHT", -SIZE.BUTTON.IconBorder / 2, SIZE.BUTTON.IconBorder / 2) -- 内缩
    statusIcon.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA()) -- 边框色
    statusIcon.art = statusIcon:CreateTexture(nil, "ARTWORK") -- 图标填充
    statusIcon.art:SetPoint("TOPLEFT", statusIcon, "TOPLEFT", SIZE.BUTTON.IconBorder, -SIZE.BUTTON.IconBorder) -- 内缩
    statusIcon.art:SetPoint("BOTTOMRIGHT", statusIcon, "BOTTOMRIGHT", -SIZE.BUTTON.IconBorder, SIZE.BUTTON.IconBorder) -- 内缩
    statusIcon.art:SetColorTexture(0, 1, 0, 1) -- 默认绿色

    local statusText = statusArea:CreateFontString(nil, "OVERLAY") -- 状态文字
    statusText:SetPoint("LEFT", statusIcon, "RIGHT", spacing, 0) -- 左对齐
    statusText:SetPoint("RIGHT", statusArea, "RIGHT", 0, 0) -- 右对齐
    statusText:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    statusText:SetJustifyH("LEFT") -- 左对齐
    statusText:SetJustifyV("MIDDLE") -- 垂直居中
    statusText:SetTextColor(0, 1, 0) -- 默认绿色
    statusText:SetText("未爆发") -- 默认文案

    local configButton = UI.CreateButton(controlFrame, "configButton", spacing * 3 + areaWidth * 2, -spacing, areaWidth, SIZE.BUTTON.Height, "配置") -- 配置按钮

    local settingFrame = CreateFrame("Frame", addonName .. "settingFrame", UIParent) -- 设置面板
    settingFrame:SetPoint("TOPLEFT", controlFrame, "BOTTOMLEFT", 0, 0) -- 紧贴控制条下方
    settingFrame:SetSize(SIZE.MainFrame.Width, SIZE.MainFrame.Height) -- 初始尺寸
    settingFrame:SetFrameStrata("TOOLTIP") -- 层级
    settingFrame:SetFrameLevel(900) -- 层级
    settingFrame.bg, settingFrame.art = UI.ApplyBorderAndFill(settingFrame, COLOR.WindowBorder, COLOR.WindowBg, SIZE.MainFrame.Border) -- 边框
    settingFrame:Hide() -- 默认收缩

    Panel.ControlFrame = controlFrame -- 保存控制条
    Panel.SettingFrame = settingFrame -- 保存设置面板
    Panel.Frame = settingFrame -- 设置行容器指向设置面板

    local function UpdateStatusUI(enabled) -- 刷新状态显示
        if enabled then -- 启用状态
            toggleButton.text:SetText("已启动") -- 按钮文案
            toggleButton.text:SetTextColor(0, 1, 0)
        else -- 停用状态
            toggleButton.text:SetText("已停止") -- 按钮文案
            toggleButton.text:SetTextColor(1, 0, 0)
        end -- 状态判断结束
    end -- UpdateStatusUI 结束

    local lastBurstState = nil -- 记录上次爆发状态
    local lastBurstText = nil -- 记录上次爆发文案

    local function UpdateBurstUI() -- 刷新爆发状态显示
        local inBurst = DejaVu.InBurst -- 爆发状态来源
        -- print(GetTime())
        if type(inBurst) == "function" then -- 当前核心定义是函数
            inBurst = inBurst()
        else -- 防御式兼容布尔值写法
            inBurst = inBurst == true
        end

        if inBurst then                             -- 爆发中显示倒计时
            local remaining = DejaVu.BurstRemaining -- 爆发剩余时间来源
            if type(remaining) == "function" then
                remaining = remaining()
            elseif type(remaining) ~= "number" then
                remaining = 0
            end

            local currentText = format("%.2f", remaining)  -- 当前倒计时文案

            if lastBurstState ~= true then                 -- 仅在爆发状态变化时刷新颜色
                statusIcon.art:SetColorTexture(0, 1, 0, 1) -- 绿色
                statusText:SetTextColor(0, 1, 0)           -- 绿色
                lastBurstState = true                      -- 缓存当前状态
            end

            if lastBurstText ~= currentText then           -- 文案变化才刷新
                statusText:SetText(currentText)            -- 倒计时
                lastBurstText = currentText                -- 缓存当前文案
            end
        else                                               -- 非爆发显示红色文案
            if lastBurstState ~= false then                -- 仅在爆发状态变化时刷新颜色
                statusIcon.art:SetColorTexture(1, 0, 0, 1) -- 红色
                statusText:SetTextColor(1, 0, 0)           -- 红色
                lastBurstState = false                     -- 缓存当前状态
            end

            if lastBurstText ~= "未爆发" then -- 文案变化才刷新
                statusText:SetText("未爆发") -- 文案
                lastBurstText = "未爆发" -- 缓存当前文案
            end
        end -- 爆发判断结束
    end -- UpdateBurstUI 结束

    local function ToggleSetting() -- 展开/收缩设置面板
        if settingFrame:IsShown() then -- 当前已展开
            settingFrame:Hide() -- 收缩
            if Panel.SpellListEditorFrame and Panel.SpellListEditorFrame:IsShown() then -- 编辑器显示时
                Panel.SpellListEditorFrame:Hide() -- 一起隐藏
            end -- 编辑器判断结束
        else -- 当前收缩
            settingFrame:Show() -- 展开
        end -- 展开判断结束
    end -- ToggleSetting 结束

    toggleButton:HookScript("OnMouseUp", function() -- 启停按钮点击
        DejaVu.Enable = not DejaVu.Enable -- 切换状态
        UpdateStatusUI(DejaVu.Enable == true) -- 刷新显示
    end) -- 启停回调结束

    configButton:HookScript("OnMouseUp", function() -- 配置按钮点击
        ToggleSetting() -- 展开/收缩
    end) -- 配置回调结束

    UpdateStatusUI(DejaVu.Enable == true) -- 初始化状态
    UpdateBurstUI() -- 初始化爆发显示
    insert(OnUpdateFuncs, UpdateBurstUI) -- 高频刷新爆发倒计时

    controlFrame.StatusIcon = statusIcon -- 保存图标
    controlFrame.StatusText = statusText -- 保存文字
    controlFrame.ToggleButton = toggleButton -- 保存按钮
    controlFrame.ConfigButton = configButton -- 保存按钮
    controlFrame.ToggleSetting = ToggleSetting -- 保存函数
end -- CreatePanelFrame 结束



local function GetStepDecimals(step)                                                                                                                        -- 计算步进小数位
    local s = tostring(step)                                                                                                                                -- 转字符串
    local dot = find(s, "%.")                                                                                                                               -- 查找小数点
    if not dot then                                                                                                                                         -- 无小数点
        return 0                                                                                                                                            -- 整数步进
    end                                                                                                                                                     -- 小数点判断结束
    local decimals = #s - dot                                                                                                                               -- 小数位数
    while decimals > 0 and sub(s, -1) == "0" do                                                                                                             -- 去掉末尾0
        s = sub(s, 1, -2)                                                                                                                                   -- 截断
        decimals = decimals - 1                                                                                                                             -- 更新小数位
    end                                                                                                                                                     -- 去零结束
    return decimals                                                                                                                                         -- 返回小数位数
end                                                                                                                                                         -- GetStepDecimals 结束

local function FormatStepValue(value, decimals)                                                                                                             -- 格式化显示值
    if decimals <= 0 then                                                                                                                                   -- 整数显示
        return format("%d", floor(value + 0.5))                                                                                                             -- 四舍五入
    end                                                                                                                                                     -- 整数判断结束
    return format("%." .. decimals .. "f", value)                                                                                                           -- 保留小数
end                                                                                                                                                         -- FormatStepValue 结束

local function ApplyDefaultValue(config, value)                                                                                                             -- 只设一次默认值
    if not config or not config.key then                                                                                                                    -- 配置对象无效
        return                                                                                                                                              -- 直接退出
    end                                                                                                                                                     -- 配置检查结束
    if DefaultApplied[config.key] then                                                                                                                      -- 已设过默认值
        return                                                                                                                                              -- 直接退出
    end                                                                                                                                                     -- 默认值检查结束
    config:set_default(value)                                                                                                                               -- 设默认值
    DefaultApplied[config.key] = true                                                                                                                       -- 标记已处理
end                                                                                                                                                         -- ApplyDefaultValue 结束

local function AddSliderRow(row_info)                                                                                                                       -- 创建滑块行                                                                                                                         -- 尺寸表
    local config = row_info.bind_config                                                                                                                     -- 绑定配置
    ApplyDefaultValue(config, row_info.default_value)                                                                                                       -- 只设一次默认值

    local row = CreateSettingRow(row_info.name, row_info.tooltip)                                                                                           -- 创建行
    if not row then                                                                                                                                         -- 创建失败
        return nil                                                                                                                                          -- 直接返回
    end                                                                                                                                                     -- 行创建检查结束

    local minValue = row_info.min_value                                                                                                                     -- 最小值
    local maxValue = row_info.max_value                                                                                                                     -- 最大值
    local step = row_info.step                                                                                                                              -- 步进
    local decimals = GetStepDecimals(step)                                                                                                                  -- 小数位数

    local widget = CreateFrame("Frame", addonName .. "sliderWidget" .. row:GetName(), row)                                                                  -- 控件容器
    widget:SetPoint("LEFT", row.title, "RIGHT", SIZE.SETTING_LINE.Spacing, 0)                                                                               -- 位置
    widget:SetSize(SIZE.SETTING_LINE.WidgetWidth, SIZE.SETTING_LINE.Height)                                                                                 -- 尺寸
    widget:EnableMouse(true)                                                                                                                                -- 可交互

    widget.bg = widget:CreateTexture(nil, "BACKGROUND")                                                                                                     -- 外边框
    widget.bg:SetAllPoints(widget)                                                                                                                          -- 填满
    widget.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA())                                                                                                 -- 边框色

    widget.art = widget:CreateTexture(nil, "ARTWORK")                                                                                                       -- 内填充
    widget.art:SetPoint("TOPLEFT", widget, "TOPLEFT", SIZE.BUTTON.Border, -SIZE.BUTTON.Border)                                                              -- 内缩
    widget.art:SetPoint("BOTTOMRIGHT", widget, "BOTTOMRIGHT", -SIZE.BUTTON.Border, SIZE.BUTTON.Border)                                                      -- 内缩
    widget.art:SetColorTexture(COLOR.ButtonMouseUp:GetRGBA())                                                                                               -- 背景色

    local slider = CreateFrame("Slider", addonName .. "slider" .. row:GetName(), widget)                                                                    -- 滑块
    slider:SetPoint("LEFT", widget, "LEFT", SIZE.MainFrame.Spacing, 0)                                                                                      -- 左对齐
    slider:SetPoint("RIGHT", widget, "RIGHT", -SIZE.MainFrame.Spacing * 2 - SIZE.SETTING_LINE.SliderValueWidth, 0)                                          -- 右对齐
    slider:SetHeight(SIZE.SETTING_LINE.SliderBarHeight)                                                                                                     -- 高度
    slider:SetOrientation("HORIZONTAL")                                                                                                                     -- 水平
    slider:SetMinMaxValues(minValue, maxValue)                                                                                                              -- 范围
    slider:SetValueStep(step)                                                                                                                               -- 步进
    slider:SetObeyStepOnDrag(true)                                                                                                                          -- 拖动吸附步进

    local bar = CreateFrame("Frame", addonName .. "sliderBar" .. row:GetName(), widget)                                                                     -- 轨道容器
    bar:SetAllPoints(slider)                                                                                                                                -- 同步滑块区域
    bar.left = bar:CreateTexture(nil, "ARTWORK")                                                                                                            -- 左填充
    bar.left:SetPoint("LEFT", bar, "LEFT")                                                                                                                  -- 左对齐
    bar.left:SetHeight(SIZE.SETTING_LINE.SliderBarHeight)                                                                                                   -- 高度
    bar.left:SetColorTexture(COLOR.SliderLeft:GetRGBA())                                                                                                    -- 颜色
    bar.right = bar:CreateTexture(nil, "ARTWORK")                                                                                                           -- 右填充
    bar.right:SetPoint("RIGHT", bar, "RIGHT")                                                                                                               -- 右对齐
    bar.right:SetHeight(SIZE.SETTING_LINE.SliderBarHeight)                                                                                                  -- 高度
    bar.right:SetColorTexture(COLOR.SliderRight:GetRGBA())                                                                                                  -- 颜色

    local thumb = slider:CreateTexture(nil, "ARTWORK")                                                                                                      -- 滑块方块
    thumb:SetSize(SIZE.SETTING_LINE.SliderSquareHeight, SIZE.SETTING_LINE.SliderSquareHeight)                                                               -- 大小
    thumb:SetColorTexture(COLOR.Base:GetRGBA())                                                                                                             -- 颜色
    slider:SetThumbTexture(thumb)                                                                                                                           -- 绑定方块
    local thumbBorder = slider:CreateTexture(nil, "BACKGROUND")                                                                                             -- 方块边框
    thumbBorder:SetSize(SIZE.SETTING_LINE.SliderSquareHeight + SIZE.MainFrame.Border * 2, SIZE.SETTING_LINE.SliderSquareHeight + SIZE.MainFrame.Border * 2) -- 尺寸
    thumbBorder:SetColorTexture(COLOR.ButtonBorder:GetRGBA())                                                                                               -- 颜色
    thumbBorder:SetPoint("CENTER", thumb, "CENTER")                                                                                                         -- 居中

    local valueText = widget:CreateFontString(nil, "OVERLAY")                                                                                               -- 数值文本
    valueText:SetPoint("RIGHT", widget, "RIGHT", -SIZE.MainFrame.Spacing, 0)                                                                                -- 右对齐
    valueText:SetFont(FontPath, GetUIScaleFactor(20), "")                                                                                                   -- 字体
    valueText:SetJustifyH("RIGHT")                                                                                                                          -- 右对齐
    valueText:SetJustifyV("MIDDLE")                                                                                                                         -- 垂直居中
    valueText:SetTextColor(COLOR.Text:GetRGBA())                                                                                                            -- 文字色

    local function ApplySliderVisual(value)                                                                                                                 -- 更新视觉
        local percent = (value - minValue) / (maxValue - minValue)                                                                                          -- 百分比
        local barWidth = bar:GetWidth()                                                                                                                     -- 轨道宽度
        local filled = percent * barWidth                                                                                                                   -- 填充宽度
        bar.left:SetWidth(filled)                                                                                                                           -- 左侧宽度
        bar.right:SetWidth(barWidth - filled)                                                                                                               -- 右侧宽度
        valueText:SetText(FormatStepValue(value, decimals))                                                                                                 -- 显示值
    end                                                                                                                                                     -- ApplySliderVisual 结束

    local function SetSliderValue(value)                                                                                                                    -- 设置数值
        slider:SetValue(value)                                                                                                                              -- 写入滑块
        ApplySliderVisual(value)                                                                                                                            -- 同步视觉
    end                                                                                                                                                     -- SetSliderValue 结束

    slider:SetScript("OnValueChanged", function(sliderFrame, value)                                                                                         -- 拖动时更新
        sliderFrame = sliderFrame or slider                                                                                                                 -- 当前滑块
        ApplySliderVisual(sliderFrame:GetValue())                                                                                                           -- 更新视觉
    end)                                                                                                                                                    -- 拖动回调结束
    slider:SetScript("OnMouseUp", function()                                                                                                                -- 鼠标抬起时写入配置
        if config then                                                                                                                                      -- 有配置对象
            config:set_value(slider:GetValue())                                                                                                             -- 写入配置
        end                                                                                                                                                 -- 配置判断结束
    end)                                                                                                                                                    -- 鼠标抬起回调结束

    local initialValue = row_info.default_value                                                                                                             -- 默认值
    if config then                                                                                                                                          -- 有配置对象
        initialValue = config:get_value()                                                                                                                   -- 从配置取当前值
    end                                                                                                                                                     -- 配置读取结束
    SetSliderValue(initialValue)                                                                                                                            -- 初始化显示

    if config then                                                                                                                                          -- 绑定外部回调
        config:register_callback(function(value)                                                                                                            -- 配置变更时
            SetSliderValue(value)                                                                                                                           -- 同步滑块
        end)                                                                                                                                                -- 回调注册结束
    end                                                                                                                                                     -- 外部回调结束
    return row                                                                                                                                              -- 返回行
end                                                                                                                                                         -- AddSliderRow 结束

local function CreateDropdownControl(row, options, defaultValue, config)                                                                                    -- 创建下拉控件
    if not row then                                                                                                                                         -- 行不存在
        return nil                                                                                                                                          -- 直接返回
    end                                                                                                                                                     -- 行检查结束                                                                                                             -- 尺寸表
    local ownerFrame = Panel.Frame or row:GetParent()                                                                                                       -- 列表容器

    local widget = CreateFrame("Frame", addonName .. "dropdownWidget" .. row:GetName(), row)                                                                -- 控件容器
    widget:SetPoint("LEFT", row.title, "RIGHT", SIZE.SETTING_LINE.Spacing, 0)                                                                               -- 定位
    widget:SetSize(SIZE.SETTING_LINE.WidgetWidth, SIZE.SETTING_LINE.Height)                                                                                 -- 尺寸
    widget:EnableMouse(true)                                                                                                                                -- 可交互

    widget.bg = widget:CreateTexture(nil, "BACKGROUND")                                                                                                     -- 外边框
    widget.bg:SetAllPoints(widget)                                                                                                                          -- 填满
    widget.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA())                                                                                                 -- 颜色

    widget.art = widget:CreateTexture(nil, "ARTWORK")                                                                                                       -- 内填充
    widget.art:SetPoint("TOPLEFT", widget, "TOPLEFT", SIZE.BUTTON.Border, -SIZE.BUTTON.Border)                                                              -- 内缩
    widget.art:SetPoint("BOTTOMRIGHT", widget, "BOTTOMRIGHT", -SIZE.BUTTON.Border, SIZE.BUTTON.Border)                                                      -- 内缩
    widget.art:SetColorTexture(COLOR.ButtonMouseUp:GetRGBA())                                                                                               -- 颜色

    local valueText = widget:CreateFontString(nil, "OVERLAY")                                                                                               -- 显示文本
    valueText:SetPoint("LEFT", widget, "LEFT", SIZE.MainFrame.Spacing, 0)                                                                                   -- 左对齐
    valueText:SetPoint("RIGHT", widget, "RIGHT", -SIZE.MainFrame.Spacing, 0)                                                                                -- 右对齐
    valueText:SetFont(FontPath, GetUIScaleFactor(20), "")                                                                                                   -- 字体
    valueText:SetJustifyH("LEFT")                                                                                                                           -- 左对齐
    valueText:SetJustifyV("MIDDLE")                                                                                                                         -- 垂直居中
    valueText:SetTextColor(COLOR.Text:GetRGBA())                                                                                                            -- 文字色

    local listFrame = CreateFrame("Frame", addonName .. "dropdownList" .. row:GetName(), ownerFrame)                                                        -- 列表容器
    listFrame:SetPoint("TOPLEFT", widget, "BOTTOMLEFT", 0, -SIZE.SETTING_LINE.Spacing / 2)                                                                  -- 位置
    listFrame:SetPoint("TOPRIGHT", widget, "BOTTOMRIGHT", 0, -SIZE.SETTING_LINE.Spacing / 2)                                                                -- 位置
    listFrame:SetHeight(#options * SIZE.SETTING_LINE.Height)                                                                                                -- 高度
    listFrame:SetFrameStrata("TOOLTIP")                                                                                                                     -- 层级
    listFrame:SetFrameLevel(920)                                                                                                                            -- 层级
    listFrame:Hide()                                                                                                                                        -- 初始隐藏

    listFrame.bg, listFrame.art = UI.ApplyBorderAndFill(listFrame, COLOR.ButtonBorder, COLOR.DropdownBg, SIZE.MainFrame.Border)                             -- 边框

    local function FindIndexByValue(value)                                                                                                                  -- 根据 k 查找索引
        for i, option in ipairs(options) do                                                                                                                 -- 遍历选项
            if option.k == value then                                                                                                                       -- 命中
                return i                                                                                                                                    -- 返回索引
            end                                                                                                                                             -- 命中判断结束
        end                                                                                                                                                 -- 遍历结束
        return nil                                                                                                                                          -- 未找到
    end                                                                                                                                                     -- FindIndexByValue 结束

    local function SetDropdownValue(value, fromUser)                                                                                                        -- 设置显示与写入
        local index = FindIndexByValue(value) or 1                                                                                                          -- 找索引
        local option = options[index]                                                                                                                       -- 选项对象
        if not option then                                                                                                                                  -- 无选项
            return                                                                                                                                          -- 直接退出
        end                                                                                                                                                 -- 选项检查结束
        valueText:SetText(option.v)                                                                                                                         -- 显示文本
        if fromUser and config then                                                                                                                         -- 用户点击且有配置
            config:set_value(option.k)                                                                                                                      -- 写入配置
        end                                                                                                                                                 -- 写入判断结束
    end                                                                                                                                                     -- SetDropdownValue 结束

    for i, option in ipairs(options) do                                                                                                                     -- 渲染每个选项
        local item = CreateFrame("Frame", addonName .. "dropdownItem" .. row:GetName() .. i, listFrame)                                                     -- 选项行
        item:SetPoint("TOPLEFT", listFrame, "TOPLEFT", SIZE.MainFrame.Border, -SIZE.MainFrame.Border - (i - 1) * SIZE.SETTING_LINE.Height)                  -- 定位
        item:SetPoint("TOPRIGHT", listFrame, "TOPRIGHT", -SIZE.MainFrame.Border, -SIZE.MainFrame.Border - (i - 1) * SIZE.SETTING_LINE.Height)               -- 定位
        item:SetHeight(SIZE.SETTING_LINE.Height)                                                                                                            -- 行高
        item:EnableMouse(true)                                                                                                                              -- 可点击

        item.bg = item:CreateTexture(nil, "BACKGROUND")                                                                                                     -- 背景
        item.bg:SetAllPoints(item)                                                                                                                          -- 填满
        item.bg:SetColorTexture(0, 0, 0, 0)                                                                                                                 -- 默认透明

        item.text = item:CreateFontString(nil, "OVERLAY")                                                                                                   -- 文本
        item.text:SetPoint("LEFT", item, "LEFT", SIZE.MainFrame.Spacing, 0)                                                                                 -- 左对齐
        item.text:SetPoint("RIGHT", item, "RIGHT", -SIZE.MainFrame.Spacing, 0)                                                                              -- 右对齐
        item.text:SetFont(FontPath, GetUIScaleFactor(20), "")                                                                                               -- 字体
        item.text:SetJustifyH("LEFT")                                                                                                                       -- 左对齐
        item.text:SetJustifyV("MIDDLE")                                                                                                                     -- 垂直居中
        item.text:SetTextColor(COLOR.Text:GetRGBA())                                                                                                        -- 文字色
        item.text:SetText(option.v)                                                                                                                         -- 选项文本

        item:SetScript("OnEnter", function()                                                                                                                -- 悬停
            item.bg:SetColorTexture(COLOR.RowHover:GetRGBA())                                                                                               -- 高亮
        end)                                                                                                                                                -- 悬停结束
        item:SetScript("OnLeave", function()                                                                                                                -- 离开
            item.bg:SetColorTexture(0, 0, 0, 0)                                                                                                             -- 还原
        end)                                                                                                                                                -- 离开结束
        item:SetScript("OnMouseDown", function()                                                                                                            -- 点击
            SetDropdownValue(option.k, true)                                                                                                                -- 设置并写入
            listFrame:Hide()                                                                                                                                -- 隐藏列表
        end)                                                                                                                                                -- 点击结束
    end                                                                                                                                                     -- 选项渲染结束

    local function ToggleList()                                                                                                                             -- 切换列表显示
        if #options <= 0 then                                                                                                                               -- 无选项
            return                                                                                                                                          -- 直接退出
        end                                                                                                                                                 -- 无选项判断结束
        UI.ToggleFrame(listFrame)                                                                                                                           -- 切换显示
    end                                                                                                                                                     -- ToggleList 结束

    row:SetScript("OnMouseDown", ToggleList)                                                                                                                -- 行点击切换
    widget:SetScript("OnMouseDown", ToggleList)                                                                                                             -- 控件点击切换

    SetDropdownValue(defaultValue, false)                                                                                                                   -- 初始化显示
    return widget, SetDropdownValue                                                                                                                         -- 返回控件与设置函数
end                                                                                                                                                         -- CreateDropdownControl 结束

local function AddComboRow(row_info)                                                                                                                        -- 创建下拉框行
    local config = row_info.bind_config                                                                                                                     -- 绑定配置
    ApplyDefaultValue(config, row_info.default_value)                                                                                                       -- 只设一次默认值

    local row = CreateSettingRow(row_info.name, row_info.tooltip)                                                                                           -- 创建行
    if not row then                                                                                                                                         -- 创建失败
        return nil                                                                                                                                          -- 直接返回
    end                                                                                                                                                     -- 行创建检查结束

    local setValue = select(2, CreateDropdownControl(row, row_info.options, row_info.default_value, config))                                                -- 创建控件
    if config then                                                                                                                                          -- 绑定配置
        setValue(config:get_value(), false)                                                                                                                 -- 同步当前值
        config:register_callback(function(value)                                                                                                            -- 配置变化回调
            setValue(value, false)                                                                                                                          -- 同步显示
        end)                                                                                                                                                -- 回调注册结束
    end                                                                                                                                                     -- 配置绑定结束
    return row                                                                                                                                              -- 返回行
end                                                                                                                                                         -- AddComboRow 结束



local function NormalizeSpellID(value) -- 规范化 SpellID
    local numberValue = tonumber(value) -- 转数字
    if not numberValue then -- 非数字
        return nil -- 直接返回
    end -- 数字判断结束
    numberValue = floor(numberValue) -- 取整
    if numberValue <= 0 then -- 只接受正数
        return nil -- 直接返回
    end -- 正数判断结束
    return numberValue -- 返回规范化 ID
end -- NormalizeSpellID 结束

local function CopySpellList(source) -- 复制技能表
    local copy = {} -- 新表
    if type(source) ~= "table" then -- 非表直接返回空
        return copy -- 返回空表
    end -- 类型判断结束
    for rawSpellID, enabled in pairs(source) do -- 遍历源表
        if enabled then -- 只复制 true 项
            local spellID = NormalizeSpellID(rawSpellID) -- 规范化
            if spellID then -- 有效则写入
                copy[spellID] = true -- 写入新表
            end -- 有效判断结束
        end -- enabled 判断结束
    end -- 遍历结束
    return copy -- 返回新表
end -- CopySpellList 结束

local function CollectSpellIDs(spellList) -- 收集技能 ID 数组
    local spellIDs = {} -- ID 数组
    if type(spellList) ~= "table" then -- 非表返回空
        return spellIDs -- 返回空数组
    end -- 类型判断结束
    for rawSpellID, enabled in pairs(spellList) do -- 遍历表
        if enabled then -- 只保留 true
            local spellID = NormalizeSpellID(rawSpellID) -- 规范化
            if spellID then -- 有效则插入
                insert(spellIDs, spellID) -- 写入数组
            end -- 有效判断结束
        end -- enabled 判断结束
    end -- 遍历结束
    return spellIDs -- 返回数组
end -- CollectSpellIDs 结束

local function EnsureSpellListEditorFrame() -- 确保编辑器存在
    if Panel.SpellListEditorFrame then -- 已创建
        return Panel.SpellListEditorFrame -- 直接返回
    end -- 已创建判断结束
    if not Panel.Frame then -- 主面板未创建
        return nil -- 直接返回
    end -- 主面板判断结束

    local scale = 4 -- UI 缩放基准
    local maxRows = 15 -- 列表最大行数
    local lineHeight = SIZE.SETTING_LINE.Height -- 行高
    local panelWidth = GetUIScaleFactor(scale * 120) -- 编辑器宽度
    local panelHeight = GetUIScaleFactor(scale * 152) + lineHeight -- 编辑器高度
    local spacing = SIZE.MainFrame.Spacing -- 间距
    local border = SIZE.MainFrame.Border -- 边框
    local iconFallback = 61304 -- 备用图标

    local frame = CreateFrame("Frame", addonName .. "spellListEditorFrame", UIParent) -- 编辑器框体
    frame:SetPoint("TOPLEFT", Panel.Frame, "TOPRIGHT", 0, 0) -- 放在主面板右侧
    frame:SetSize(panelWidth, panelHeight) -- 尺寸
    frame:SetFrameStrata("TOOLTIP") -- 层级
    frame:SetFrameLevel(905) -- 层级
    frame:Hide() -- 默认隐藏

    frame.bg, frame.art = UI.ApplyBorderAndFill(frame, COLOR.WindowBorder, COLOR.WindowBg, SIZE.MainFrame.Border) -- 边框

    local contentWidth = panelWidth - spacing * 2 -- 内容区宽度
    local actionButtonWidth = GetUIScaleFactor(64) -- 按钮宽度
    local actionGap = spacing -- 按钮间距
    local inputWidth = contentWidth - actionButtonWidth * 2 - actionGap * 2 -- 输入框宽度
    local addButtonX = spacing -- 新增按钮 X
    local deleteButtonX = addButtonX + actionButtonWidth + actionGap -- 删除按钮 X
    local inputX = deleteButtonX + actionButtonWidth + actionGap -- 输入框 X
    local inputRowY = -(spacing * 2 + lineHeight) -- 输入行 Y
    local listTopY = -(spacing * 3 + lineHeight * 2) -- 列表顶部 Y

    frame.titleText = frame:CreateFontString(nil, "OVERLAY") -- 标题文本
    frame.titleText:SetPoint("TOPLEFT", frame, "TOPLEFT", spacing, -spacing) -- 定位
    frame.titleText:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -spacing, -spacing) -- 定位
    frame.titleText:SetHeight(lineHeight) -- 高度
    frame.titleText:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    frame.titleText:SetJustifyH("CENTER") -- 水平居中
    frame.titleText:SetJustifyV("MIDDLE") -- 垂直居中
    frame.titleText:SetTextColor(COLOR.Text:GetRGBA()) -- 文字色
    frame.titleText:SetText("法术列表") -- 文案

    frame.spellIDBox = CreateFrame("EditBox", addonName .. "spellListInputBox", frame) -- 输入框
    frame.spellIDBox:SetPoint("TOPLEFT", frame, "TOPLEFT", inputX, inputRowY) -- 定位
    frame.spellIDBox:SetSize(inputWidth, lineHeight) -- 尺寸
    frame.spellIDBox:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    frame.spellIDBox:SetJustifyH("LEFT") -- 左对齐
    frame.spellIDBox:SetJustifyV("MIDDLE") -- 垂直居中
    frame.spellIDBox:SetTextColor(COLOR.Text:GetRGBA()) -- 文字色
    frame.spellIDBox:SetAutoFocus(false) -- 不自动聚焦
    frame.spellIDBox:SetMultiLine(false) -- 单行
    frame.spellIDBox:SetTextInsets(spacing, spacing, 0, 0) -- 内边距

    frame.spellIDBox.bg = frame.spellIDBox:CreateTexture(nil, "BACKGROUND") -- 输入框边框
    frame.spellIDBox.bg:SetAllPoints(frame.spellIDBox) -- 填满
    frame.spellIDBox.bg:SetColorTexture(COLOR.ButtonBorder:GetRGBA()) -- 边框色

    frame.spellIDBox.art = frame.spellIDBox:CreateTexture(nil, "ARTWORK") -- 输入框填充
    frame.spellIDBox.art:SetPoint("TOPLEFT", frame.spellIDBox, "TOPLEFT", SIZE.BUTTON.Border, -SIZE.BUTTON.Border) -- 内缩
    frame.spellIDBox.art:SetPoint("BOTTOMRIGHT", frame.spellIDBox, "BOTTOMRIGHT", -SIZE.BUTTON.Border, SIZE.BUTTON.Border) -- 内缩
    frame.spellIDBox.art:SetColorTexture(COLOR.ButtonMouseUp:GetRGBA()) -- 填充色

    frame.spellIDBox:SetScript("OnEnterPressed", function(self) -- 回车取消焦点
        self:ClearFocus() -- 清理焦点
    end) -- 回车回调结束
    frame.spellIDBox:SetScript("OnEscapePressed", function(self) -- ESC 取消焦点
        self:ClearFocus() -- 清理焦点
    end) -- ESC 回调结束

    frame.addButton = UI.CreateButton(frame, "spellListAddButton", addButtonX, inputRowY, actionButtonWidth, SIZE.BUTTON.Height, "新增") -- 新增按钮
    frame.deleteButton = UI.CreateButton(frame, "spellListDeleteButton", deleteButtonX, inputRowY, actionButtonWidth, SIZE.BUTTON.Height, "删除") -- 删除按钮

    frame.listFrame = CreateFrame("Frame", addonName .. "spellListListFrame", frame) -- 列表容器
    frame.listFrame:SetPoint("TOPLEFT", frame, "TOPLEFT", spacing, listTopY) -- 定位
    frame.listFrame:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -spacing, spacing) -- 定位
    frame.listFrame:EnableMouseWheel(true) -- 支持滚轮
    frame.listFrame.bg, frame.listFrame.art = UI.ApplyBorderAndFill(frame.listFrame, COLOR.ButtonBorder, COLOR.DropdownBg, border) -- 边框

    frame.emptyText = frame.listFrame:CreateFontString(nil, "OVERLAY") -- 空文本
    frame.emptyText:SetPoint("CENTER", frame.listFrame, "CENTER") -- 居中
    frame.emptyText:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
    frame.emptyText:SetJustifyH("CENTER") -- 居中
    frame.emptyText:SetJustifyV("MIDDLE") -- 居中
    frame.emptyText:SetTextColor(0.65, 0.65, 0.65) -- 文字色
    frame.emptyText:SetText("暂无数据") -- 文案
    frame.emptyText:Hide() -- 默认隐藏

    frame.rows = {} -- 行数组
    for i = 1, maxRows do -- 创建固定行
        local row = CreateFrame("Frame", addonName .. "spellListRow" .. i, frame.listFrame) -- 行框体
        row:SetPoint("TOPLEFT", frame.listFrame, "TOPLEFT", border, -border - (i - 1) * lineHeight) -- 定位
        row:SetPoint("TOPRIGHT", frame.listFrame, "TOPRIGHT", -border, -border - (i - 1) * lineHeight) -- 定位
        row:SetHeight(lineHeight) -- 行高
        row:EnableMouse(true) -- 可交互
        row:EnableMouseWheel(true) -- 支持滚轮

        row.bg = row:CreateTexture(nil, "BACKGROUND") -- 行背景
        row.bg:SetAllPoints(row) -- 填满
        row.bg:SetColorTexture(0, 0, 0, 0) -- 默认透明

        row.icon = row:CreateTexture(nil, "ARTWORK") -- 图标
        row.icon:SetPoint("LEFT", row, "LEFT", spacing, 0) -- 定位
        row.icon:SetSize(lineHeight - border * 2, lineHeight - border * 2) -- 尺寸
        row.icon:SetTexture(iconFallback) -- 默认图标

        row.idText = row:CreateFontString(nil, "OVERLAY") -- ID 文本
        row.idText:SetPoint("RIGHT", row, "RIGHT", -spacing, 0) -- 右对齐
        row.idText:SetFont(FontPath, GetUIScaleFactor(18), "") -- 字体
        row.idText:SetJustifyH("RIGHT") -- 右对齐
        row.idText:SetJustifyV("MIDDLE") -- 垂直居中
        row.idText:SetTextColor(COLOR.Text:GetRGBA()) -- 文字色

        row.nameText = row:CreateFontString(nil, "OVERLAY") -- 名称文本
        row.nameText:SetPoint("LEFT", row.icon, "RIGHT", spacing, 0) -- 左对齐
        row.nameText:SetPoint("RIGHT", row.idText, "LEFT", -spacing, 0) -- 右对齐
        row.nameText:SetFont(FontPath, GetUIScaleFactor(20), "") -- 字体
        row.nameText:SetJustifyH("LEFT") -- 左对齐
        row.nameText:SetJustifyV("MIDDLE") -- 垂直居中
        row.nameText:SetTextColor(COLOR.Text:GetRGBA()) -- 文字色

        frame.rows[i] = row -- 保存行
    end -- 行创建结束

    function frame:_ClampScrollOffset() -- 约束滚动偏移
        local total = self._spellIDs and #self._spellIDs or 0 -- 总数
        local maxOffset = math.max(0, total - maxRows) -- 最大偏移
        if not self._scrollOffset then -- 未设置
            self._scrollOffset = 0 -- 初始化
        end -- 未设置判断结束
        if self._scrollOffset < 0 then -- 下界
            self._scrollOffset = 0 -- 修正
        elseif self._scrollOffset > maxOffset then -- 上界
            self._scrollOffset = maxOffset -- 修正
        end -- 边界判断结束
    end -- _ClampScrollOffset 结束

    function frame:_SetRowVisual(row) -- 更新行高亮
        if row._spellID and self._selectedSpellID == row._spellID then -- 选中行
            row.bg:SetColorTexture(73 / 255, 179 / 255, 234 / 255, 0.35) -- 选中高亮
            return -- 结束
        end -- 选中判断结束
        if row._hovered then -- 悬停行
            row.bg:SetColorTexture(COLOR.RowHover:GetRGBA()) -- 悬停高亮
            return -- 结束
        end -- 悬停判断结束
        row.bg:SetColorTexture(0, 0, 0, 0) -- 默认背景
    end -- _SetRowVisual 结束

    function frame:RefreshList() -- 刷新列表
        self._spellIDs = CollectSpellIDs(self._currentData) -- 生成 ID 列表
        self:_ClampScrollOffset() -- 修正滚动
        if #self._spellIDs == 0 then -- 空列表
            self.emptyText:Show() -- 显示空提示
        else -- 非空列表
            self.emptyText:Hide() -- 隐藏空提示
        end -- 空列表判断结束

        for index, row in ipairs(self.rows) do -- 填充行
            local listIndex = (self._scrollOffset or 0) + index -- 计算真实索引
            local spellID = self._spellIDs[listIndex] -- 当前 ID

            row._spellID = spellID -- 绑定 ID
            row._hovered = false -- 重置悬停
            if spellID then -- 有 ID
                local spellName = GetSpellName(spellID) or "" -- 名称
                local iconID = GetSpellTexture(spellID) or iconFallback -- 图标
                row.icon:SetTexture(iconID) -- 设置图标
                row.nameText:SetText(spellName) -- 设置名称
                row.idText:SetText(tostring(spellID)) -- 设置 ID
                row:Show() -- 显示
            else -- 无 ID
                row.icon:SetTexture(iconFallback) -- 默认图标
                row.nameText:SetText("") -- 清空名称
                row.idText:SetText("") -- 清空 ID
                row:Hide() -- 隐藏
            end -- 是否有 ID 判断结束
            self:_SetRowVisual(row) -- 更新高亮
        end -- 行遍历结束
    end -- RefreshList 结束

    function frame:BindSetting(setting) -- 绑定设置项
        self._currentSetting = setting -- 当前设置项
        if self.titleText then -- 更新标题
            local title = "法术列表" -- 默认标题
            if type(setting) == "table" then -- 有设置对象
                title = tostring(setting.name or setting.key or title) -- 标题取设置名
            end -- 设置对象判断结束
            self.titleText:SetText(title) -- 设置标题
        end -- 标题更新结束
        if type(setting) ~= "table" or not setting.bind_config then -- 无配置
            self._currentData = {} -- 空数据
        else -- 有配置
            self._currentData = CopySpellList(setting.bind_config:get_value()) -- 读取配置并复制
        end -- 配置判断结束
        self._selectedSpellID = nil -- 清空选中
        self._scrollOffset = 0 -- 归零滚动
        self.spellIDBox:SetText("") -- 清空输入
        self:RefreshList() -- 刷新显示
    end -- BindSetting 结束

    function frame:PersistCurrentValue() -- 写入当前数据
        if type(self._currentSetting) ~= "table" then -- 无设置对象
            return -- 直接退出
        end -- 设置对象判断结束
        local config = self._currentSetting.bind_config -- 取配置
        if not config then -- 无配置
            return -- 直接退出
        end -- 配置判断结束
        config:set_value(CopySpellList(self._currentData)) -- 写入配置
        self._currentData = CopySpellList(config:get_value()) -- 重新读取
    end -- PersistCurrentValue 结束

    local function GetInputSpellID() -- 读取输入框
        local text = frame.spellIDBox:GetText() or "" -- 取文本
        text = text:gsub("%s+", "") -- 去空格
        return NormalizeSpellID(text) -- 规范化
    end -- GetInputSpellID 结束

    frame.addButton:HookScript("OnMouseUp", function() -- 新增按钮
        if type(frame._currentSetting) ~= "table" then -- 无设置
            return -- 直接退出
        end -- 设置判断结束

        local spellID = GetInputSpellID() -- 取输入
        if not spellID then -- 无效输入
            return -- 直接退出
        end -- 输入判断结束

        frame._currentData[spellID] = true -- 写入
        frame._selectedSpellID = spellID -- 选中
        frame.spellIDBox:SetText(tostring(spellID)) -- 回写输入框
        frame:PersistCurrentValue() -- 写入配置
        frame:RefreshList() -- 刷新
    end) -- 新增回调结束

    frame.deleteButton:HookScript("OnMouseUp", function() -- 删除按钮
        if type(frame._currentSetting) ~= "table" then -- 无设置
            return -- 直接退出
        end -- 设置判断结束

        local spellID = GetInputSpellID() -- 取输入
        if not spellID then -- 无效输入
            return -- 直接退出
        end -- 输入判断结束

        frame._currentData[spellID] = nil -- 删除
        if frame._selectedSpellID == spellID then -- 清除选中
            frame._selectedSpellID = nil -- 清空
        end -- 选中判断结束
        frame:PersistCurrentValue() -- 写入配置
        frame:RefreshList() -- 刷新
    end) -- 删除回调结束

    frame.listFrame:SetScript("OnMouseWheel", function(listFrame, delta) -- 列表滚轮
        local editorFrame = listFrame:GetParent()
        if delta > 0 then -- 上滚
            editorFrame._scrollOffset = (editorFrame._scrollOffset or 0) - 1 -- 向上
        else -- 下滚
            editorFrame._scrollOffset = (editorFrame._scrollOffset or 0) + 1 -- 向下
        end -- 滚动方向判断结束
        editorFrame:_ClampScrollOffset() -- 修正
        editorFrame:RefreshList() -- 刷新
    end) -- 滚轮回调结束

    for rowIndex = 1, #frame.rows do -- 行交互
        local row = frame.rows[rowIndex]
        row:SetScript("OnMouseDown", function(self) -- 点击选择
            if not self._spellID then -- 无 ID
                return -- 直接退出
            end -- ID 判断结束
            frame._selectedSpellID = self._spellID -- 选中
            frame.spellIDBox:SetText(tostring(self._spellID)) -- 回写输入框
            frame:RefreshList() -- 刷新
        end) -- 点击回调结束
        row:SetScript("OnEnter", function(self) -- 悬停提示
            if not self._spellID then -- 无 ID
                return -- 直接退出
            end -- ID 判断结束
            self._hovered = true -- 标记悬停
            frame:_SetRowVisual(self) -- 更新高亮

            local spellID = self._spellID -- 当前 ID
            local spellName = GetSpellName(spellID) or "未知技能" -- 名称
            local description = GetSpellDescription(spellID) -- 描述
            if not description or description == "" then -- 无描述
                description = "无描述" -- 兜底描述
            end -- 描述判断结束

            GameTooltip:SetOwner(self, "ANCHOR_RIGHT", spacing, 0) -- 提示位置
            GameTooltip:SetFrameStrata("TOOLTIP") -- 层级
            GameTooltip:SetFrameLevel(1000) -- 层级
            GameTooltip:SetText("SpellID: " .. tostring(spellID), 1, 1, 1, 1, true) -- 标题
            GameTooltip:AddLine(spellName, 0.9, 0.9, 0.9, true) -- 名称
            GameTooltip:AddLine(description, 0.8, 0.8, 0.8, true) -- 描述
            GameTooltip:Show() -- 显示
        end) -- 悬停回调结束
        row:SetScript("OnLeave", function(self) -- 离开提示
            self._hovered = false -- 清除悬停
            frame:_SetRowVisual(self) -- 更新
            GameTooltip:Hide() -- 隐藏
        end) -- 离开回调结束
        row:SetScript("OnMouseWheel", function(rowFrame, delta) -- 行滚轮
            local listMouseWheelScript = frame.listFrame:GetScript("OnMouseWheel")
            if listMouseWheelScript then -- 代理到列表
                listMouseWheelScript(rowFrame:GetParent(), delta) -- 调用列表滚轮
            end -- 代理判断结束
        end) -- 行滚轮回调结束
    end -- 行遍历结束

    Panel.SpellListEditorFrame = frame -- 保存编辑器
    return frame -- 返回编辑器
end -- EnsureSpellListEditorFrame 结束

local function AddSpellListRow(row_info) -- 创建技能列表行
    local config = row_info.bind_config -- 绑定配置
    ApplyDefaultValue(config, row_info.default_value) -- 只设一次默认值

    local row = CreateSettingRow(row_info.name, row_info.tooltip) -- 创建行
    if not row then -- 创建失败
        return nil -- 直接返回
    end -- 行创建判断结束

    local buttonX = SIZE.SETTING_LINE.TitleWidth + SIZE.SETTING_LINE.Spacing -- 按钮 X
    local buttonWidth = SIZE.SETTING_LINE.WidgetWidth -- 按钮宽度
    local button = UI.CreateButton(row, "spellListSettingButton" .. row:GetName(), buttonX, 0, buttonWidth, SIZE.BUTTON.Height, "编辑") -- 编辑按钮
    button:HookScript("OnMouseUp", function() -- 点击打开/关闭
        local editor = EnsureSpellListEditorFrame() -- 获取编辑器
        if not editor then -- 无编辑器
            return -- 直接退出
        end -- 编辑器判断结束
        if editor:IsShown() and editor._currentSetting == row_info then -- 已打开且同一项
            editor:Hide() -- 关闭
            return -- 直接退出
        end -- 同一项判断结束
        editor:Show() -- 打开
        editor:BindSetting(row_info) -- 绑定设置项
    end) -- 点击回调结束

    return row -- 返回行
end -- AddSpellListRow 结束



local function CreatePanelRows()                  -- 构建所有设置行
    for rowIndex = 1, #ConfigRows do              -- 遍历 Rows
        local row_info = ConfigRows[rowIndex]
        if row_info.type == "slider" then         -- 滑块
            AddSliderRow(row_info)                -- 创建滑块行
        elseif row_info.type == "combo" then      -- 下拉
            AddComboRow(row_info)                 -- 创建下拉行
        elseif row_info.type == "spell_list" then -- 技能列表
            AddSpellListRow(row_info)             -- 创建技能列表行
        end                                       -- 分支结束
    end                                           -- Rows 遍历结束
end                                               -- CreatePanelRows 结束

C_Timer.After(1, function()
    CreatePanelFrame()
    CreatePanelRows()
end)
