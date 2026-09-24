# 宏键位语法

## 固定宏键位池

`phantom/core/macro_keys.py` 的 `MACRO_KEYS` 使用 tuple 显式列出全部 148 个键位，不通过运行期组合生成。顺序固定如下；每行按主键列出的顺序展开，再依次进入下一行：

| 顺序 | 修饰键前缀 | 主键顺序 | 数量 |
| --- | --- | --- | --- |
| 1 | `RCTRL-` | `NUMPAD1`–`NUMPAD9`、`NUMPAD0` | 10 |
| 2 | `RSHIFT-` | `NUMPAD1`–`NUMPAD9`、`NUMPAD0` | 10 |
| 3 | `RCTRL-` | `F1`–`F12` | 12 |
| 4 | `RSHIFT-` | `F1`–`F12` | 12 |
| 5 | `RALT-` | `F1`–`F3`、`F5`–`F12` | 11 |
| 6 | `RALT-` | `NUMPAD1`–`NUMPAD9`、`NUMPAD0` | 10 |
| 7 | `RCTRL-` | `,`、`.`、`/`、`;`、`'`、`[`、`]`、`=` | 8 |
| 8 | `RALT-` | `,`、`.`、`/`、`;`、`'`、`[`、`]`、`=` | 8 |
| 9 | `RSHIFT-` | `,`、`.`、`/`、`;`、`'`、`[`、`]`、`=` | 8 |
| 10 | `RCTRL-RSHIFT-` | `NUMPAD1`–`NUMPAD9`、`NUMPAD0` | 10 |
| 11 | `RALT-RSHIFT-` | `NUMPAD1`–`NUMPAD9`、`NUMPAD0` | 10 |
| 12 | `RCTRL-RSHIFT-` | `F1`–`F12` | 12 |
| 13 | `RALT-RSHIFT-` | `F1`–`F3`、`F5`–`F12` | 11 |
| 14 | `RCTRL-RSHIFT-` | `,`、`.`、`/`、`;`、`'`、`[`、`]`、`=` | 8 |
| 15 | `RALT-RSHIFT-` | `,`、`.`、`/`、`;`、`'`、`[`、`]`、`=` | 8 |

`RALT-F4` 和 `RALT-RSHIFT-F4` 均不进入池；显式列表在这两处分别用中文注释说明跳过。首个键位为 `RCTRL-NUMPAD1`，最后一个为 `RALT-RSHIFT-=`。

每份 rotation 的全部宏按声明顺序独立从池开头分配，包括未引用宏；数量和配置兼容规则见[宏与键位](configuration.md#宏与键位)。池顺序是分配契约，不能排序、按引用过滤或依据旧 `key`/`bind_key` 改变分配结果。

## 内部键位语法

内核在加载 rotation 时解析自动分配的键位并冻结为 `KeyCombination`，同一键位字符串用于 Lua 绑定和展示。配置中的旧 `macros[].key` 不参与解析或校验。以下是公共解析器的能力范围，不是宏配置的自定义键位入口，也不扩大固定池。

公共解析器支持以下主键，标识区分大小写：

- `A`–`Z`、`0`–`9`、`F1`–`F24`、`NUMPAD0`–`NUMPAD9`。
- `NUMPADPLUS`、`NUMPADMINUS`、`NUMPADMULTIPLY`、`NUMPADDIVIDE`、`NUMPADDECIMAL`。
- `UP`、`DOWN`、`LEFT`、`RIGHT`、`HOME`、`END`、`PAGEUP`、`PAGEDOWN`、`INSERT`、`DELETE`。
- `SPACE`、`TAB`、`ENTER`、`ESCAPE`、`BACKSPACE`。
- 标点字面量：逗号、句点、斜杠、分号、单引号、左右方括号、反斜杠、等号、减号、反引号。

主键前仅可带不重复的 `RCTRL-`、`RALT-`、`RSHIFT-`，保留字符串中的顺序。减号主键写作 `-`，例如 `RCTRL--`。不保留通用 `CTRL`、`ALT`、`SHIFT` 枚举、解析支持或别名，也不支持左侧修饰键。解析器不接受小写、加号分隔、裸修饰键、鼠标按钮或任意未知键名；这些校验不适用于配置中被忽略的旧字段。

右侧键位池与发送端需配套使用；应用更新后须重新生成并加载 addon，使 Lua 覆盖绑定与发送键位一致。
