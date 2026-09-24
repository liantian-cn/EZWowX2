# Flexoki Palette (Historical)

This is the former Phantom palette, retained for historical lookup only. Current colors are defined in the [TUI specification](../tui.md) and `phantom/ui/theme.py`. The original role mapping below is not the current theme.

Source: the official Flexoki color scheme, `kepano/flexoki` (https://stephango.com/flexoki), retrieved on 2026-09-12. Values below are transcribed without conversion or rounding. This is reference data; project usage rules live in [the TUI specification](../tui.md).

## Base scale

| Token | Hex |
| --- | --- |
| black | #100F0F |
| base-950 | #1C1B1A |
| base-900 | #282726 |
| base-850 | #343331 |
| base-800 | #403E3C |
| base-700 | #575653 |
| base-600 | #6F6E69 |
| base-500 | #878580 |
| base-300 | #B7B5AC |
| base-200 | #CECDC3 |
| base-150 | #DAD8CE |
| base-100 | #E6E4D9 |
| base-50 | #F2F0E5 |
| paper | #FFFCF0 |

## Accent scale

The official palette maps the 600 step to the light theme and the 400 step to the dark theme. Phantom uses the 400 step on its black background.

| Token | Hex | Token | Hex |
| --- | --- | --- | --- |
| red-600 | #AF3029 | red-400 | #D14D41 |
| orange-600 | #BC5215 | orange-400 | #DA702C |
| yellow-600 | #AD8301 | yellow-400 | #D0A215 |
| green-600 | #66800B | green-400 | #879A39 |
| cyan-600 | #24837B | cyan-400 | #3AA99F |
| blue-600 | #205EA6 | blue-400 | #4385BE |
| purple-600 | #5E409D | purple-400 | #8B7EC8 |
| magenta-600 | #A02F6F | magenta-400 | #CE5D97 |

## Phantom role mapping

| Phantom role | Flexoki token | Hex |
| --- | --- | --- |
| background | black | #100F0F |
| containers and footer | base-950 | #1C1B1A |
| nested surface | base-900 | #282726 |
| button fill | base-850 | #343331 |
| borders | base-800 | #403E3C |
| scrollbar | base-700 | #575653 |
| disabled text | base-600 | #6F6E69 |
| secondary text | base-500 | #878580 |
| muted labels | base-300 | #B7B5AC |
| body text | paper | #FFFCF0 |
| selection and emphasis | blue-400 | #4385BE |
| state on | green-400 | #879A39 |
| state off and warning | orange-400 | #DA702C |
| error | red-400 | #D14D41 |
| secondary accent | purple-400 | #8B7EC8 |
| info | cyan-400 | #3AA99F |
| yellow | yellow-400 | #D0A215 |
| magenta | magenta-400 | #CE5D97 |
