# Rewrite Root README

## Goal

Replace the root README with a concise Chinese project notice that presents the repository as learning material, clearly summarizes the MIT permissions, disclaims responsibility for derivatives and services, and records the requested project history in a table.

## Non-goals

- Do not explain architecture, implementation principles, setup, operation, performance, anti-cheat behavior, or AI-assisted refactoring.
- Do not change subproject documentation, source code, licenses, or repository structure.
- Do not invent links or availability claims for unreleased projects.

## Constraints

- Follow the root MIT license and retain its notice-preservation condition in the summary.
- Treat the learning-only statement as project purpose, not as a restriction on MIT-granted rights.
- Preserve separately identified third-party license terms.
- Modify and commit each intended non-plan file separately; commit this plan last.
- Do not push.

## Chosen approach

Replace the full README with a title plus four compact parts: learning-purpose statement, MIT/license statement, derivative-and-service disclaimer, and one two-column history table. Use repository-relative links for existing subprojects. Leave Phantom and Copilot unlinked because they are not present in the repository.

The history table is frozen as follows:

| Stage | Projects |
| --- | --- |
| `WoW 12.1（尚未发布）` | `Phantom` and `Copilot`, as plain text |
| `WoW 12.0（即将过时）` | `DejaVu` and `Terminal`, linked to their local directories |
| `上一代` | `EZPixelAddonX2`, `EZPixelDumperX2`, `EZPixelRotationX2`, and `EZPixelDumperX2.NET`, linked to their local directories; append `EZPixelDumperX2 的 .NET 版本` to the last item |
| `上上代` | `EZAddonX2`, `EZBridgeX2`, and `EZDriverX2`, linked to their local directories |
| `辅助工具` | `EZAssistedX2`, `EZAssistedX2.NET`, and `EZAssistedX2.PY`, linked to their local directories |

## Expected files

- `README.md`
- `.plan/2026-07-16-rewrite-readme.md`

## Implementation steps

1. Replace the existing root README content with the concise project notice.
2. State that project-owned subproject code uses MIT and may be used, copied, modified, published, distributed, sublicensed, or sold when required notices are retained.
3. State that the repository is published only for learning and reference, without limiting MIT rights.
4. State that derivative authors and users bear responsibility and that no deployment, maintenance, support, consulting, or other service is provided.
5. Add the exact frozen history rows above, with relative links for all existing projects and plain text for Phantom and Copilot.
6. Verify content, links, Markdown structure, and diff scope.

## Acceptance criteria

- The root README contains no architecture, principle, implementation, setup, operational, performance, anti-cheat, or AI-refactoring explanation.
- The README prominently communicates the learning-only purpose.
- The README prominently communicates MIT permissions, including modification and republication, while retaining the notice condition.
- The README contains no commercial-use prohibition or other restriction that conflicts with MIT.
- The README explicitly disclaims responsibility for modified and derivative versions.
- The README explicitly states that no services or support are provided.
- The history table includes every requested project in the requested generation/status and identifies `EZPixelDumperX2.NET` as the .NET version of `EZPixelDumperX2`.
- Existing projects use valid relative links; Phantom and Copilot have no fabricated links.
- Only the expected files change.

## Verification

- Review `git diff --check`.
- Inspect the rendered Markdown structure and table source.
- Confirm every relative project target and `LICENSE` exists.
- Search the rewritten README for removed topics and conflicting restrictions.
- Confirm `git status --short` contains only intended files before commits.

## Risks

- A blanket license statement could accidentally claim ownership of bundled third-party material; mitigate by limiting the statement to project-owned code and preserving separately identified third-party terms.
- “Learning only” could be read as a use restriction; mitigate by explicitly stating that it describes purpose and does not narrow MIT rights.
- Status labels are time-sensitive; retain the exact user-requested labels without adding unsupported dates.

## Decision record

- Use a two-column table because status and generation can be expressed together without extra empty cells.
- Use relative links so links continue to work in forks and branches.
- Do not link Phantom or Copilot because no corresponding repository paths or confirmed URLs exist.
- Replace rather than edit the old sections because all existing substantive sections are outside the requested scope.

## Final status

Completed. The root README was replaced with the concise learning-purpose, license, disclaimer, and history content defined by this plan. Independent logic and clarity reviews both approved the result with no findings.

## Final verification results

- `git diff --check`: passed; Git emitted only the expected informational LF-to-CRLF working-copy warning.
- Required path checks: passed for `LICENSE` and all 12 linked local project directories.
- Content inspection: confirmed that Phantom and Copilot are unlinked, all requested projects and statuses are present, and removed explanatory/commercial-prohibition topics are absent from the root README.
- Scope inspection: confirmed that the implementation commit contains only `README.md`.
- Executable tests: not applicable to this documentation-only change.

## Remaining risks

- History status labels are intentionally time-sensitive and will require future documentation updates.
- Separately identified third-party material remains governed by its own license terms, as stated in the README.
- The disclaimer is consistent with the repository license but is not jurisdiction-specific legal advice.

## Commits

- `ca655a5` — `docs: rewrite project README`
- This plan is committed last; its commit hash remains available in Git history.
