# Source Verification

Use this reference when adding or reviewing a WoW API, event or access claim. User instructions and frozen plans take precedence over project contracts, which take precedence over technical references. Target-build official source is authoritative for API and behavior verification within that scope. Do not promote an unresolved claim or historical example into a requirement.

## Evidence order

1. Read the actual target-build `@wow-ui-source` generated API definitions and FrameXML.
2. Check Blizzard's accompanying API and version-change records.
3. Use other sources as leads; validate against the target-version source. If local evidence is inaccessible, use explicitly pinned official source online and state the limitation.

`@PhantomProject` and `@Shigure` are optional, low-priority historical/external Lua examples with limited value. They are not design bases, implementation constraints or API evidence; consulting or reusing them is not required.

Record verification date, actual version/build, full revision and relevant source paths. Never label an old local snapshot as current-version proof. If sources disagree or behavior cannot be established, mark it unverified and do not implement a guessed contract.

## Local checkout

Resolve `@wow-ui-source` through the session's configured reference. Check availability and inspect its actual version and revision before citing it. Do not assume it is available because a historical record used it. Reference subpaths use `/`, for example `@wow-ui-source/Interface/AddOns/`.
The external source repositories are read-only references outside Phantom, not dependencies or writable task worktrees. Do not import them into this repository; updates, edits, fetch/pull, branch changes, resets and commits need an explicit user request.

## API comments

For APIs central to the business logic, add a Lua long comment near `api cache` explaining purpose, signature, arguments, returns and relevant restriction markers. Ordinary auxiliary calls only need concise Chinese end-of-line comments under the project's Lua style.
Obtain explanatory API documentation from the corresponding latest [Warcraft Wiki](https://warcraft.wiki.gg/wiki/) page and keep its exact link. Explain the current interface rather than legacy migration or unrelated page content. A Wiki description does not establish availability or permissions in the target build: verify those in source.
If the page cannot be read, disclose that limitation and distinguish source-derived notes from fetched Wiki evidence. Do not invent a successful lookup.

## Update discipline

Treat combat, unit, aura, spell, cooldown, cast, target, threat and nameplate values as potentially secret until the current build proves otherwise. Recheck volatile claims when the build or source revision changes. Keep technical identifiers and references in English, examples task-specific, and conclusions no stronger than the evidence.

## Historical evidence

Read [source snapshots](history/source-snapshots.md) only to trace an earlier verification. Those dates, revisions and availability observations are historical and were not reverified by the documentation migration.
