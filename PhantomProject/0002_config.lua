-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local insert = table.insert
local setmetatable = setmetatable


-- 插件级变量定义/引用

PhantomSettings = PhantomSettings or {}
PhantomSettings.profiles = PhantomSettings.profiles or {}
PhantomSettings.profiles["default"] = PhantomSettings.profiles["default"] or {}
PhantomSettings.current_profile = PhantomSettings.current_profile or "default"

-- 本地变量定义
local all_configs = {}
local Profile = {}

-- 获取当前profile名称
function Profile.current_profile()
    return PhantomSettings.current_profile
end

-- 切换profile（不存在则创建, 所有值恢复默认）
function Profile.switch_profile(name)
    -- 如果profile不存在, 创建一个空表
    if not PhantomSettings.profiles[name] then
        PhantomSettings.profiles[name] = {}
    end

    -- 切换当前profile
    PhantomSettings.current_profile = name

    -- 通知所有config回调
    for configIndex = 1, #all_configs do
        local config = all_configs[configIndex]
        config:_notify()
    end
end

-- 内部函数: 注册config对象
function Profile._register_config(config)
    insert(all_configs, config)
end

-- 获取当前profile的数据表（内部使用）
function Profile._get_current_data()
    return PhantomSettings.profiles[PhantomSettings.current_profile]
end

-- 缓存所有config对象, 相同key返回同一对象
local config_cache = {}

-- Config对象
local ConfigObj = {}
ConfigObj.__index = ConfigObj

-- 创建新的config对象
function ConfigObj:new(key)
    local obj = {
        key = key,
        default_value = nil,
        callbacks = {}
    }
    setmetatable(obj, self)
    return obj
end

-- 设置默认值
function ConfigObj:set_default(value)
    self.default_value = value
end

-- 获取当前值（优先从profile读取, 没有则返回默认值）
function ConfigObj:get_value()
    local data = Profile._get_current_data()
    if data[self.key] ~= nil then
        return data[self.key]
    end
    return self.default_value
end

-- 设置值（写入当前profile, 触发回调）
function ConfigObj:set_value(value)
    local data = Profile._get_current_data()
    data[self.key] = value
    self:_notify()
end

-- 注册回调函数（值改变或profile切换时触发）
function ConfigObj:register_callback(func)
    insert(self.callbacks, func)
end

-- 内部: 触发所有回调
function ConfigObj:_notify()
    local value = self:get_value()
    for callbackIndex = 1, #self.callbacks do
        local callback = self.callbacks[callbackIndex]
        callback(value)
    end
end

-- 工厂函数: 获取或创建config对象
local function Config(key)
    if not config_cache[key] then
        config_cache[key] = ConfigObj:new(key)
        Profile._register_config(config_cache[key])
    end
    return config_cache[key]
end

addonTable.Config = Config
addonTable.ConfigRows = {}
