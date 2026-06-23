local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random                = math.random
local insert                = table.insert
local format                = string.format
-- WoW 官方 API
local CreateFrame           = CreateFrame

local DejaVu_Aura           = _G["DejaVu_Aura"]

-- 插件内引用
local CreateAuraController  = DejaVu_Aura.CreateAuraController

local MAX_AURA_COUNT        = 7
local BASE_Y                = 19
local AURA_FILTER           = "HELPFUL|PLAYER|RAID_IN_COMBAT"
local SORT_RULE             = Enum.UnitAuraSortRule.Default
local SORT_DIRECTION        = Enum.UnitAuraSortDirection.Reverse
local DejaVu                = _G["DejaVu"]
local MartixInitFuncs       = DejaVu.MartixInitFuncs


local function InitFrame()
    for partyIndex = 1, 4 do
        local eventFrame = CreateFrame("Frame")
        local UNIT_KEY = format("party%d", partyIndex)
        local BASE_X = 21 * partyIndex - 20
        local controller = CreateAuraController({
            unitKey = UNIT_KEY,
            auraFilter = AURA_FILTER,
            maxAuraCount = MAX_AURA_COUNT,
            baseX = BASE_X,
            baseY = BASE_Y,
            sortRule = SORT_RULE,
            sortDirection = SORT_DIRECTION,
            colorMode = "Helpful",
        })

        -- 说明：全量刷新当前 party 单位的增益显示。
        -- 依赖事件更新：UNIT_AURA、UNIT_FLAGS、GROUP_ROSTER_UPDATE、GROUP_JOINED、GROUP_LEFT、GROUP_FORMED。
        -- 依赖定时刷新：无。
        local function refreshAll()
            controller.refreshAll()
        end

        -- 说明：更新当前 party 单位所有增益的剩余时间文本。
        -- 依赖事件更新：无。
        -- 依赖定时刷新：0.1 秒。
        local function updateRemainingAll()
            controller.updateRemainingAll()
        end

        local GroupChangeOnFrame = false

        -- UNIT_AURA
        -- 事件说明：当前 party 单位的 Aura 列表变化时，按当前 API 限制刷新增益显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterUnitEvent("UNIT_AURA", UNIT_KEY)
        function eventFrame:UNIT_AURA(unitToken, info)
            -- 因为无法判断 isHarmful 还是 isHelpful，所以只能全量刷新。这个问题在 12.0.5 修正。等那时补回来。
            if info.isFullUpdate then
                refreshAll()
                return
            end
            if info.removedAuraInstanceIDs then
                -- for _, instanceID in ipairs(info.removedAuraInstanceIDs) do
                --     controller.removeAura(instanceID)
                -- end
                refreshAll() -- 临时代替，等 12.0.5 修正 API 后再改回。
                return       -- 因为完全刷新了，所以 return 就行了。
            end
            if info.addedAuras then
                -- for _, aura in ipairs(info.addedAuras) do
                --     controller.addAura(aura.auraInstanceID)
                -- end
                refreshAll() -- 临时代替，等 12.0.5 修正 API 后再改回。
                return       -- 因为完全刷新了，所以 return 就行了。
            end
            if info.updatedAuraInstanceIDs then
                -- for _, instanceID in ipairs(info.updatedAuraInstanceIDs) do
                --     controller.updateRemaining(instanceID)
                -- end
                -- 暂时什么都不用做，等 12.0.5 修正 API 后再改回来。
                return -- 因为完全刷新了，所以 return 就行了。
            end
        end

        -- UNIT_FLAGS
        -- 事件说明：当前 party 单位的标记状态变化时刷新增益显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_KEY)
        function eventFrame:UNIT_FLAGS(unitToken)
            refreshAll()
        end

        -- GROUP_ROSTER_UPDATE
        -- 事件说明：队伍名单变化时刷新当前 party 单位的 Aura 显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
        function eventFrame:GROUP_ROSTER_UPDATE()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            refreshAll()
        end

        -- GROUP_JOINED
        -- 事件说明：加入队伍时刷新当前 party 单位的 Aura 显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterEvent("GROUP_JOINED")
        function eventFrame:GROUP_JOINED()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            refreshAll()
        end

        -- GROUP_LEFT
        -- 事件说明：离开队伍时刷新当前 party 单位的 Aura 显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterEvent("GROUP_LEFT")
        function eventFrame:GROUP_LEFT()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            refreshAll()
        end

        -- GROUP_FORMED
        -- 事件说明：新队伍形成时刷新当前 party 单位的 Aura 显示。
        -- 对应函数：refreshAll
        eventFrame:RegisterEvent("GROUP_FORMED")
        function eventFrame:GROUP_FORMED()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            refreshAll()
        end

        local fastTimeElapsed = -random() -- 随机初始时间，避免所有事件在同一帧更新。
        -- local lowTimeElapsed = -random()      -- 当前未使用，保留 0.5 秒刷新档位结构。
        -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构。
        eventFrame:HookScript("OnUpdate", function(frame, elapsed)
            GroupChangeOnFrame = false -- 每帧重置，避免同一帧内重复处理多个队伍结构事件。
            fastTimeElapsed = fastTimeElapsed + elapsed
            if fastTimeElapsed > 0.1 then
                fastTimeElapsed = fastTimeElapsed - 0.1
                updateRemainingAll()
            end
            -- lowTimeElapsed = lowTimeElapsed + elapsed
            -- if lowTimeElapsed > 0.5 then
            --     lowTimeElapsed = lowTimeElapsed - 0.5
            -- end
            -- superLowTimeElapsed = superLowTimeElapsed + elapsed
            -- if superLowTimeElapsed > 2 then
            --     superLowTimeElapsed = superLowTimeElapsed - 2
            --     refreshAll()
            -- end
        end)

        eventFrame:SetScript("OnEvent", function(self, event, ...)
            self[event](self, ...)
        end)

        refreshAll()
    end
end
insert(MartixInitFuncs, InitFrame)
