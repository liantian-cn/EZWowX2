# Historical Source Snapshots

Historical evidence only. This migration does not revalidate these checkouts or builds.

## Snapshot

The material was consolidated on 2026-09-05 and checked against these local references:

| Reference | Branch | Revision | Primary area |
| --- | --- | --- | --- |
| `@wow-ui-source` | `ptr` | upstream `a89e9d0c` (Build 69587); local archival commit `288f40d5` | FrameXML and generated API documentation for the recorded build |
| `@PhantomProject` | `develop` | `f6935113` | Optional, low-priority historical Lua examples |
| `@Shigure` | `main` | `b73d242f` | Optional, low-priority external Lua examples |

These repositories are read-only references. Do not modify, fetch, pull, reset, switch branches, or commit in them unless the user explicitly requests an update. The two Lua example repositories have limited value and are not design bases, implementation constraints or API evidence; consulting them is optional.

The 42 pre-consolidation Markdown files are preserved outside the project in the archive `phantom-5796e240-context-original-20260905.tar.gz` with SHA-256 `cd9137d4c6922c37e7fdf1b528c9113944b42c7bd8905567fe384bb57f7eeb54`.

## 2026-09-12 reference verification

The read-only `@wow-ui-source` reference was checked on 2026-09-12: version 12.1.0.69587, revision `a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58`. Historical archival revisions above are preserved as historical evidence; this does not establish current checkout availability.

## 2026-09-14 macro-binding verification

At the time of this verification, the configured local checkout for `@wow-ui-source` was unavailable on that machine.
The same recorded revision `a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58` was inspected online at
[SecureTemplates.lua](https://raw.githubusercontent.com/Gethe/wow-ui-source/a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua).
Its macro action reads `macrotext` when no macro-slot attribute is supplied and calls `C_Macro.RunMacroText`.
The click handler selects the down or up action according to `useOnKeyDown` / `ActionButtonUseKeyDown`.
This is pinned source evidence, not verification of a running game build or protected execution.
The user designated [EZWowX2 Blood/Macro.lua](https://raw.githubusercontent.com/liantian-cn/EZWowX2/refs/heads/main/DejaVu/DejaVu_DeathKnight/Blood/Macro.lua)
as the standard example for Phantom's generated bindings. Existing historical snapshots above remain unchanged.

## Blood DK condition verification — 2026-09-12

Reference: @wow-ui-source, 12.1.0.69587,
revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58.
PlayerScriptDocumentation.lua defines GetRuneCooldown with optional absence and no secret-return annotation;
Blizzard_UnitFrame/Mainline/RuneFrame.lua branches on runeReady. UnitDocumentation.lua marks
RUNE_POWER_UPDATE payloads secret: the plugin ignores them and queries all six runes again.
UnitPowerPercent accepts powerType, unmodified and a curve; the result is sent directly to Cell.
SpellDocumentation.lua defines GetSpellCooldownDuration(spellIdentifier, ignoreGCD), MayReturnNothing.
The user identifies 61304 as the fixed GCD spell; spell_gcd queries it directly with false and no spellbook test.
The absence of a duration renders black. This does not establish the actual in-game 61304 behavior;
game loading/rendering verification remains outstanding. Wiki requests for GetRuneCooldown/UnitPowerPercent
failed during this task, so API signatures are documented from the local source, not claimed as live Wiki evidence.

## Initial development-rule snapshot

The original development rules also recorded `@wow-ui-source` at upstream `a89e9d0c` with an additional local archival commit that must not be discarded, `@PhantomProject` at `f6935113e686`, and `@Shigure` at `b73d242f`. Short revisions locate historical snapshots; new evidence needs the actual full revision or source file.
