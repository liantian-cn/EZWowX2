local addonName, DejaVu_Core = ...

-- Lua 原生函数
local insert = table.insert

-- 确保保存表存在
DejaVu_CoreSave = DejaVu_CoreSave or {}
DejaVu_CoreSave.profiles = DejaVu_CoreSave.profiles or {}
DejaVu_CoreSave.profiles["default"] = DejaVu_CoreSave.profiles["default"] or {}
DejaVu_CoreSave.current_profile = DejaVu_CoreSave.current_profile or "default"

-- 所有config对象的注册表, 用于切换profile时通知
local all_configs = {}

local Profile = {}

-- 获取当前profile名称
function Profile.current_profile()
    return DejaVu_CoreSave.current_profile
end

-- 切换profile（不存在则创建, 所有值恢复默认）
function Profile.switch_profile(name)
    -- 如果profile不存在, 创建一个空表
    if not DejaVu_CoreSave.profiles[name] then
        DejaVu_CoreSave.profiles[name] = {}
    end

    -- 切换当前profile
    DejaVu_CoreSave.current_profile = name

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
    return DejaVu_CoreSave.profiles[DejaVu_CoreSave.current_profile]
end

DejaVu_Core.Profile = Profile
