"""
Summary:
    Phantom 纯黑配色与 Textual 深色主题配置。
Description:
    集中定义界面颜色角色，并据此注册界面唯一使用的深色主题。
Key Variables:
    MONOCHROME: Phantom 颜色角色。
    PHANTOM_THEME: 注册到 Textual 的 Phantom 深色主题。
Change Log:
    2026-09-12: Changed 界面配色为纯黑、深灰面板和明亮状态色。
"""

from textual.theme import Theme

MONOCHROME: dict[str, str] = {
    "base": "#000000",
    "panel": "#111111",
    "surface": "#222222",
    "border": "#333333",
    "muted": "#A1A1AA",
    "disabled": "#71717A",
    "text": "#EDEDED",
    "focus": "#FFFFFF",
    "green": "#4ADE80",
    "yellow": "#FBBF24",
    "red": "#F87171",
}

# 样式表保留稳定的语义变量名，颜色角色已全部映射到新的纯黑方案。
FLEXOKI: dict[str, str] = {
    "base": MONOCHROME["base"],
    "mantle": MONOCHROME["panel"],
    "crust": MONOCHROME["surface"],
    "surface_0": MONOCHROME["surface"],
    "surface_1": MONOCHROME["border"],
    "overlay_0": MONOCHROME["muted"],
    "overlay_1": MONOCHROME["disabled"],
    "subtext_0": MONOCHROME["muted"],
    "subtext_1": MONOCHROME["muted"],
    "text": MONOCHROME["text"],
    "blue": MONOCHROME["focus"],
    "green": MONOCHROME["green"],
    "orange": MONOCHROME["yellow"],
    "red": MONOCHROME["red"],
}

PHANTOM_THEME = Theme(
    name="phantom-monochrome",
    primary=MONOCHROME["focus"],
    secondary=MONOCHROME["muted"],
    accent=MONOCHROME["focus"],
    warning=MONOCHROME["yellow"],
    error=MONOCHROME["red"],
    success=MONOCHROME["green"],
    foreground=MONOCHROME["text"],
    background=MONOCHROME["base"],
    surface=MONOCHROME["panel"],
    panel=MONOCHROME["panel"],
    dark=True,
    variables={
        **{f"flexoki-{name.replace('_', '-')}": color for name, color in FLEXOKI.items()},
        "text": MONOCHROME["text"],
        "text-muted": MONOCHROME["muted"],
        "text-disabled": MONOCHROME["disabled"],
        "block-cursor-background": MONOCHROME["focus"],
        "block-cursor-foreground": MONOCHROME["base"],
    },
)
