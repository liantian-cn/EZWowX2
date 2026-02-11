# PixelDumperX2 项目规范

## 项目概述

PixelDumperX2 是一个用于《魔兽世界》的像素数据捕获和解析工具。它通过捕获游戏屏幕上的像素块（由游戏内插件 [PixelAddonX2](https://github.com/liantian-cn/PixelAddonX2) 生成），解析出游戏状态数据，并通过 HTTP API（端口 65131）提供 JSON 格式的数据输出。

**核心设计理念**：将游戏内的"秘密值"数据编码为屏幕角落的彩色像素块，外部程序通过屏幕捕获获取结构化信息，绕过游戏 API 的数据访问限制。

## 项目结构

```
PixelDumperX2/
├── AGENTS.md              # 本文件 - 项目规范
├── Dumper.md              # Dumper模块详细规范
├── README.md              # 项目说明
├── pyproject.toml         # Python项目配置
│
└── Dumper/                # 主要代码目录
    ├── DumperGUI.py       # 程序入口
    ├── MainWindow.py      # 主窗口（UI、日志、相机控制）
    ├── Worker.py          # 工作线程（CameraWorker + WebServerWorker）
    ├── Node.py            # 像素节点类（PixelBlock + Node + NodeExtractor）
    ├── NodeExtractorData.py  # 数据提取函数（extract_all_data）
    ├── Database.py        # 节点标题管理器（NodeTitleManager）
    ├── Utils.py           # 工具函数（模板匹配、ColorMap加载）
    ├── IconLibraryDialog.py  # 图标库管理对话框
    ├── ColorMap.json      # 颜色映射配置
    ├── node_titles.db     # 图标标题数据库
    ├── mark8.png          # 模板标记图片
    ├── icon.ico           # 程序图标
    ├── deploy.py          # Nuitka打包脚本
    ├── test_script.py     # 功能测试脚本
    └── comment_deleter.py # AST注释删除工具
```

## 核心数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                         游戏内 (PixelAddonX2)                        │
│  游戏数据 → 编码为像素块 → 显示在屏幕角落                              │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         PixelDumperX2                               │
│                                                                     │
│  1. DumperGUI.py (入口)                                             │
│         ↓                                                           │
│  2. MainWindow.py (UI控制)                                          │
│         ├── CameraWorker (DXCam屏幕捕获)                            │
│         │       ↓                                                   │
│         ├── Utils.py (find_template_bounds 定位像素区域)            │
│         │       ↓                                                   │
│         ├── NodeExtractor (提取8x8节点)                             │
│         │       ↓                                                   │
│         ├── Node (解析颜色/亮度/哈希/标题)                           │
│         │       ↓                                                   │
│         ├── Database.py (NodeTitleManager 标题匹配)                 │
│         │       ↓                                                   │
│         ├── NodeExtractorData.py (extract_all_data 组装数据)        │
│         │       ↓                                                   │
│         └── WebServerWorker (HTTP API :65131)                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    外部程序 (PixelRotationX2)                        │
│  HTTP GET → JSON数据 → 决策逻辑 → 游戏指令                           │
└─────────────────────────────────────────────────────────────────────┘
```

## 模块详解

### 1. DumperGUI.py - 程序入口

**职责**：应用程序入口点，确保单实例运行。

**核心逻辑**：
- 使用 Windows 互斥锁 (`CreateMutexW`) 防止多实例运行
- 创建 `QApplication` 和 `MainWindow`
- 错误码 183 (`ERROR_ALREADY_EXISTS`) 检测重复启动

```python
# 单实例检查
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "DumperGUI")
if ctypes.windll.kernel32.GetLastError() == 183:
    # 已有实例运行，退出
```

### 2. MainWindow.py - 主窗口

**职责**：GUI 主窗口，负责 UI 展示、用户交互、相机控制和数据处理。

**核心组件**：

| 组件 | 说明 |
|------|------|
| `LogEmitter` | 日志信号发射器，线程安全地发送日志到主线程 |
| `LogRedirector` | 日志重定向器，将 print 输出重定向到 QTextEdit |
| `MainWindow` | 主窗口类 |

**MainWindow 关键属性**：
- `pixel_dump: dict` - 当前像素数据
- `camera: dxcam.DXCamera` - DXCam 相机对象
- `camera_worker: CameraWorker` - 相机工作线程
- `web_server: WebServerWorker` - Web 服务器线程
- `title_manager: NodeTitleManager` - 图标标题管理器

**主要功能**：
1. 显示器选择和 FPS 设置
2. 相机启停控制
3. 帧数据处理（`process_captured_frame`）
4. 遮挡检测（验证节点颜色一致性）
5. 图标库管理对话框

### 3. Worker.py - 工作线程

**职责**：后台工作线程，包括屏幕捕获和 HTTP 服务。

#### CameraWorker

```python
class CameraWorker(QThread):
    data_signal = Signal(np.ndarray, str)  # 图像数据信号
    log_signal = Signal(str)               # 日志信号
```

**核心逻辑**：
- 使用 DXCam 的 `camera.start()` 持续捕获指定区域
- 通过 `get_latest_frame()` 获取最新帧
- 发送信号到主线程处理

#### WebServerWorker

```python
class WebServerWorker(QThread):
    # Flask HTTP 服务器，端口 65131
    # 所有路径返回 pixel_dump JSON 数据
```

**API 特性**：
- 监听 `0.0.0.0:65131`
- 捕获所有路径请求（`/` 和 `/<path>`）
- 返回 JSON 格式的游戏状态数据
- 支持 CORS 跨域访问

### 4. Node.py - 像素节点

**职责**：定义像素数据的基本单元和提取引擎。

#### PixelBlock（像素块）

最基础的数据单元，表示一组像素数组。

**核心属性**：
| 属性 | 说明 |
|------|------|
| `hash` | xxhash 哈希值 |
| `mean` | 亮度均值 (0-255) |
| `percent` | 亮度百分比 (0-100%) |
| `is_pure` | 是否为纯色块 |
| `color` | 颜色值 (仅纯色块) |
| `remaining` | 从亮度解码的剩余时间（秒） |
| `white_count` | 白色像素数量 |

#### Node（节点）

8x8 像素节点，包含坐标和像素数组。

**区域划分**：
```
  0   1   2   3   4   5   6   7
┌───┬───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │   │  full: 完整 8x8
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │  middle: 中心 6x6 (哈希计算)
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │
├───┼───┼───┼───┼───┼───┼───┼───┤      inner: 中间 4x4 (亮度计算)
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ ░ │ ░ │ ░ │ ░ │ █ │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │ █ │ █ │ █ │ █ │ █ │ █ │   │
├───┼───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │ □ │ □ │  footnote: 右下 2x2 (类型标识)
└───┴───┴───┴───┴───┴───┴───┴───┘
```

**核心属性**：
- `title`: 通过 NodeTitleManager 获取的可读标题
- `footnote_title`: 右下 2x2 区域解析的类型（如 PLAYER_BUFF、ENEMY_DEBUFF）

#### NodeExtractor（节点提取器）

像素数据提取引擎，从图像数组中提取节点信息。

**核心方法**：
| 方法 | 说明 |
|------|------|
| `node(x, y)` | 获取指定坐标的 8x8 节点 |
| `read_health_bar(left, top, length)` | 读取白色进度条（吸收盾/血量） |
| `read_spell_sequence(left, top, length)` | 读取技能序列（图标、冷却、充能） |
| `read_aura_sequence(left, top, length)` | 读取 Buff/Debuff 序列 |

### 5. Database.py - 节点标题管理器

**职责**：管理图标标题数据库，支持 hash 匹配和余弦相似度匹配。

#### TitleRecord（标题记录）

```python
@dataclass
class TitleRecord:
    id: int
    full_data: bytes          # base64 编码的 8x8x3 数组
    middle_hash: str          # middle 区域的哈希值
    title: str                # 标题名称
    match_type: str           # 'manual' | 'cosine'
    created_at: str
    footnote_title: str       # 图标类型
```

#### NodeTitleManager

**核心功能**：
1. **Hash 直接匹配**：O(1) 时间复杂度
2. **余弦相似度匹配**：阈值默认 0.99
3. **未匹配节点记录**：用于手动添加

**匹配优先级**：
1. Hash 直接匹配 → 返回标题
2. 余弦相似度匹配（≥阈值）→ 自动添加到数据库，返回标题
3. 未匹配 → 记录到未匹配列表，返回 hash

### 6. NodeExtractorData.py - 数据提取

**职责**：从 NodeExtractor 提取完整的游戏状态数据。

#### extract_all_data()

**输出数据结构**：
```python
{
    'timestamp': '2024-01-01 12:00:00',
    'misc': {
        'ac': '护甲类型',
        'on_chat': True,
        'is_targeting': True
    },
    'player': {
        'unitToken': 'player',
        'aura': {
            'buff_sequence': [...],
            'buff': {...},
            'debuff_sequence': [...],
            'debuff': {...}
        },
        'spell_sequence': [...],
        'spell': {...},
        'status': {
            'unit_health': 85.5,
            'unit_power': 60.0,
            'unit_in_combat': True,
            'unit_class': 'WARRIOR',
            'unit_role': 'DAMAGER',
            # ... 更多状态
        }
    },
    'target': {...},
    'focus': {...},
    'party': {
        'party1': {...},
        'party2': {...},
        # ...
    },
    'signal': {...},
    'spec': {...}
}
```

### 7. Utils.py - 工具函数

**职责**：图像处理工具和配置加载。

**核心函数**：
| 函数 | 说明 |
|------|------|
| `load_template(path)` | 加载模板图片 |
| `find_all_matches(screenshot, template, threshold)` | OpenCV 模板匹配 |
| `find_template_bounds(screenshot, template_path)` | 查找两个标记点确定的矩形边界 |

**ColorMap 配置**：
- 自动加载 `ColorMap.json`
- 包含职业、职责、图标类型的颜色映射

### 8. IconLibraryDialog.py - 图标库管理

**职责**：图标库管理对话框，提供 9 个 Tab 页面。

**Tab 页面**：
1. 敌人释放的减益 (PLAYER_DEBUFF, BLEED, ENRAGE, POISON, DISEASE, CURSE, MAGIC)
2. 玩家施放的减益 (ENEMY_DEBUFF)
3. 友方施放的增益 (PLAYER_BUFF)
4. 友方施放的技能 (PLAYER_SPELL)
5. 敌方释放的技能 (ENEMY_SPELL_INTERRUPTIBLE, ENEMY_SPELL_NOT_INTERRUPTIBLE)
6. 其他 (NONE, Unknown)
7. 未匹配图标
8. 相似度匹配记录
9. 设置（阈值调整、数据导入导出）

## 代码风格规范

### 1. Import 规范

**强制要求：所有 import 必须在文件头部**

```python
# 正确
import os
from pathlib import Path
import numpy as np

def process():
    pass

# 错误
def process():
    import numpy as np  # 禁止！
```

**import 分组顺序**：
1. 标准库（os, sys, datetime 等）
2. 第三方库（numpy, cv2, PIL 等）
3. 项目内部模块（from Node import xxx）

### 2. TypeHint 规范

使用 Python 3.12+ 语法：

```python
def process_data(
    data: np.ndarray,
    threshold: float = 0.5,
    enabled: bool = True
) -> dict[str, Any] | None:
    """处理数据。"""
    pass

# 使用 | 替代 Optional 和 Union
def find_item() -> str | None:
    pass

# 使用内置泛型
def get_items() -> list[dict[str, Any]]:
    pass
```

### 3. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `CameraWorker`, `NodeTitleManager` |
| 函数/方法 | snake_case | `capture_window`, `get_title` |
| 常量 | UPPER_SNAKE_CASE | `SIMILARITY_THRESHOLD` |
| 私有方法 | _前缀 | `_init_database`, `_load_data` |
| 保护属性 | _前缀 | `self._hash_cache`, `self._running` |

### 4. 注释规范

**文件头 docstring**：极简单行

```python
"""窗口捕获模块 - Win32 API窗口截图与相机工作线程。"""
```

**区域分隔注释**：使用井号行

```python
####### Win32 API初始化 #######

####### 像素区域访问 #######

####### 信号定义 #######
```

## 依赖要求

```toml
[project]
requires-python = ">=3.12,<3.13"

dependencies = [
    "dxcam==0.0.5",
    "flask==3.1.2",
    "numpy==2.4.2",
    "opencv-python==4.13.0.90",
    "pillow==12.1.0",
    "pyside6==6.10.1",
    "pywin32==311",
    "xxhash==3.6.0",
]
```

## 运行方式

```bash
# 方式1：进入目录运行
cd Dumper
python DumperGUI.py

# 方式2：从项目根目录运行
python Dumper/DumperGUI.py
```

## 测试

```bash
cd Dumper
python test_script.py
```

## 打包部署

```bash
cd Dumper
python deploy.py
```

使用 Nuitka 编译为 Windows 可执行文件，输出到 `build/DumperGUI.dist/`。

## 相关项目

- **PixelAddonX2**: 游戏内插件，负责生成像素块
- **PixelRotationX2**: 外部决策程序，消费 HTTP API 数据

## 注意事项

1. **单实例运行**：程序使用互斥锁确保只有一个实例运行
2. **遮挡检测**：程序会验证节点颜色一致性，检测游戏窗口是否被遮挡
3. **图标库管理**：首次运行需要手动添加未匹配的图标标题
4. **相似度阈值**：默认 0.99，可在设置中调整
