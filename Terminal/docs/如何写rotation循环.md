# 如何写 rotation 循环

这套工程里的“循环”，不是自己写 `while True`。

真正会被反复调用的是 `main_rotation(ctx)`。外部线程每来一帧数据，就会新建一次 rotation 对象，调用一次 `handle(decoded_data)`，最后转到你的 `main_rotation(ctx)`，让你只决定“这一拍做什么”。

所以写 rotation 时，核心原则只有一句话：

按优先级从上往下判断，命中后立刻 `return`。

## 先看最小骨架

```python
from __future__ import annotations

from terminal.context import Context
from .base import BaseRotation


class DemoRotation(BaseRotation):
    name = "示例专精"
    desc = "示例循环"

    def __init__(self) -> None:
        super().__init__()
        self.macroTable = {
            "target技能A": "ALT-NUMPAD1",
            "player技能B": "ALT-NUMPAD2",
        }

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:
        player = ctx.player
        target = ctx.target
        spell_queue_window = float(ctx.spell_queue_window or 0.2)

        if not ctx.enable:
            return self.idle("总开关未开启")

        if ctx.delay:
            return self.idle("延迟开关开启")

        if not player.alive:
            return self.idle("玩家已死亡")

        if not player.isInCombat:
            return self.idle("未进入战斗")

        if not (target.exists and target.canAttack):
            return self.idle("没有可攻击目标")

        if ctx.spell_cooldown_ready("技能A", spell_queue_window):
            return self.cast("target技能A")

        if ctx.spell_cooldown_ready("技能B", spell_queue_window):
            return self.cast("player技能B")

        return self.idle("当前没有合适动作")
```

## 返回值是什么意思

`BaseRotation` 里已经给你准备好了三个返回方式：

- `self.cast("宏名")`
  表示这一拍要按哪个宏。这里传的是 `macroTable` 里的名字，不是按键本身。
- `self.idle("原因")`
  表示这一拍什么都不做。
- `self.wait(秒数, "原因")`
  表示暂时等一下，再继续后面的轮转。

平时最常用的是 `cast` 和 `idle`。

## 推荐照着写的顺序

参考 `terminal/rotation/DeathKnightBlood.py` 和 `terminal/rotation/DruidGuardian.py`，基本都可以整理成下面 6 步。

## 1. 先放固定参数，或者先读设置

这一步就是把后面会反复用到的数值先准备好。

有两种常见写法：

- 像 `DruidGuardian` 那样，直接在 `main_rotation()` 开头写常量。
  适合短期内不准备让 UI 调整的阈值。
- 像 `DeathKnightBlood` 那样，从 `ctx.setting.cell(...)`、`ctx.spec.cell(...)` 里读配置。
  适合已经接到矩阵设置里的参数。

简单说：

- 固定写死，用常量。
- 想在外面调，用 `ctx.setting` / `ctx.spec` 读取。

## 2. 先写“挡板”

挡板就是“当前根本不能出手”的情况，要尽早返回，不要拖到后面。

两个示例里都先检查了这些东西：

- 总开关是否开启
- 延迟开关是否开启
- 玩家是否活着
- 是否正在聊天输入
- 是否在骑乘
- 是否正在施法 / 引导 / 蓄力
- 是否在吃喝
- 是否已经进战斗

熊德还多了一层形态判断：

- 在旅行形态就先 `idle`
- 不是熊形态就先 `cast("any熊形态")`

这一步建议尽量放在最前面，因为它能把后面的判断量一下子砍掉很多。

## 3. 先确定主目标

不要后面每一段都重复写一长串“目标存在、可攻击、在范围内”的判断。

更稳的写法是，先统一整理出一个 `main_target`，后面都围绕它写。

这两个示例的区别是：

- `DeathKnightBlood` 更偏近战，只把近战可打的 `focus` 或 `target` 选成主目标
- `DruidGuardian` 更宽一点，近战和远程范围都可以先接住

如果最后连主目标都没有，就直接 `return self.idle(...)`。

## 4. 把这一拍会用到的状态先算好

常见做法：

- `player = ctx.player`
- `target = ctx.target`
- `focus = ctx.focus`
- `mouseover = ctx.mouseover`
- `spell_queue_window = float(ctx.spell_queue_window or 0.2)`
- 当前资源值，比如怒气、符能、符文
- 当前环境标签，比如是不是开怪期、是不是 AOE、敌人数够不够

这样做的好处是：

- 后面判断更短，更容易看
- 同一个值不会到处重复算
- 出问题时更容易打印日志排查

## 5. 按“最重要的先写”排优先级

这就是 rotation 的正文了。推荐顺序可以直接参考这两个例子：

1. 生存
2. 打断
3. 关键 buff / 形态维持
4. 开怪爆发
5. 主输出技能
6. 资源溢出处理
7. 填充技能
8. 最后 `idle`

最重要的一条：

每个 `if` 分支只处理一件事，一旦命中就立刻 `return`。

不要写成“这一拍想按 3 个技能”。这一套框架一次只会执行你返回的那一个动作。

## 6. 最后一定留一个兜底

两个示例最后都有：

```python
return self.idle("当前没有合适动作")
```

这个兜底很重要，因为它能明确告诉外层：

- 不是程序坏了
- 只是这一拍没有需要按的技能

## 两个示例分别适合学什么

## `DeathKnightBlood.py` 适合参考的点

- 怎么从 `ctx.setting.cell()`、`ctx.spec.cell()` 读取外部配置
- 怎么先做主目标筛选，再区分 `target` / `focus`
- 怎么先写保命，再写打断，再写资源和填充
- 怎么根据资源值、buff 剩余时间、敌人血量做更细的判断

如果你要写的是“可调参数比较多”的循环，先看这个更合适。

## `DruidGuardian.py` 适合参考的点

- 怎么把常量统一放在函数开头
- 怎么把开怪期、AOE、站立不动这些状态先算成布尔值
- 怎么把循环拆成一段一段短判断，让阅读顺序很直
- 怎么把“形态不对先变形”这种前置动作插在挡板后面

如果你要写的是“先跑通，再慢慢细化”的循环，先照这个骨架会更省事。

## 最容易写错的几个地方

- 不要自己写死循环。
  外面已经在反复调用了，你这里只需要决定当前动作。
- 不要一个分支里连续返回多个动作。
  一次只能返回一个。
- 不要把目标判断到处复制。
  先整理出 `main_target`，后面会轻很多。
- 不要把“不能出手”的判断放得太靠后。
  这会让正文越来越乱。
- 不要漏掉最后的 `idle(...)`。
  否则调试时不容易分清是“没动作”还是“代码走漏了”。

## 实际动手时的推荐模板

写新循环时，最省事的办法不是从零写，而是直接按下面顺序改：

1. 复制一个最接近你的现成 rotation 文件
2. 先改 `name`、`desc`、`macroTable`
3. 保留挡板结构不动
4. 保留主目标选择结构，只改范围条件
5. 先写 3 到 5 个最核心技能
6. 跑通以后，再补开怪、打断、AOE、资源溢出这些细节

如果不知道某一段该放哪，优先记这个顺序：

先判断“能不能打”，再判断“打谁”，最后判断“现在最该按什么”。
