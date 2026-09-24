# 目标／焦点与黑名单最小配置片段

将所需条件加入已有有效 rotation。这里只声明观察条件，不添加自动匹配或打断规则；无需修改实际战斗循环来试读说明。

```toml
[[conditions]]
title = "目标存在"
plugin = "target_is_exists@dev"

[[conditions]]
title = "目标存活"
plugin = "target_is_alive@dev"

[[conditions]]
title = "玩家可攻击目标"
plugin = "target_can_attack@dev"

[[conditions]]
title = "目标战斗中"
plugin = "target_in_combat@dev"

[[conditions]]
title = "目标施法进度"
plugin = "target_cast_progress@dev"

[[conditions]]
title = "目标当前施法可中断"
plugin = "target_cast_interruptible@dev"

[[conditions]]
title = "目标施法图标"
plugin = "target_cast_icon@dev"

[[conditions]]
title = "目标可驱散魔法增益"
plugin = "target_has_dispellable_buff@dev"
plugin_args = { dispel_types = { Magic = true } }

# 焦点对应插件：将以上 target_ 替换为 focus_，并使用唯一的条件标题。
# 七种驱散键：Magic/Poison/Disease/Curse/Stealth/Special/Enrage。
# Enrage 的实际 dispelName 键游戏待验；不猜映射，空表或全 false 不匹配。

# 每份循环只允许声明一次；共享 interrupt_blacklist，不支持多份独立黑名单。
[[conditions]]
title = "打断黑名单图标"
plugin = "interrupt_blacklist_icons@dev"

[[conditions]]
title = "目标玩家来源减益"
plugin = "target_has_debuff@dev"
plugin_args = { aura_ids = [55078] }

[[conditions]]
title = "焦点玩家来源减益"
plugin = "focus_has_debuff@dev"
plugin_args = { aura_ids = [55078] }

[[conditions]]
title = "目标减益剩余时间估计"
plugin = "aura_target_debuff_duration@dev"
plugin_args = { aura_ids = [55078], duration = 24 }

[[conditions]]
title = "目标减益层数估计"
plugin = "aura_target_debuff_stacks@dev"
plugin_args = { aura_ids = [55078], max_value = 5 }
```

最后四项固定 `PLAYER|HARMFUL`，不接受 `player_only`；官方 PLAYER 包含玩家宠物和载具。ID、时长和层数上限仅用于展示参数结构，请按实际光环配置。时长是显示比例乘配置时长的估计。

施法进度的零值不能区分空闲与刚开始；可中断只是施法状态。敌人可驱散 Buff 表示团队有人能驱散且类型匹配，不保证玩家本人现在可以驱散。黑名单在游戏 panel 中编辑，默认六项按档案回退、已有列表优先；显示前十个数值升序 ID，失败槽不补位。黄色角标只表示类别。
