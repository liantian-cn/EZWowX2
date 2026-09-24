# WoW 12.1 Changes Relevant to Phantom

## Scope and verification

This page tracks only 12.1 changes that can affect Phantom's Lua-to-screen data path. It was reviewed on 2026-09-05 against `@wow-ui-source` upstream revision `a89e9d0c` (12.1.0 Build 69587) and the archived 12.1 weekly and consolidated change notes.

It is not a complete API diff. Revalidate every item when the local source revision changes.

## Secret and access controls

12.1 exposes more of the secrecy and access model in public script-object contracts:

- Frame script objects can carry secret aspects, forbidden aspects, and access restrictions.
- Script assignment and hooks may check forbidden aspects and reject secret arguments.
- `C_Secrets` and generated predicate documentation describe why a value may become secret; they do not provide a way to reveal it.
- Unit identity restrictions can make identity-related APIs secret in restricted contexts.

Relevant local evidence:

- `@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/SecretPredicatesDocumentation.lua`
- `@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/SecretPredicateAPIDocumentation.lua`
- `@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/SecretAspectConstantsDocumentation.lua`
- `@wow-ui-source/Interface/AddOns/Blizzard_RestrictedAddOnEnvironment/`

## Aura model

The 12.1 AuraContainer model is managed and display-oriented:

- `AuraContainer`, `ManagedAuraContainer`, Aura groups, Aura slots, and custom Aura buttons are implemented under `Blizzard_AuraContainer`.
- The container owns aura tracking, button allocation, filtering, ordering, and layout.
- Inbound regions and Aura buttons participate in forbidden-aspect and access-restriction checks.
- Layout names and helper structures changed during the 12.1 PTR sequence; examples from earlier weekly notes must be checked against Build 69587 source before use.
- NeverSecret spell handling is explicit in `Blizzard_AuraContainerUtil.lua`; do not generalize that exemption to ordinary auras.

The current implementation is the authority for method names:

- `@wow-ui-source/Interface/AddOns/Blizzard_AuraContainer/`
- `@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/AuraContainerSharedDocumentation.lua`
- `@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/AuraContainerUtilDocumentation.lua`

## Unit identity changes

Archived Build 68914 notes identify identity-sensitive behavior for APIs including `UnitClass`, `UnitClassBase`, `UnitRace`, group-role and group-leadership queries, and `GetInspectSpecialization`. These values may be secret when unit identity is restricted.

Phantom's generated rotation activation reads the local player's class and specialization during addon loading. Verify those exact calls in the target build and context; do not assume that an API being safe for `"player"` makes it safe for arbitrary unit tokens.

## Rendering additions

The 12.1 source includes newer rendering surfaces relevant to pixel output, including StatusBar render-mode methods and radial-progress texture methods. Their presence does not guarantee that every secret input can be converted into a readable Lua number. Prefer direct assignment from the secret producer to a consumer that explicitly accepts that input.

## Migration cautions

- Do not copy a 12.0 or early-12.1 AuraContainer example without checking current field and method names.
- Do not infer a combat decision from `IsShown`, callbacks, layout changes, button counts, or forbidden-state transitions.
- Do not use a deprecated global merely because an older project still contains it. Search generated API documentation and current FrameXML first.
- A display path and a readable-value path are different capabilities. Confirm each independently.

## Archived chronology

The original archive contains consolidated and weekly records for 12.0.0, 12.0.1, 12.0.5, 12.0.7, and 12.1.0. Use it only when a historical change is needed; copy verified conclusions back into this compact page instead of restoring the entire archive.
