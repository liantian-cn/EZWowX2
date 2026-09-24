# Rendering Primitives for Pixel Output

## Purpose

Phantom's generated addon renders a small screen-corner matrix for Python capture. The normative geometry lives in `.agents/skills/phantom-code-dev/references/pixel-protocol.md`; this page records WoW-side primitives and restrictions.

## Frames and regions

- Create frames and regions during addon initialization, outside combat-sensitive mutation paths.
- Give only objects that must be referenced later a global name.
- Anchor each object deterministically and clear old anchors before re-anchoring an existing object.
- Keep the matrix at a stable scale and pixel-aligned position. UI scale, render scale, antialiasing, and post-processing can alter edge pixels.
- Render solid interiors and treat borders as untrusted. Phantom therefore samples only the middle 2×2 of a 4×4 Cell and the middle 6×6 of an 8×8 Icon Tile.

## Cell

A Cell is a 4×4 solid-color region. The Python side reads only `[1:3, 1:3]`. A plugin must define how RGB or brightness maps to its business value and how invalid or non-uniform samples fall back.

Do not assume grayscale unless the plugin contract says so.

## Value Bar

A Value Bar is four pixels high and `4n` pixels wide. Python reads the middle two rows, counts pixels exactly equal to white `(255, 255, 255)`, and returns the white percentage in the range 0–100.

This pattern is useful when WoW can display a secret value as bar fill but Lua cannot inspect the number. The plugin still owns the mapping between the rendered percentage and its business value.

## Icon Tile

An Icon Tile occupies 8×8 pixels. Python ignores the one-pixel border and hashes the contiguous middle 6×6 array with `xxh3_64_hexdigest` and seed zero. An all-black trusted region represents an absent slot.

Hash stability depends on identical capture channel order and pixel bytes. Capture backends must expose a common channel-order contract before hashes are shared across them.

## Secure macro button

The established runtime-binding pattern is:

```lua
local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
frame:SetAttribute("type", "macro")
frame:SetAttribute("macrotext", macroText)
frame:RegisterForClicks("AnyDown", "AnyUp")
SetOverrideBindingClick(frame, true, key, buttonName)
```

This creates an invisible secure action button and a priority override binding. It does not create a saved macro-slot entry or overwrite the persistent keybinding database. The configured key's normal action is shadowed while the override exists.

Create and configure these secure objects at a permitted time. Recheck combat-lockdown and protected-operation behavior in the target build before implementation.

## Local references

- `@wow-ui-source/Interface/AddOns/Blizzard_RestrictedAddOnEnvironment/`
