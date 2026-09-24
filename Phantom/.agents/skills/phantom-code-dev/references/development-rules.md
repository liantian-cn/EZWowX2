# 开发规则

适用于代码实现；Lua 专属格式见 [Lua 开发规则](lua-development.md)。项目规范使用中文，WoW 技术背景保持英文，技术标识符保持英文。

## 分支与范围

- 日常开发只在 `develop` 分支修改 Phantom；`main` 由 GitHub Actions 发布过滤后的快照，同步工作流仅在用户授权下于 `main` 维护。发布规则见根 [README](../../../../README.md#分支与对外同步)。
- 根 `README.md` 预留给最终用户说明；详细规范写入所属 skill 的 references；同一规则只维护一份，跨 skill 按需引用。
- 不得把 `@wow-ui-source`、`@PhantomProject`、`@Shigure` 纳入 Phantom 仓库。
- 外部源码目录作为只读参考。除非用户明确要求更新，不得修改、提交、切换分支、fetch、pull 或 reset。

## 代码表达

- 代码应优先清楚表达业务步骤；只有技术细节遮蔽业务流程、具有独立职责或确有复用边界时才抽取。
- 变量、函数、类、模块等代码标识符使用英文，并遵循对应语言与项目的既有命名方式。
- 业务解释和业务注释使用中文；API、字段、类型和协议名称保持其原始英文。
- 不为业余桌面工具擅自加入生产服务器式可用性、故障隔离或自动恢复机制。
- 不得以“运行时可以修”为理由交付已知的确定性失败。

## Python Type Hint

所有手写 Python 文件强制使用 Type Hint：

- 所有函数和方法参数、返回值。
- 类属性和实例属性。
- 容器类型。
- 类型不明显的局部变量。

明显的简单局部变量与循环变量不强制逐个标注。第三方代码和生成代码不受本条约束。所有手写 Python 源码由 mypy strict 检查。

## Python 工程与运行

使用 Python 3.13 和 pip。`requirements.txt` 固定运行依赖，`requirements-dev.txt` 引入运行依赖并固定开发工具及其依赖。
`pyproject.toml` 保存工程元数据、pytest、mypy 和 Ruff 配置；本阶段直接从仓库运行，不建立发行包或插件安装机制。

Windows PowerShell 在仓库根目录执行：

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m phantom.main
.venv/Scripts/python demo/demo.py
.venv/Scripts/python demo/demo01.py
```

仅运行时安装 `requirements.txt` 即可。`python -m phantom.main` 启动 Textual 主程序，读取或创建启动工作目录下的 `phantom.toml`；
在仓库根目录启动时配置落在仓库根目录，换目录启动就使用该目录的配置，程序不改变工作目录。界面、配置与检测规则见 [tui.md](tui.md)。
demo 的时序与输出格式见插件规范，demo 不经过 TUI，也不读取应用配置。
独立 demo 统一放在项目根目录 `demo/`，执行时先打印演示内容，再开始采集流程。
像素解析 demo 同样等待 3 秒、采集 5 秒，停止后输出最后一帧的十个 Cell 亮度、
一个 ValueBar 的 ratio/percent 和两个 IconTile hash；截图错误或区域不足时明确失败，不回退旧帧。
WSL2／容器使用 Python 3.13 创建虚拟环境后，通过 `.venv/bin/python` 安装同一开发依赖并运行纯图像测试，GDI 仅支持 Windows。
源码变量和接口使用英文，业务注释与输出说明使用中文；不把本机 `.venv` 或 demo 截图提交到 Git。

## 必要文档头

新建的业务实现文件，或本次任务中发生实质修改的业务实现文件，需要完整文件头。局部修改遵循已有风格，不为补模板扩大改动。第三方库、测试、脚本、配置、工具、生成代码、锁文件和纯数据文件不要求该头部。

Lua 文件遵循 [Lua 开发规则](lua-development.md) 的专用格式；其他文件没有既有格式时，使用语言原生注释语法并保留以下英文标签：

```text
Summary:
    一行说明文件主要用途，不超过 120 个字符。
Description:
    说明业务内容结构或单一业务流程。
Key Variables:
    每行记录一个重要业务变量及含义；没有时写 None。
Change Log:
    YYYY-MM-DD: Added/Changed/Removed/Improved 已知的具体变更
```

不得编造历史。复杂函数内部只在有助于理解业务流程时增加解释，不以注释数量作为质量指标。插件还要满足 [插件开发手册](../../phantom-plugin-dev/references/common.md) 的专用说明。

## 安全与变更边界

- 不绕过 WoW 的保护机制或把 Secret Value 强制转换成普通值。
- 用户确认的键位覆盖风险适用于全部宏使用自动分配键位建立运行期覆盖绑定；旧 `bind_key` 不再控制该行为。该授权仅限运行期覆盖，不包含实际游戏操作或其他外部动作。
- 配置结构、像素布局或插件公共契约的变化必须先更新相应规范和迁移决策。
- WoW 技术参考是背景证据，不能覆盖项目规范；不要把历史示例或待定事项直接转为实施要求。

## 待定事项

- 打包、发布和正式版本号策略；当前工程元数据版本仅为基础占位。
- 新键盘后端的设备和权限要求由相应插件版本定义；当前 PostMessageW 在线程中发送，不自动提权。
