# PixelDumperX2 重构指南

> 本文档面向希望基于本项目重构自己实现的开发者，重点关注**业务逻辑**而非具体代码实现。

---

## 一、核心概念

### 1.1 什么是"像素桥接"

这是绕过游戏 API 限制的一种技术方案：

```
┌─────────────────────────────────────────────────────────────────────────┐
│  游戏内 (WoW)                                                            │
│  ┌──────────────┐    编码    ┌─────────────┐                            │
│  │ 游戏状态数据  │ ────────→ │ 彩色像素块   │ ← 显示在屏幕角落            │
│  │ (秘密值)      │           │ (8x8像素)    │   (几乎不可见)              │
│  └──────────────┘           └─────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓ 屏幕捕获
┌─────────────────────────────────────────────────────────────────────────┐
│  PixelDumper (本程序)                                                   │
│  ┌──────────────┐    解码    ┌─────────────┐    输出    ┌─────────────┐  │
│  │ 屏幕截图      │ ────────→ │ 像素解析     │ ────────→ │ JSON API    │  │
│  │ (DXCam)      │           │ (Node提取)   │           │ (端口65131) │  │
│  └──────────────┘           └─────────────┘           └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓ HTTP GET
┌─────────────────────────────────────────────────────────────────────────┐
│  Rotation 程序 (消费端)                                                   │
│  ┌──────────────┐    决策    ┌─────────────┐                            │
│  │ 读取JSON      │ ────────→ │ 技能决策     │                            │
│  │              │           │ 按键模拟     │                            │
│  └──────────────┘           └─────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 关键设计约束

| 约束项 | 说明 | 影响 |
|--------|------|------|
| **像素尺寸** | 每个数据单元 = 8×8 像素 | 所有坐标计算基于8的倍数 |
| **颜色编码** | RGB 值承载状态信息 | 需要 ColorMap 映射表 |
| **亮度编码** | 0-255 亮度值承载数值 | 需要 remaining_curve 解码 |
| **锚点定位** | 2个模板标记确定数据区域 | 需要模板匹配算法 |
| **哈希识别** | 图标通过哈希值识别 | 需要图标数据库 |

---

## 二、数据布局详解

### 2.1 像素网格坐标系

整个数据区域是一个二维网格，每个单元格 = 8×8 像素。

```
        X坐标 (0开始，每个格子8像素)
        0    1    2    ...   34   35   36   ...  45
      ┌────┬────┬────┬────┬────┬────┬────┬────┬────┐
   0  │    │    │    │    │    │    │    │    │    │  ← Y=0: 技能序列区域
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   1  │    │    │    │    │    │    │    │    │    │
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   2  │    │    │████│████│████│... │████│    │    │  ← Y=2: 玩家技能 (36个)
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   3  │    │    │    │    │    │    │    │    │    │
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   4  │    │    │████│████│████│... │████│████│████│  ← Y=4: 玩家BUFF (32个)
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   5  │    │    │    │    │    │    │    │████│████│  ← (38,5)=职业, (39,5)=职责
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
   6  │    │    │████│████│████│... │████│    │    │  ← Y=6: 玩家DEBUFF (8个)
      ├────┼────┼────┼────┼────┼────┼────┼────┼────┤
      │    │    │    │    │    │    │    │    │    │
      │    │    │    │    │    │    │    │    │    │
  14  │████│████│████│████│████│████│████│████│████│  ← Y=14: 小队成员状态
      └────┴────┴────┴────┴────┴────┴────┴────┴────┘
```

### 2.2 节点类型定义

一个 8×8 的节点内部有不同功能区域：

```
  0   1   2   3   4   5   6   7
┌───┬───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │   │  ← 边界（无用）
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │  ← █ = middle 区域 (6×6)
├───┼───┼───┼───┼───┼───┼───┼───┤      用于：图标哈希计算、标题识别
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │  ← ░ = inner 区域 (4×4)
├───┼───┼───┼───┼───┼───┼───┼───┤      用于：亮度/颜色计算、数值解码
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │ □ │ □ │  ← □ = footnote 区域 (2×2)
└───┴───┴───┴───┴───┴───┴───┴───┘       用于：图标类型标识
```

**各区域用途：**

| 区域 | 尺寸 | 用途 |
|------|------|------|
| `full` | 8×8 | 完整像素数据，存储到数据库 |
| `middle` | 6×6 | 图标主体，计算 xxhash 用于识别 |
| `inner` | 4×4 | 中心区域，计算平均亮度/颜色 |
| `footnote` | 2×2 | 右下角，标识图标类型(BUFF/DEBUFF等) |

### 2.3 数据区域布局

#### 玩家状态区域 (Player)

```
坐标系统：X 从 0 开始，每个单位 = 8 像素

┌─────────────────────────────────────────────────────────────────┐
│ 技能序列 (36个技能图标)                                          │
│ X=2..37, Y=2 (每个技能占1个节点)                                 │
│                                                                 │
│ 技能1  技能2  技能3  ...  技能35  技能36                         │
│ (2,2)  (3,2)  (4,2)       (36,2) (37,2)                         │
├─────────────────────────────────────────────────────────────────┤
│ 玩家 BUFF (32个图标)                                             │
│ X=2..33, Y=4                                                    │
│                                                                 │
│ Buff1  Buff2  Buff3  ...  Buff31  Buff32                         │
│ (2,4)  (3,4)  (4,4)       (33,4) (34,4)                         │
├─────────────────────────────────────────────────────────────────┤
│ 玩家 DEBUFF (8个图标)                                            │
│ X=2..9, Y=6                                                     │
│                                                                 │
│ Debuff1  Debuff2  ...  Debuff8                                  │
│ (2,6)    (3,6)         (9,6)                                    │
├─────────────────────────────────────────────────────────────────┤
│ 状态标识区域 (X=38..45, Y=4..5)                                  │
│                                                                 │
│   X=38    X=39    X=40    X=41    X=42    X=43    X=44    X=45   │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐              │
│ │伤害吸│移动中│载具中│蓄力中│施法图│施法进│职业  │血量% │ Y=4    │
│ │收盾  │     │     │     │标    │度    │      │      │        │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤              │
│ │治疗吸│战斗  │死亡  │引导图│引导进│能量% │职责  │护甲  │ Y=5    │
│ │收盾  │中    │状态  │标    │度    │      │      │类型  │        │
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘              │
│                                                                 │
│ 说明：                                                          │
│ - 白色节点 = True/有值，黑色节点 = False/无值                    │
│ - 施法/引导图标节点为纯色时表示无施法                            │
│ - 血量和能量使用亮度百分比 (0-100%)                              │
└─────────────────────────────────────────────────────────────────┘
```

#### 目标状态区域 (Target)

```
X=38..45, Y=6..8 区域

┌─────────────────────────────────────────────────────┐
│ 目标 DEBUFF (16个图标)                               │
│ X=10..25, Y=8                                       │
├─────────────────────────────────────────────────────┤
│ 状态标识区域                                         │
│                                                     │
│   X=38    X=39    X=40    X=41    X=42    X=43      │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐  │
│ │目标存│可攻击│是自己│存活  │战斗中│距离内│施法图│施法进│ Y=6    │
│ │在    │     │     │     │     │     │标    │度    │        │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤  │
│ │施法打│可断法│引导图│引导进│可断引│     │     │血量% │ Y=7    │
│ │断性  │     │标    │度    │导    │     │     │      │        │
└─────────────────────────────────────────────────────┘
```

#### Focus 状态区域

```
与目标类似，使用 Y=8..9 区域
X=38..45, Y=8..9
```

#### 小队成员区域 (Party)

```
每个队友占用一个垂直区域，共4个队友

队友1 (party1): X=10..11, Y=11..15
队友2 (party2): X=22..23, Y=11..15  
队友3 (party3): X=34..35, Y=11..15
队友4 (party4): X=46..47, Y=11..15

每个队友区域包含：
┌─────────────────────────────────────┐
│ BUFF序列 (6个)   │ DEBUFF序列 (6个)  │ Y=11
│ X=N-4..N-1      │ X=N-10..N-5       │
├─────────────────────────────────────┤
│ 存在标识│距离内│血量%│选中标识      │ Y=14
│ 职业    │职责  │伤害吸收│治疗吸收    │ Y=15
└─────────────────────────────────────┘
(N = 12*i, i=1..4)
```

---

## 三、核心算法

### 3.1 屏幕捕获流程

```
1. 截图 (DXCam/OpenCV/其他)
   ↓
2. 模板匹配查找两个锚点 (mark8.png)
   ↓
3. 计算数据区域边界 (left, top, right, bottom)
   ↓
4. 裁剪出数据区域图像
   ↓
5. 按 8x8 切分为 Node 网格
   ↓
6. 逐个解析 Node
```

**边界计算规则：**

```python
# 两个锚点位置 (x1, y1), (x2, y2)
# 模板尺寸: template_w, template_h

left   = x1 + template_w          # 第一个锚点右侧
top    = y1                       # 第一个锚点顶部
right  = x2                       # 第二个锚点左侧
bottom = y2 + template_h          # 第二个锚点底部

# 边界必须是8的倍数
def round_to_8(n):
    return (n // 8) * 8

left   = round_to_8(left + 7)     # 向上取整到8的倍数
top    = round_to_8(top)
right  = round_to_8(right)
bottom = round_to_8(bottom)
```

### 3.2 Node 解析流程

```
输入: 8x8 RGB 像素数组
   ↓
1. 提取 middle 区域 (6x6) → 计算 xxhash
   ↓
2. 查询数据库
   ├─ Hash 直接匹配 → 返回 title
   ├─ 余弦相似度匹配 (≥0.99) → 记录并返回 title
   └─ 未匹配 → 记录到未匹配列表，返回 hash
   ↓
3. 提取 inner 区域 (4x4)
   ├─ 计算平均亮度 (0-255)
   ├─ 计算亮度百分比 (0-100%)
   └─ 如果是纯色 → 解析颜色值
   ↓
4. 提取 footnote 区域 (2x2)
   └─ 如果纯色 → 映射为图标类型 (BUFF/DEBUFF等)
   ↓
输出: Node 对象 {title, hash, percent, color, footnote_title, ...}
```

### 3.3 亮度值解码 (Remaining Curve)

游戏内将时间/数值编码为亮度，需要反向解码：

```
亮度值 → 时间(秒) 映射表：

亮度    时间
────    ────
0       0.0 秒
100     5.0 秒
150     30.0 秒
200     155.0 秒
255     375.0 秒

解码方法：线性插值
```

```python
def decode_remaining(brightness: int) -> float:
    points = [(0.0, 0), (5.0, 100), (30.0, 150), (155.0, 200), (375.0, 255)]
    
    # 边界处理
    if brightness <= 0:
        return 0.0
    if brightness >= 255:
        return 375.0
    
    # 找到所在区间并线性插值
    for i in range(len(points) - 1):
        time1, bright1 = points[i]
        time2, bright2 = points[i + 1]
        if bright1 <= brightness <= bright2:
            ratio = (brightness - bright1) / (bright2 - bright1)
            return time1 + (time2 - time1) * ratio
    
    return 0.0
```

### 3.4 图标识别算法

#### 数据库结构

```sql
-- node_titles.db
CREATE TABLE node_titles (
    id INTEGER PRIMARY KEY,
    full_data BLOB,        -- base64编码的 8x8x3 字节
    middle_hash TEXT,      -- middle区域 xxhash
    title TEXT,            -- 图标标题
    match_type TEXT,       -- 'manual' | 'cosine'
    created_at TIMESTAMP,
    footnote_title TEXT    -- 图标类型
);
```

#### 匹配流程

```
输入: middle_hash, middle_array(6x6x3)
   ↓
1. Hash 直接查找
   ├─ 命中 → 返回 title
   └─ 未命中 → 继续
   ↓
2. 余弦相似度匹配 (遍历数据库)
   ├─ similarity >= 0.99 → 自动添加到数据库，返回 title
   ├─ similarity >= 0.90 → 记录相似度匹配日志
   └─ 全部 < 0.90 → 标记为未匹配
   ↓
3. 返回结果 (title 或 hash)
```

**余弦相似度计算：**

```python
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个6x6x3数组的相似度，范围 [-1, 1]"""
    a_flat = a.flatten().astype(float)
    b_flat = b.flatten().astype(float)
    
    norm_a = np.linalg.norm(a_flat)
    norm_b = np.linalg.norm(b_flat)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return np.dot(a_flat, b_flat) / (norm_a * norm_b)
```

---

## 四、ColorMap 映射表

### 4.1 图标类型 (IconType)

右下 2×2 像素颜色 → 图标类型

| RGB 值 | 类型标识 | 说明 |
|--------|----------|------|
| 60,100,220 | MAGIC | 魔法效果 |
| 100,0,120 | CURSE | 诅咒效果 |
| 160,120,60 | DISEASE | 疾病效果 |
| 154,205,50 | POISON | 中毒效果 |
| 230,120,20 | ENRAGE | 激怒效果 |
| 80,0,20 | BLEED | 流血效果 |
| 255,60,60 | PLAYER_DEBUFF | 玩家受到的减益 |
| 80,220,120 | PLAYER_BUFF | 玩家获得的增益 |
| 64,158,210 | PLAYER_SPELL | 玩家技能 |
| 255,255,60 | ENEMY_SPELL_INTERRUPTIBLE | 敌人可打断技能 |
| 200,0,0 | ENEMY_SPELL_NOT_INTERRUPTIBLE | 敌人不可打断技能 |
| 105,105,210 | ENEMY_DEBUFF | 敌人身上的减益 |
| 0,0,0 | NONE | 无类型 |

### 4.2 职业 (Class)

纯色节点颜色 → 职业

| RGB 值 | 职业 |
|--------|------|
| 199,86,36 | WARRIOR (战士) |
| 245,140,186 | PALADIN (圣骑士) |
| 163,203,66 | HUNTER (猎人) |
| 255,245,105 | ROGUE (潜行者) |
| 196,207,207 | PRIEST (牧师) |
| 125,125,215 | DEATHKNIGHT (死亡骑士) |
| 64,148,255 | SHAMAN (萨满) |
| 64,158,210 | MAGE (法师) |
| 105,105,210 | WARLOCK (术士) |
| 0,255,150 | MONK (武僧) |
| 255,125,10 | DRUID (德鲁伊) |
| 163,48,201 | DEMONHUNTER (恶魔猎手) |
| 108,191,246 | EVOKER (唤魔师) |
| 0,0,0 | NONE |

### 4.3 职责 (Role)

| RGB 值 | 职责 |
|--------|------|
| 180,80,20 | TANK (坦克) |
| 230,200,50 | DPS (输出) |
| 120,200,255 | HEALER (治疗) |
| 0,0,0 | NONE |

---

## 五、数据提取流程

### 5.1 数据提取主流程

```
输入: NodeExtractor (包含所有节点的访问器)
   ↓
1. 提取 MISC 数据
   ├─ (34,5): 护甲类型
   ├─ (35,5): 是否在聊天
   └─ (36,5): 是否正在选目标
   ↓
2. 提取玩家状态 (Player)
   ├─ 技能序列: read_spell_sequence(X=2, Y=2, length=36)
   ├─ BUFF序列: read_aura_sequence(X=2, Y=4, length=32)
   ├─ DEBUFF序列: read_aura_sequence(X=2, Y=6, length=8)
   └─ 状态节点: (38..45, 4..5)
   ↓
3. 提取目标状态 (Target)
   ├─ 存在检查: (38,6).is_white
   ├─ DEBUFF序列: read_aura_sequence(X=10, Y=8, length=16)
   └─ 状态节点: (38..45, 6..7)
   ↓
4. 提取 Focus 状态
   └─ 与目标类似，使用 Y=8..9
   ↓
5. 提取小队状态 (Party1-4)
   └─ 循环4次，每次使用不同X偏移
   ↓
6. 提取信号区域 (Signal)
   └─ (38..45, 10)
   ↓
7. 提取专精区域 (Spec)
   └─ (34..37, 8..10)
   ↓
输出: 完整的 JSON 数据结构
```

### 5.2 特殊读取函数

#### read_health_bar - 读取进度条

```python
# 用于：吸收盾、血量条等
# 原理：从左到右读取白色像素节点，计算比例

def read_health_bar(left: int, top: int, length: int) -> float:
    """
    读取白色进度条
    
    Args:
        left: 起始X坐标
        top: Y坐标
        length: 进度条最大长度(节点数)
    
    Returns:
        float: 0.0 ~ 1.0 的进度比例
    """
    white_count = 0
    for i in range(length):
        node = self.node(left + i, top)
        if node.is_white:
            white_count += 1
        else:
            break
    return white_count / length
```

#### read_aura_sequence - 读取光环序列

```python
def read_aura_sequence(left: int, top: int, length: int) -> tuple[list, dict]:
    """
    读取BUFF/DEBUFF序列
    
    Args:
        left: 起始X坐标
        top: Y坐标
        length: 最大图标数量
    
    Returns:
        (sequence_list, aura_dict)
        - sequence_list: 按顺序的图标标题列表
        - aura_dict: {标题: 剩余时间(秒)}
    """
    sequence = []
    auras = {}
    
    for i in range(length):
        icon_node = self.node(left + i, top)
        time_node = self.node(left + i, top + 1)
        
        # 跳过纯黑节点(空位)
        if icon_node.is_black:
            continue
        
        title = icon_node.title
        remaining = time_node.remaining  # 从亮度解码
        
        sequence.append(title)
        auras[title] = remaining
    
    return sequence, auras
```

#### read_spell_sequence - 读取技能序列

```python
def read_spell_sequence(left: int, top: int, length: int) -> tuple[list, dict]:
    """
    读取技能序列(包含冷却和充能信息)
    
    每个技能占用2个节点：
    - (X, Y): 技能图标
    - (X, Y+1): 冷却/充能信息
    
    Returns:
        (sequence_list, spell_dict)
        - spell_dict: {标题: {cooldown, charges, max_charges}}
    """
    sequence = []
    spells = {}
    
    for i in range(length):
        icon_node = self.node(left + i, top)
        info_node = self.node(left + i, top + 1)
        
        if icon_node.is_black:
            continue
        
        title = icon_node.title
        
        # 解析 info_node
        # - 纯色黑色: 可用，无CD
        # - 纯色白色: 可用，有充能
        # - 非纯色: 冷却中，亮度 = 剩余CD时间
        
        spell_info = {
            'cooldown': info_node.remaining if info_node.is_not_pure else 0,
            'charges': info_node.white_count if info_node.is_pure else 0,
            'max_charges': 0  # 需要额外逻辑判断
        }
        
        sequence.append(title)
        spells[title] = spell_info
    
    return sequence, spells
```

---

## 六、输出 JSON 结构

```json
{
  "timestamp": "2024-01-01 12:00:00",
  "misc": {
    "ac": "护甲类型",
    "on_chat": true,
    "is_targeting": false
  },
  "player": {
    "unitToken": "player",
    "aura": {
      "buff_sequence": ["BUFF名称1", "BUFF名称2"],
      "buff": {
        "BUFF名称1": 25.5,
        "BUFF名称2": 120.0
      },
      "debuff_sequence": [],
      "debuff": {}
    },
    "spell_sequence": ["技能1", "技能2"],
    "spell": {
      "技能1": {
        "cooldown": 0,
        "charges": 2,
        "max_charges": 3
      }
    },
    "status": {
      "unit_health": 85.5,
      "unit_power": 60.0,
      "unit_in_combat": true,
      "unit_class": "ROGUE",
      "unit_role": "DAMAGER",
      "unit_damage_absorbs": 15.0,
      "unit_cast_icon": "正在施法的技能",
      "unit_cast_duration": 45.0
    }
  },
  "target": {
    "unitToken": "target",
    "status": {
      "exists": true,
      "unit_health": 70.0,
      "unit_can_attack": true
    },
    "aura": {
      "debuff_sequence": [],
      "debuff": {}
    }
  },
  "focus": {
    "unitToken": "focus",
    "status": {
      "exists": false
    },
    "aura": {}
  },
  "party": {
    "party1": {
      "exists": true,
      "unitToken": "party1",
      "status": {
        "unit_health": 90.0,
        "unit_class": "PRIEST",
        "unit_role": "HEALER",
        "unit_in_range": true
      },
      "aura": {
        "buff_sequence": [],
        "debuff_sequence": []
      }
    }
  },
  "signal": {
    "1": {"is_pure": true, "color_string": "255,0,0"},
    "2": {"is_pure": false, "title": "某个图标"}
  },
  "spec": {}
}
```

---

## 七、重构任务清单

### 阶段一：基础框架

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] 屏幕捕获模块 | 使用系统API捕获屏幕，支持选择显示器和FPS | `Worker.py` 的 CameraWorker |
| [ ] 模板匹配定位 | 在截图中查找两个 mark8.png 锚点 | `Utils.py` 的 find_template_bounds |
| [ ] 数据区域裁剪 | 根据锚点计算并裁剪像素数据区域 | `Utils.py` 的 find_template_bounds |
| [ ] Node 网格切分 | 将数据区域按 8×8 切分为网格 | `Node.py` 的 NodeExtractor |

### 阶段二：Node 解析

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] PixelBlock 基础 | 8×8 像素块的基础计算(哈希/亮度/颜色) | `Node.py` 的 PixelBlock |
| [ ] Node 区域划分 | 实现 full/middle/inner/footnote 区域提取 | `Node.py` 的 Node |
| [ ] 亮度解码 | 实现 remaining_curve 解码算法 | `Node.py` 的 PixelBlock.remaining |
| [ ] ColorMap 加载 | 加载颜色映射配置 | `Utils.py` 的 _load_colormap |

### 阶段三：图标识别系统

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] 数据库初始化 | 创建 SQLite 表结构 | `Database.py` 的 _init_database |
| [ ] Hash 计算 | 使用 xxhash 计算 middle 区域哈希 | `Node.py` 的 PixelBlock.hash |
| [ ] Hash 匹配 | 优先使用 Hash 直接匹配 | `Database.py` 的 get_title |
| [ ] 余弦相似度 | 实现相似度计算和模糊匹配 | `Database.py` 的 cosine_similarity |
| [ ] 未匹配处理 | 记录未匹配节点供后续添加 | `Database.py` 的 unmatched handling |

### 阶段四：数据提取

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] NodeExtractor | 实现节点坐标访问器 | `Node.py` 的 NodeExtractor |
| [ ] 进度条读取 | 实现 read_health_bar | `Node.py` 的 read_health_bar |
| [ ] 光环读取 | 实现 read_aura_sequence | `Node.py` 的 read_aura_sequence |
| [ ] 技能读取 | 实现 read_spell_sequence | `Node.py` 的 read_spell_sequence |
| [ ] 完整数据提取 | 按布局提取所有游戏状态 | `NodeExtractorData.py` 的 extract_all_data |

### 阶段五：HTTP 服务

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] Web 服务器 | 启动 HTTP 服务，监听 0.0.0.0:65131 | `Worker.py` 的 WebServerWorker |
| [ ] JSON 接口 | 所有路径返回 pixel_dump JSON | `Worker.py` 的 catch_all |
| [ ] CORS 支持 | 添加跨域响应头 | `Worker.py` 的 CORS headers |
| [ ] 数据刷新 | 持续捕获并更新 pixel_dump | `MainWindow.py` 的数据流 |

### 阶段六：GUI (可选)

| 任务 | 业务描述 | 对应原文件 |
|------|----------|------------|
| [ ] 主窗口 | 创建主窗口，显示器/FPS选择 | `MainWindow.py` |
| [ ] 日志显示 | 实时显示捕获日志 | `MainWindow.py` 的 LogEmitter |
| [ ] 相机控制 | 启动/停止相机按钮 | `MainWindow.py` |
| [ ] 图标库管理 | 管理图标标题数据库 | `IconLibraryDialog.py` |
| [ ] 单实例锁 | 防止程序多开 | `DumperGUI.py` 的 mutex |

### 阶段七：优化改进

| 任务 | 业务描述 |
|------|----------|
| [ ] 遮挡检测 | 检测游戏窗口是否被遮挡 |
| [ ] 性能优化 | 降低 CPU 占用，提高捕获帧率 |
| [ ] 容错处理 | 游戏窗口移动/关闭时的处理 |
| [ ] 配置持久化 | 保存用户设置(显示器选择、FPS等) |

---

## 八、技术选型建议

### 屏幕捕获

| 语言 | 推荐方案 | 说明 |
|------|----------|------|
| Python | DXCam / mss | DXCam 性能最好 |
| C# | SharpDX / Windows.Graphics.Capture | Win10+ 推荐后者 |
| C++ | DXGI Desktop Duplication | 最高性能方案 |
| Go | robotgo | 跨平台支持 |
| Rust | scrap / windows-capture | 性能好，内存安全 |

### 图像处理

| 功能 | 推荐方案 |
|------|----------|
| 模板匹配 | OpenCV (TM_CCOEFF_NORMED) |
| 哈希计算 | xxhash (非常快) |
| 数组运算 | NumPy (Python) / ndarray (Rust) |

### HTTP 服务

| 语言 | 推荐框架 |
|------|----------|
| Python | Flask / FastAPI |
| C# | ASP.NET Core / Nancy |
| Go | net/http (内置) |
| Rust | axum / actix-web |
| Node.js | Express / Fastify |

---

## 九、现有文件对应关系

```
Dumper/
├── DumperGUI.py          → 阶段六：程序入口、单实例锁
├── MainWindow.py          → 阶段六：主窗口、UI、日志、相机控制
├── Worker.py              → 阶段一/五：CameraWorker + WebServerWorker
├── Node.py                → 阶段二/四：PixelBlock + Node + NodeExtractor
├── NodeExtractorData.py   → 阶段四：extract_all_data 完整数据提取
├── Database.py            → 阶段三：NodeTitleManager 图标数据库
├── Utils.py               → 阶段一/二：模板匹配、ColorMap加载
├── IconLibraryDialog.py   → 阶段六：图标库管理对话框
├── ColorMap.json          → 阶段二：颜色映射配置
├── node_titles.db         → 阶段三：SQLite 图标数据库
├── mark8.png              → 阶段一：模板标记图片 (8x8)
├── deploy.py              → 打包脚本 (Nuitka)
└── test_script.py         → 功能测试脚本
```

---

## 十、关键注意事项

### 10.1 像素布局依赖

本项目的数据布局与 [PixelAddonX2](https://github.com/liantian-cn/PixelAddonX2) 插件紧密耦合。如果要修改布局：

1. 必须同时修改插件和 Dumper 的布局定义
2. 坐标计算基于 8×8 节点，确保总尺寸是 8 的倍数
3. 保持两个 mark8.png 锚点的相对位置

### 10.2 图标数据库

- 首次运行需要手动添加未匹配的图标标题
- 数据库会随使用自动增长（相似度匹配自动添加）
- 建议定期备份 node_titles.db

### 10.3 性能考虑

| 优化点 | 建议 |
|--------|------|
| 截图频率 | 30-60 FPS 足够，过高会增加 CPU 负担 |
| 模板匹配 | 只在启动时执行，之后固定区域捕获 |
| 数据库查询 | Hash 查询 O(1)，余弦相似度 O(n) |
| 内存缓存 | 将数据库加载到内存加速匹配 |

### 10.4 反检测建议

1. **修改像素布局**：调整数据区域的排列方式
2. **修改颜色映射**：使用不同的 RGB 值编码
3. **修改端口**：不使用默认 65131 端口
4. **修改模板图片**：替换 mark8.png 为其他标记
5. **修改代码特征**：编译为不同语言，改变程序结构

---

## 附录：快速参考

### 坐标速查表

| 数据项 | 坐标 (X, Y) | 说明 |
|--------|-------------|------|
| 技能序列 | (2..37, 2) | 36个技能 |
| 玩家BUFF | (2..33, 4) | 32个BUFF |
| 玩家DEBUFF | (2..9, 6) | 8个DEBUFF |
| 玩家职业 | (38, 5) | 纯色节点 |
| 玩家职责 | (39, 5) | 纯色节点 |
| 玩家血量 | (45, 4) | 亮度值 |
| 玩家能量 | (45, 5) | 亮度值 |
| 目标存在 | (38, 6) | 白色=true |
| 目标血量 | (45, 6) | 亮度值 |
| Focus存在 | (38, 8) | 白色=true |
| 队友1存在 | (10, 14) | 白色=true |
| 队友1血量 | (12, 14) | 亮度值 |
| 队友2存在 | (22, 14) | 白色=true |
| 队友3存在 | (34, 14) | 白色=true |
| 队友4存在 | (46, 14) | 白色=true |

### 亮度值解码速查

| 亮度 | 时间 |
|------|------|
| 0 | 0s |
| 50 | ~2.5s |
| 100 | 5s |
| 150 | 30s |
| 200 | 155s |
| 255 | 375s |
