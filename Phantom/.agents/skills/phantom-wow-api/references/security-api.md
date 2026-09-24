# Security and API Verification

## Combat and taint

WoW distinguishes ordinary addon code from secure and protected execution. Code that works out of combat may fail during combat lockdown, and tainted code can prevent protected actions.

Before touching secure frames, attributes, bindings, templates, or protected actions:

- check whether creation or mutation is allowed during combat;
- create static secure objects during initialization when possible;
- defer prohibited mutations until the documented post-combat event;
- do not replace Blizzard functions; use supported hooks;
- check forbidden/access restrictions before touching objects received from Blizzard code.

`hooksecurefunc` is a post-hook and cannot change the original return value. Frame script extension uses supported script hooks; neither mechanism grants access to secret data.

## Hardware actions

Protected actions such as casting, targeting, or running macro text require a secure action path and a hardware event. Phantom's generated Lua connects a real key event to an invisible `SecureActionButtonTemplate`; the Python side sends that key to the game window. Revalidate the exact secure-button setup in the target build before implementation.

The user-designated example for Phantom's generated bindings is [EZWowX2 Blood/Macro.lua](https://raw.githubusercontent.com/liantian-cn/EZWowX2/refs/heads/main/DejaVu/DejaVu_DeathKnight/Blood/Macro.lua). Use it for the intended pattern, then verify API behavior against the target-build source; historical verification is in [source snapshots](history/source-snapshots.md).

## API query playbook

Follow [source verification](source-verification.md), search the exact API name with `rg`, and inspect both generated documentation and Blizzard usage. Check [version changes](wow-12.1-changes.md) when signatures or restrictions may have changed.

## Modern namespace cautions

Many modern APIs live under `C_*` namespaces and return structures rather than legacy multi-return tuples. Some data loads asynchronously and may return `nil` before an event signals availability. Never infer a signature from an older project.

Lua in WoW is not a normal standalone Lua environment. Do not assume filesystem I/O, package loading, `require`, `dofile`, or a newer language feature exists.

## Review checklist

- Is the API present at the pinned revision?
- Is the signature copied from generated documentation rather than memory?
- Can any argument, return, event payload, or script object be secret or forbidden?
- Does the call mutate a protected object or binding during combat?
- Does a third-party example target the same build?
- Is every uncertain statement labeled unverified?
