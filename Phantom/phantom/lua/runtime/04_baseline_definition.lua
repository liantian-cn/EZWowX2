--[[
original: runtime\04_baseline_definition.lua
uuid: d9cf2e29-674c-4ad5-828a-d61d47fbed0d
runtime_index: 4
摘要：
    定义运行时共用的颜色、框架层级与界面尺寸。

描述：
    集中提供光环、施法、基础色和设置面板配色，并按调试开关选择定位标记颜色。
    定义画布、背板、内容、光环和标记的静态层级；将尺寸初始化注册到 UI 初始化队列，
    延后换算 Cell 和设置面板的尺寸，供后续界面组件使用。

修改记录：
2026-09-20：统一九档静态 FrameLevel，直接替换旧层级键。
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateColor = CreateColor  -- 根据 RGBA 分量创建颜色对象
local insert      = table.insert -- 将尺寸初始化函数加入 UI 初始化队列

--[[  variable reference  ]]

local DEBUG            = addonTable.DEBUG            -- 调试开关，用于选择定位标记配色
local GetUIScaleFactor = addonTable.GetUIScaleFactor -- 将物理像素尺寸换算为 UI 尺寸
local scale            = addonTable.SCALE            -- Cell 的显示倍率，调试时放大
local UIInitFuncs      = addonTable.UIInitFuncs      -- 按注册顺序执行的 UI 初始化队列


--[[  logical code  ]]

addonTable.COLOR = {                                                        -- 供其他运行时文件共用的颜色定义
    AURA_TYPE = {                                                           -- 光环
        MAGIC = CreateColor(60 / 255, 100 / 255, 220 / 255, 1),             -- 魔法
        CURSE = CreateColor(100 / 255, 0, 120 / 255, 1),                    -- 诅咒
        DISEASE = CreateColor(160 / 255, 120 / 255, 60 / 255, 1),           -- 疾病
        POISON = CreateColor(154 / 255, 205 / 255, 50 / 255, 1),            -- 中毒
        ENRAGE = CreateColor(230 / 255, 120 / 255, 20 / 255, 1),            -- 激怒
        BLEED = CreateColor(80 / 255, 0, 20 / 255, 1),                      -- 流血
        DEBUFF_ON_FRIENDLY = CreateColor(255 / 255, 60 / 255, 60 / 255, 1), -- 在友方身上的减益,不属于上述状态
        BUFF_ON_FRIENDLY = CreateColor(80 / 255, 220 / 255, 120 / 255, 1),  -- 在友方身上的增益,不属于上述状态
        DEBUFF_ON_ENEMY = CreateColor(105 / 255, 105 / 255, 210 / 255, 1),  -- 在敌方身上的减益,不属于上述状态
    },
    SPELL_TYPE = {                                                          -- 施法状态配色
        PLAYER_SPELL = CreateColor(64 / 255, 158 / 255, 210 / 255, 1),      -- 友方施法
        INTERRUPTIBLE = CreateColor(255 / 255, 255 / 255, 60 / 255, 1),     -- 可打断
        NOT_INTERRUPTIBLE = CreateColor(200 / 255, 0, 0, 1),                -- 不可打断
    },
    NONE = CreateColor(0, 0, 0, 0),                                         -- 无
    RED = CreateColor(255 / 255, 0, 0, 1),                                  -- 红色
    GREEN = CreateColor(0, 255 / 255, 0, 1),                                -- 绿色
    BLUE = CreateColor(0, 0, 255 / 255, 1),                                 -- 蓝色
    BLACK = CreateColor(0, 0, 0, 1),                                        -- 黑色
    WHITE = CreateColor(1, 1, 1, 1),                                        -- 白色
    TRANSPARENT = CreateColor(0, 0, 0, 0),                                  -- 透明
    PANEL = {                                                               -- 面板的UI配色
        Black           = CreateColor(0 / 255, 0 / 255, 0 / 255, 1),        -- 纯黑
        WindowBg        = CreateColor(30 / 255, 30 / 255, 30 / 255, 1),     -- 窗口背景色
        WindowText      = CreateColor(0 / 255, 0 / 255, 0 / 255, 1),        -- 窗口文字色（备用）
        WindowBorder    = CreateColor(83 / 255, 88 / 255, 91 / 255, 1),     -- 窗口边框色
        Base            = CreateColor(255 / 255, 255 / 255, 255 / 255, 1),  -- 基础白
        ButtonBorder    = CreateColor(52 / 255, 52 / 255, 52 / 255, 1),     -- 按钮边框色
        ButtonHighlight = CreateColor(86 / 255, 86 / 255, 86 / 255, 1),     -- 按钮悬停高亮
        ButtonMouseUp   = CreateColor(43 / 255, 43 / 255, 43 / 255, 1),     -- 按钮正常底色
        ButtonMouseDown = CreateColor(37 / 255, 37 / 255, 37 / 255, 1),     -- 按钮按下底色
        SliderLeft      = CreateColor(73 / 255, 179 / 255, 234 / 255, 1),   -- 滑块已填充色
        SliderRight     = CreateColor(159 / 255, 159 / 255, 159 / 255, 1),  -- 滑块未填充色
        RowHover        = CreateColor(50 / 255, 50 / 255, 50 / 255, 1),     -- 行悬停色
        Text            = CreateColor(230 / 255, 230 / 255, 230 / 255, 1),  -- 文本颜色
        DropdownBg      = CreateColor(34 / 255, 34 / 255, 34 / 255, 1),     -- 下拉列表背景色
    }
}

--[[
标记位颜色
调试模式使用亮绿和亮红，便于肉眼辨别。
常规模式使用两种接近黑色的颜色作为定位标记。

]]
if DEBUG then                                                   -- 调试模式以高对比度展示定位标记
    addonTable.COLOR.MARK = {                                   -- 画布定位标记配色
        POINT_0 = CreateColor(0, 255 / 255, 0, 1),              -- 定位标记的第一种颜色：亮绿色
        POINT_1 = CreateColor(255 / 255, 0, 0, 1),              -- 定位标记的第二种颜色：亮红色
    }
else                                                            -- 常规模式降低定位标记的视觉亮度
    addonTable.COLOR.MARK = {                                   -- 画布定位标记配色
        POINT_0 = CreateColor(15 / 255, 25 / 255, 20 / 255, 1), -- 接近黑色的定位标记
        POINT_1 = CreateColor(25 / 255, 15 / 255, 20 / 255, 1), -- 接近黑色的定位标记
    }
end

--[[
框架层级：画布、分隔、背板、内容、光环及标记使用固定间隔；Overlay 仅预留。
- 基础为9500
]]


addonTable.FrameLevel = { -- 供界面组件统一使用的框架层级
    Canvas = 9500,        -- 共享画布
    Separator = 9550,     -- 数值条红色分隔
    Backplate = 9600,     -- 固定黑色背板
    Content = 9650,       -- 普通数值条与吸收条
    AuraContainer = 9700, -- 光环容器
    AuraButton = 9750,    -- 光环槽位
    AuraContent = 9800,   -- 光环槽位内部数值条
    Overlay = 9850,       -- 预留层级，当前不创建框体
    Marker = 9900,        -- 定位与检测标记

}


--[[
尺寸表：在延后执行的 UI 初始化队列中计算，供后续注册的界面初始化函数读取。
]]
addonTable.SIZE = {}                                              -- 尺寸表
local function InitializeSize()                                   -- 初始化尺寸
    local SIZE = addonTable.SIZE                                  -- 执行初始化时取得当前共享尺寸表
    SIZE.CELL = GetUIScaleFactor(scale * 4)                       -- Cell 边长，包含调试显示倍率
    SIZE.PANEL = {                                                -- 游戏内设置面板尺寸
        MainFrame = {                                             -- 主框体尺寸
            Width = GetUIScaleFactor(400),                        -- 主框体宽度
            Height = GetUIScaleFactor(16) + GetUIScaleFactor(36), -- 主框体初始高度，由 16 与 36 像素分别换算后相加
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
    }
end
insert(UIInitFuncs, InitializeSize) -- 注册尺寸计算，先于后续文件的界面初始化执行
