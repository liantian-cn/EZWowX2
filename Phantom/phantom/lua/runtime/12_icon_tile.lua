--[[
original: runtime\12_icon_tile.lua
uuid: 8bf43429-5d8b-4fd4-82af-6ad13b6e0789
runtime_index: 12
摘要：
    在像素画布第四行创建图标槽位，提供图标、类型角标更新和清空接口。

描述：
    在已创建的共享背景上构建黑色背景、图标与类型角标三层纹理。
    x 为从 1 开始的 IconTile 槽位编号，每个槽位边长为两个 Cell，默认尺寸为 8×8。
    槽位固定向下偏移三个 Cell；跳过左侧一个 Cell 的检测列后，按 1、2、3 等编号紧密排列。
    IconTileBackplate 独立登记两个 Cell 的行宽，并更新背景尺寸。
    图标与角标初始隐藏，分别通过 SetIcon 和 SetBorderColor 更新并显示。
    Clear 隐藏图标与角标、保留黑底，不释放槽位，也不重置已保存的纹理和颜色。

修改记录：
2026-09-20：复用独立背板的框体与固定黑底纹理。
2026-09-07：liantian-cn初始化创建。

]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame              = CreateFrame                          -- 创建框体
local CreateColor              = CreateColor                          -- 创建 RGBA 颜色对象

--[[  variable reference  ]]

local IconTileBackplate      = addonTable.IconTileBackplate -- 固定黑色背板构造器
local FrameLevel            = addonTable.FrameLevel            -- 背景与 Cell 底层框体的层级定义
local SIZE                  = addonTable.SIZE                  -- 共享 Cell 尺寸定义
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 按共享长度数据调整背景尺寸

--[[  logical code  ]]

---@class IconTile
---@field Backplate IconTileBackplate 固定黑色背板
---@field Frame Frame 图标框体
---@field Background Texture 背景纹理
---@field Icon Texture 图标纹理
---@field Border Texture 边框纹理
---@field BorderColor ColorMixin 边框颜色
local IconTile = {} -- 图标槽位实例的共享方法表
IconTile.__index = IconTile -- 实例通过元表访问共享方法



---IconTile 初始化方法（私有）
---@private
---@param x integer 从 1 开始的 IconTile 槽位编号
function IconTile:_initialize(x) -- 创建第四行槽位并更新共享行宽
    self.Backplate = IconTileBackplate:New(x) -- 背板独立负责几何与计数
    local backgroundFrame = self.Backplate.Frame -- 三层纹理共用内容框体
    local backgroundBg = self.Backplate.BackgroundTexture -- 保留旧 Background 字段语义

    -- 图标层
    local icon = backgroundFrame:CreateTexture(nil, "ARTWORK") -- 在黑底上方创建图标纹理
    icon:SetAllPoints(backgroundFrame) -- 使图标覆盖整个槽位
    icon:Hide() -- 初始不显示图标

    -- 边框层
    local border = backgroundFrame:CreateTexture(nil, "OVERLAY") -- 在图标上方创建类型角标纹理
    border:SetAllPoints(backgroundFrame) -- 将角标纹理映射到整个槽位
    border:SetTexture("Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga") -- 加载插件内的类型角标资源
    border:SetVertexColor(0, 0, 0, 0) -- 默认透明
    border:Hide() -- 初始不显示类型角标

    self.Frame = backgroundFrame -- 保存槽位框体
    self.Background = backgroundBg -- 保存清空时保留的黑底纹理
    self.Icon = icon -- 保存后续更新的图标纹理
    self.Border = border -- 保存后续着色的类型角标纹理
    self.BorderColor = CreateColor(0, 0, 0, 0) -- 默认透明
end

---创建图标槽位；调用前须已创建 addonTable.BackgroundFrame
---@param x integer 从 1 开始的 IconTile 槽位编号，每槽宽两个 Cell
---@return IconTile # 返回IconTile实例
function IconTile:New(x) -- 按槽位编号构造独立图标槽位
    local instance = setmetatable({}, self) -- 创建继承共享方法的实例
    instance:_initialize(x) -- 创建槽位纹理并登记占位宽度
    return instance -- 返回初始化完成的槽位实例
end

---设置图标纹理
---@param iconID number|string 图标ID或纹理路径
function IconTile:SetIcon(iconID) -- 更新并显示图标，保留现有角标状态
    self.Icon:SetTexture(iconID) -- 设置图标资源
    self.Icon:Show() -- 显示图标纹理
end

---设置边框颜色
---@param color ColorMixin 颜色对象
function IconTile:SetBorderColor(color) -- 更新并显示类型角标，保留现有图标状态
    self.BorderColor = color -- 保存当前角标颜色对象
    self.Border:SetVertexColor(color:GetRGBA()) -- 将颜色及透明度应用到角标纹理
    self.Border:Show() -- 显示类型角标纹理
end

---隐藏图标与角标，保留黑底和槽位占位
function IconTile:Clear() -- 清空可见内容，保留槽位占位及已保存的资源
    self.Icon:Hide() -- 隐藏图标，露出黑底
    self.Border:Hide() -- 隐藏类型角标
end

addonTable.IconTile = IconTile -- 向后续模块公开图标槽位接口
