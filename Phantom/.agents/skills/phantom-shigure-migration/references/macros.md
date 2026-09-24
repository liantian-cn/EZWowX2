# 迁移宏映射

宏动作以用户文本和源动作定义为准；判断 ID 与宏动作可以不同，迁移不自行纠正。普通动作写为 `/cast 技能名称`；源明确 `Unit=31/32/33` 时分别写 `/cast [@player] 技能名称`、`/cast [@target] 技能名称`、`/cast [@focus] 技能名称`。未写 `Unit` 不补单位。

## 用户确认的特殊宏

下列宏是用户提供的可复用映射，保持行序与物品优先级。裸 `item:数字` 不是完整宏命令，归一化为 `/cast item:数字`；不要改成 Lua、自动生成 `/use` 或只保留第一件物品。

### 光注法力药水

```text
/cast item:241300
/cast item:241301
```

### 鲁莽药水

```text
/cast item:241288
/cast item:241289
```

### 圣光潜力

```text
/cast item:241308
/cast item:241309
```

### 银月城生命药水

```text
/cast item:241304
/cast item:241305
/cast item:271884
/cast item:271885
```

### 浓缩银月城生命药水

```text
/cast item:271884
/cast item:271885
/cast item:241304
/cast item:241305
```

### 圣言祭礼

```text
/cast 圣言祭礼
/use 16
```

## 检测范围与宏范围

多行宏不意味着每个物品都要新增检测。此次圣光潜力的源条件只检测 `241308`，保留该范围，不扩为 `241308 or 241309`；宏仍保留两行。本次唯一新增条件为 `item_cooldown_ready@dev(item_id)`，要求背包数量大于 0、冷却返回有效且 `enabled`、冷却就绪；不附加 usable 判定、不计银行。其余物品条件遇到差异须重新核对授权。

全部宏仍按 Phantom 声明顺序自动分配键位，包括未引用宏；只有 `Idle` 使用保留动作，不声明同名宏。完整宏格式和键位池见[配置规范](../../phantom-rotation-dev/references/configuration.md#宏与键位)。
