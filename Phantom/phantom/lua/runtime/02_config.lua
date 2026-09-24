--[[
original: runtime\02_config.lua
uuid: 623444a0-7dad-4fe6-8554-21d6753c6773
runtime_index: 2
摘要：按配置档案保存配置值，并提供默认值读取、配置对象缓存与变更回调。

描述：
    - 第 2 个加载的 Lua 文件，初始化以插件名称命名的 Settings 表及当前配置档案。
    - 配置对象按 key 复用；读取时优先使用当前档案中的值，未设置时使用对象默认值。
    - 写入配置或切换档案时通知已注册的回调；切换至新档案时创建空表，已有档案保留数据。
    - 向插件命名空间提供 Config 工厂和 ConfigRows 表，供后续文件定义配置与界面条目。


修改记录：
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local _G = _G -- Lua 全局环境表，用于按插件名称读写设置
local insert = table.insert -- 向配置对象列表或回调列表追加元素
local setmetatable = setmetatable -- 为配置实例设置方法查找元表

--[[  variable reference  ]]
-- 本文件无需缓存其他文件提供的内部引用。


--[[  logical code  ]]

_G[addonName .. "Settings"] = _G[addonName .. "Settings"] or {} -- 复用已加载的插件设置，缺失时创建

local addonSettings = _G[addonName .. "Settings"] -- 当前插件的设置数据表

addonSettings.profiles = addonSettings.profiles or {} -- 按档案名称保存配置数据
addonSettings.profiles["default"] = addonSettings.profiles["default"] or {} -- 确保默认档案存在
addonSettings.current_profile = addonSettings.current_profile or "default" -- 保留当前档案名称，未设置时选用默认档案


local all_configs = {} -- 已创建的配置对象，切换档案时逐一通知
local Profile = {} -- 文件内的档案管理接口

-- 获取当前profile名称
function Profile.current_profile() -- 读取当前档案名称
    return addonSettings.current_profile -- 返回当前选中的档案名称
end

-- 切换 profile：已有档案保留数据，新档案中的配置使用各自默认值
function Profile.switch_profile(name) -- 切换档案并通知所有配置对象
    -- 如果profile不存在, 创建一个空表
    if not addonSettings.profiles[name] then -- 目标档案尚未创建
        addonSettings.profiles[name] = {} -- 新档案暂不保存任何显式配置值
    end

    -- 切换当前profile
    addonSettings.current_profile = name -- 后续配置读写均指向该档案

    -- 通知所有config回调
    for configIndex = 1, #all_configs do -- 按注册顺序通知配置对象
        local config = all_configs[configIndex] -- 取出本次需要通知的配置对象
        config:_notify() -- 将新档案下的配置值传给该对象的回调
    end
end

-- 内部函数: 注册config对象
function Profile._register_config(config) -- 登记参与档案切换通知的配置对象
    insert(all_configs, config) -- 将配置对象纳入档案切换通知列表
end

-- 获取当前profile的数据表（内部使用）
function Profile._get_current_data() -- 取得当前档案的配置数据表
    return addonSettings.profiles[addonSettings.current_profile] -- 返回当前档案的配置数据
end

-- 缓存所有config对象, 相同key返回同一对象
local config_cache = {} -- 按配置 key 保存唯一配置对象

-- Config对象
local ConfigObj = {} -- 配置对象的方法集合
ConfigObj.__index = ConfigObj -- 实例从该表查找配置操作方法

-- 创建新的config对象
function ConfigObj:new(key) -- 按配置键创建对象
    local obj = { -- 保存配置键、默认值与回调列表
        key = key, -- 当前配置在档案数据中的索引
        default_value = nil, -- 档案未设置该配置时使用的默认值
        callbacks = {} -- 按注册顺序保存值通知回调
    }
    setmetatable(obj, self) -- 让新实例共享配置对象方法
    return obj -- 返回尚未注册到缓存的新配置实例
end

-- 设置默认值
function ConfigObj:set_default(value) -- 设置档案未赋值时使用的默认值
    self.default_value = value -- 更新回退值，本操作不触发回调
end

-- 获取当前值（优先从profile读取, 没有则返回默认值）
function ConfigObj:get_value() -- 读取当前档案值或默认值
    local data = Profile._get_current_data() -- 获取当前档案的配置数据表
    if data[self.key] ~= nil then -- 仅 nil 表示未设置，false 等显式值仍有效
        return data[self.key] -- 优先使用档案内保存的值
    end
    return self.default_value -- 档案未保存该配置时使用默认值
end

-- 设置值（写入当前profile, 触发回调）
function ConfigObj:set_value(value) -- 写入当前档案并通知回调
    local data = Profile._get_current_data() -- 获取当前档案的配置数据表
    data[self.key] = value -- 写入当前档案；nil 会清除显式值
    self:_notify() -- 每次写入后通知回调，包括重复写入相同值
end

-- 注册回调函数（值改变或profile切换时触发）
function ConfigObj:register_callback(func) -- 注册后续值通知回调
    insert(self.callbacks, func) -- 追加回调，注册时不立即触发
end

-- 内部: 触发所有回调
function ConfigObj:_notify() -- 向全部回调传递当前配置值
    local value = self:get_value() -- 读取本轮所有回调共同接收的配置值
    for callbackIndex = 1, #self.callbacks do -- 按注册顺序执行回调
        local callback = self.callbacks[callbackIndex] -- 按注册顺序取出回调
        callback(value) -- 向订阅方传递本次配置值
    end
end

-- 工厂函数: 获取或创建config对象
local function Config(key) -- 获取或创建指定键的唯一配置对象
    if not config_cache[key] then -- 同一 key 只创建和注册一次
        config_cache[key] = ConfigObj:new(key) -- 缓存该 key 对应的新实例
        Profile._register_config(config_cache[key]) -- 使新实例参与档案切换通知
    end
    return config_cache[key] -- 返回该 key 对应的共享配置对象
end

addonTable.Config = Config -- 向后续文件提供配置对象工厂
addonTable.ConfigRows = {} -- 初始化后续文件共享的配置界面条目表
