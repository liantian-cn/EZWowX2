# Terminal

该项目是[M.I.D.N.I.G.H.T/](https://github.com/liantian-cn/M.I.D.N.I.G.H.T/)项目的子项目。

接收并解析[DejaVu](https://github.com/liantian-cn/DejaVu)传来的信号，执行超维指令，直接操控游戏世界的生死轮回，执掌无限夜幕的迭代权柄。

## 新坑优势

本项目是[EZWowX2](https://github.com/liantian-cn/EZWowX2)项目的后续新坑，有诸多优势。

- 作者还在维护、更多的手写代码：为了去掉AI屎山，本项目代码手写量>95%，作者维护意愿更强。
- 使用兼容性更好的GDI截图：优化了算法，在Ryzen 9700X下能实现100fps。性能测试见`notes`目录。
- 游戏内设置：动态变量设置由游戏内插件完成。
- 循环热加载：在ide里编辑代码，保存后，rotation会自动重载。

## 使用方式

### 环境安装

如果你能看到github这个说明，我默认你有能力下载到下面的所有东西。

- 务必从[官网](https://www.python.org/downloads/release/python-31210/)下载python 3.12.10
- 安装UV，从[官网](https://github.com/astral-sh/uv)
- 从微软商店安装[Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701?hl=zh-CN&gl=CN)
- 使用`Windows Terminal`进入项目目录。
- `uv sync`完成依赖安装
- 执行`clear ; uv run .\main.py`运行程序。
- 将[DejaVu](https://github.com/liantian-cn/DejaVu)安装到游戏的插件目录。

### 基础逻辑

1. 游戏的屏幕右上角，会有一个`M.A.T.R.I.X`区域。区域内由4x4和8x8的像素区域构成。
2. [Terminal](https://github.com/liantian-cn/Terminal/)会读取这个区域。
3. 游戏逻辑由[Terminal](https://github.com/liantian-cn/Terminal/)解析并执行。
4. [DejaVu](https://github.com/liantian-cn/DejaVu)仅负责按键绑定和游戏内设置。

### Rotation循环

项目暂时只提供一份`死亡使者血DK`的循环逻辑。`熊`的循环有一份，但没有维护。

1. 在[Terminal](https://github.com/liantian-cn/Terminal/)端，逻辑的代码在`terminal\rotation\DeathKnightBlood.py`文件内。
2. 在[DejaVu](https://github.com/liantian-cn/DejaVu)端，逻辑代码在`06_spec\deathknight`目录内。
3. 你可以参考这两份文件的写法，完成自己的职业。
4. 默认的数据库，仅保存了血DK和熊的图标哈希，其他职业专精需要自己添加。
5. 布局在[布局.xlsx](https://1drv.ms/x/c/cad4d177ae3e2847/IQBWpPl3hgdIRIob6BQ6XbalAVZeY_LFzo9wHgzioLq6kDc?e=eNqLBO)
6. 阅读[docs](https://github.com/liantian-cn/Terminal/tree/main/docs/)的文档，书写循环。

-
