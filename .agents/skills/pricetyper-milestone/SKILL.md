---
name: pricetyper-milestone
description: Implement or review one PriceTyper milestone from docs/SPEC.md
---

# PriceTyper milestone workflow

1. Read root `AGENTS.md`, this skill, applicable `.agents/rules/`, and the sections of `docs/SPEC.md` named by the user.
2. Inspect the existing worktree and git diff. Identify the active milestone and its acceptance criteria in §12.
3. State a short implementation plan and list the files that should change. Do not continue into later milestones.
4. Implement the smallest complete change that satisfies the active milestone. Preserve existing behavior outside the request.
5. Add or update milestone tests described by §9. Run the narrow relevant tests first and the milestone acceptance command when the environment supports it.
6. Review the diff for scope drift, secrets, personal data, unsafe real senders in dry-run, accidental live TikTok interactions, and claims unsupported by test output.
7. Report what changed, exact checks run and their observed outcomes, checks not run, and remaining hardware/account-specific verification. Mark each acceptance item passed, failed, or not run.

## Safety invariants

- Default is disarmed. Do not enable `run.start_armed` in a committed example configuration.
- Never send to a real TikTok session during automated tests.
- Never add evasion, scraping, auto-purchase, or retry-on-send-failure behavior.
- Use dry-run and fake fixtures to validate candidate selection and sender mechanics.
