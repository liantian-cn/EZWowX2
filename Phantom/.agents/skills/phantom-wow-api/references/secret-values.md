# Secret Values

## Working model

A Secret Value is an opaque value controlled by WoW's restricted environment. It is not equivalent to `nil`, false, zero, or missing data. Whether a value is secret depends on the API, value, unit, game state, and current build.

Assume combat-derived values are potentially secret until proven otherwise, especially values derived from units, auras, casts, cooldowns, targets, threat, nameplates, and encounters.

## Unsafe operations

Do not perform ordinary Lua operations on a potentially secret value unless the current API contract permits them. Unsafe operations include:

- comparison or Boolean branching;
- arithmetic, length, indexing, iteration, sorting, or counting;
- concatenation, formatting, truncation, or serialization;
- table-key use or persistence intended to reveal identity;
- using display callbacks, visibility, layout, or timing as a side channel.

Diagnostic functions such as `issecretvalue`, `hasanysecretvalues`, or script-object secret checks identify restrictions; they do not remove them.

## Supported direction

When the business need is display, pass the value directly into a documented consumer that accepts secret inputs. Depending on the current build, useful consumer families include:

- StatusBar and texture display APIs;
- curve evaluation and color curves;
- duration objects and duration text or cooldown bindings;
- managed AuraContainer and AuraButton display bindings.

Do not read a secret value into Lua control flow merely to calculate the display. Preserve the engine-to-widget pipeline.

## Phantom consequence

Phantom may render information that Lua cannot inspect and let the Python side observe the resulting pixels. Every condition plugin must document:

1. the producer API and its secrecy predicates;
2. the consumer used to render the value;
3. whether Lua performs any forbidden branching or conversion;
4. the pixel encoding and Python decoding pair;
5. the fallback when the rendered region is unavailable or invalid.

A plugin may not translate “secret” into an empty Cell. Empty output means only what that plugin's explicit protocol says it means.

## NeverSecret is narrow

`Enum.SecrecyLevel.NeverSecret` is an explicit exemption attached to particular values such as selected spells. It is not a property that an addon can assign. Check `@wow-ui-source/Interface/AddOns/Blizzard_AuraContainer/Blizzard_AuraContainerUtil.lua` and current generated documentation before relying on it.

## Verification checklist

- Is the producer annotated as secret, conditionally secret, or NeverSecret?
- Can the consumer accept that secret input directly?
- Does any intermediate Lua code compare, index, count, format, or branch on it?
- Does the approach expose information through button count, position, visibility, events, or timing?
- Is the evidence tied to the target build and pinned revision?

If any answer is uncertain, mark the path unverified and keep it out of a normative plugin contract.

Historical Blood DK verification is in [source snapshots](history/source-snapshots.md).
