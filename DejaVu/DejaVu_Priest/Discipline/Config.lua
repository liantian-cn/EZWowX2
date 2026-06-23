local addonName, addonTable             = ... -- 插件入口固定写法

-- Lua 原生函数
local insert                            = table.insert

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "PRIEST" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是牧师则停止
if currentSpec ~= 1 then return end -- 不是戒律专精则停止

local DejaVu = _G["DejaVu"]
local Config = DejaVu.Config
local ConfigRows = DejaVu.ConfigRows
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


do
    local use_mana_balance = Config("use_mana_balance")
    insert(ConfigRows, {
        type = "combo",
        key = "use_mana_balance",
        name = "使用法力平衡",
        tooltip = "选择是否使用法力平衡\n启用后将根据法力值调整阈值",
        default_value = "no",
        options = {
            { k = "yes", v = "是" },
            { k = "no", v = "否" }
        },
        bind_config = use_mana_balance,
    })



    local function InitFrame()
        local use_mana_balance_cell = Cell:New(55, 12)

        -- 说明：根据打断模式配置更新显示强度。
        -- 依赖事件更新：无
        -- 依赖定时刷新：无
        local function set_use_mana_balance(value)
            if value == "yes" then
                use_mana_balance_cell:setCellRGBA(255 / 255)
            else
                use_mana_balance_cell:setCellRGBA(127 / 255)
            end
        end

        use_mana_balance:register_callback(set_use_mana_balance)

        set_use_mana_balance(use_mana_balance:get_value() or "no") -- 初始化时根据当前配置值更新显示
    end
    insert(MartixInitFuncs, InitFrame)
end
