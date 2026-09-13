# Agent Pipeline Design

Decision log for turning GitHub issues into merged code with Claude Code agents running on the owner's Mac. Decisions came from a grilling session on 2026-09-13. Deeper rationale for the four hardest-to-reverse decisions lives in `docs/adr/0004`–`0007`.

Decisions use `P` codes so they don't collide with the `D` codes in `docs/production-auth-hardening-plan.md`.

This is a one-person project. Review of this document does not gate the build (P27), so every rejected option and every place the owner overrode the recommendation is recorded for the reviewer.

## End-to-end flow

1. An agent writes a spec as a GitHub issue with the `write-issue-spec` skill (P5–P8).
2. A no-context sub-agent reviews the spec until it has no gaps (P6).
3. The agent applies `ready-for-agent`, unless the spec touches a sensitive area, in which case the owner applies it (P8).
4. The label event starts a job on one of three self-hosted runners on the Mac (P11–P13). The job exits if the issue has open blockers (P14).
5. The job runs a Claude Code agent with the implement skill in the runner's own checkout (P15). Hooks check each edit and block finishing until checks pass (P18).
6. The workflow pushes the agent's single commit to a branch, opens a PR, and enables auto-merge. A pre-push git hook runs the same checks (P18).
7. A PR check workflow on the Mac runner runs the fast checks. Branch protection requires it, and GitHub auto-merges with a squash (P19, P22, P23).
8. The merge closes the issue, which starts any labeled issues it was the last blocker for (P14).
9. The owner is notified on merge, check failure, or a blocked or stopped agent (P16, P17).

## Decisions

### When an issue is required

| # | Decision | Why | Rejected |
|---|---|---|---|
| P1 | Application code and deploy or runtime config (compose files, Dockerfiles, `.gitignore`, env templates, CI) require a GitHub issue. Docs, ADRs, and agent-instruction files do not. | Config breaks production as easily as code, and under P22 nothing reviews it before merge. Docs are written during discussion, so issues for them add overhead without value. | Code only (the owner's first answer, changed after the config challenge). Every tracked file. See ADR-0004. |
| P2 | A change needs an issue if it changes behavior, touches auth, access control, PHI, database schema, or secrets, needs a new or changed test, or spans more than one file or about 20 lines. Anything else is a small fix committed on its own. | The owner wanted small fixes out of tracking. Each trigger is mechanically checkable, so agents don't judge "small". | No threshold (recommended, rejected as unwieldy). |
| P3 | If the owner says "just change it", the agent skips the issue. | Keeps the owner able to act fast without editing rules. | Always require an issue. |
| P4 | No linking requirements: branch names, commits, and PRs need not reference the issue. | Keep the flow light and add governance only if needed. | Branch name with issue number plus `Closes #N` in the PR body (recommended). |

### Specs

| # | Decision | Why | Rejected |
|---|---|---|---|
| P5 | Each spec lists the files it expects to change. A spec overlapping an open issue gets a "blocked by" link. | Parallel agent PRs auto-merge without human review (P22), so conflicts must be prevented, not resolved after. | Let parallel PRs conflict and fix at merge. |
| P6 | Before labeling, a fresh sub-agent with only the issue and the repo lists anything it would have to guess. The author fixes every gap, then runs one second review. After round 2 the author fixes only gaps that would produce a wrong or unsafe result, records the rest under Assumptions, and labels. Revised 2026-09-13 after the first pipeline specs. | Directly tests the rule that a no-context agent can implement the spec. Looping until the list is empty did not converge: round 2 still found 4–14 edge cases per issue, and ten parallel reviewers hit the subscription session limit. | A written checklist, which only tests that sections are filled in. Looping until a reviewer returns an empty list (the original P6). |
| P7 | The agent asks the owner only when a decision meets the P2 sensitive-area trigger, cannot be undone, contradicts a recorded decision, or leads to materially different user outcomes. Other choices are recorded under the spec's Assumptions section. | Keeps interruptions rare for a one-person project while leaving every autonomous choice visible. | None proposed. |
| P8 | The agent applies `ready-for-agent`, except for specs meeting the P2 sensitive-area trigger. Those notify the owner and wait for the owner's label. | Most work flows with no human step. The sensitive set is the only remaining human checkpoint under P22 and P27. | Owner always labels. Agent always labels. |
| P9 | Always-on rules (P1–P3, P7) live in `CLAUDE.md`, which stays at or under 200 lines. The spec template, the P6 review, and the P8 labeling rule live in the `write-issue-spec` skill. | `CLAUDE.md` loads every session and must stay token-friendly. The skill loads only when writing a spec. | Everything in `CLAUDE.md` (over 200 lines). Everything in the skill (agents could miss the issue rule). |

### Running agents

| # | Decision | Why | Rejected |
|---|---|---|---|
| P10 | Agents run on the owner's Mac using Claude Code on the owner's existing subscription. | The subscription is already paid for. API-key billing costs far more. | GitHub-hosted Actions with `anthropics/claude-code-action` and an API key (recommended). Scheduled cloud routines. See ADR-0005. |
| P11 | Self-hosted GitHub Actions runners on the Mac pick up work from GitHub events. | Event-driven with no polling delay, and the owner does not accept outside pull requests. | A launchd job polling `gh issue list` every 60 seconds (recommended, needs no Actions and no inbound path). A webhook forwarded through a tunnel. See ADR-0006. |
| P12 | Adding the `ready-for-agent` label starts an agent. | The label is a deliberate gate, so an unreviewed spec does not become a PR. | Starting on issue creation. |
| P13 | Three runner instances are registered, which caps parallel agents at three. GitHub queues the rest. | The cap comes from subscription usage limits (R3) and Mac CPU and memory, not runner cost. GitHub does the queueing, so no scheduler code is needed. Raise it later if useful. | One runner that starts background agents and caps them itself. |
| P14 | A dependency is finished when its PR merges and the issue closes. A job for an issue with open blockers exits. Closing an issue triggers a workflow that starts labeled issues with no remaining open blockers. Blocking uses GitHub's native issue dependencies. | Building on an unmerged PR builds on code that may change. Automatic dispatch removes manual relabeling. | Dependency done when its PR opens. Owner relabels by hand. |
| P15 | The `implement-issue` skill implements an issue from its spec in the runner's persistent checkout, runs the checks, and leaves one commit. The `agent-implement` workflow pushes the branch, opens the PR, and enables auto-merge. Revised 2026-09-13 during spec review of #8. | `piv-implement-issue` expects an RCA artifact that specs don't have, and the `piv-*` skills are vendored. Each runner already has its own checkout, so worktrees add nothing. A workflow step for push and PR is deterministic, costs no tokens, and cannot be skipped by the agent. | Modifying `piv-implement-issue`. The skill creating a worktree and opening the PR itself (the original P15). |
| P16 | After 3 blocked attempts to finish, the agent stops, labels the issue `agent-blocked`, and notifies the owner. On a usage limit it labels `agent-paused` and retries after the limit resets. | Caps wasted tokens at a known count. Most check failures are lint or type errors an agent can fix. | Stop on the first failure. |
| P17 | Notify on PR merged, checks failed, and agent blocked or stopped, to macOS Notification Center and the owner's phone via ntfy.sh. | These events need attention. "Started" and "PR opened" add noise without action. | Notifying on every event. |

### Checks and merging

| # | Decision | Why | Rejected |
|---|---|---|---|
| P18 | Checks run in four layers. After each edit, a Claude Code hook runs `php -l`, `phpcs`, and `eslint` on only that file, with output capped at 20 lines. On finish, a Claude Code hook runs `phpstan` on changed files plus `phpunit-isolated` and blocks finishing until they pass. Before push, a git hook runs the same script. In CI, the P19 checks run. | The owner wants lint and syntax caught by hooks with minimal tokens, and everything passing before CI. Each layer catches problems where they are cheapest. Hooks only run checks matching the changed file type. Git hooks can be skipped, so CI stays the gate (R4). | Checks in CI only. |
| P19 | The fast checks with no database gate auto-merge: PHP syntax, `phpstan`, `phpcs`, `phpunit-isolated`, `lint:js`, `test:js`. | Three parallel agents would each need a heavy OpenEMR stack for API and end-to-end suites. | Adding API and end-to-end suites now. Deferred until the pipeline proves itself, possibly against a shared stack on the local Kubernetes cluster. |
| P20 | PHP 8.5 and Composer run on the Mac. Each runner's persistent checkout keeps its own `vendor/`, installed once and reused. Revised 2026-09-13 during spec review of #8. | The edit hook must finish in about two seconds, and a container start per edit breaks that. PHP 8.5 is within the project's `>=8.2` requirement and is the version upstream CI tests most. Per-runner checkouts replace worktrees (P15), so there is no shared `vendor/` to link. | A throwaway PHP container per check. One `vendor/` shared across worktrees (the original P20). |
| P21 | Hook configuration is tracked in git in `.claude/settings.json` and `.githooks/`, with `core.hooksPath` set to `.githooks/`. | Agents in worktrees only get hooks that are tracked. These are new files, so upstream files stay untouched. | Per-machine untracked setup. |
| P22 | A PR check workflow runs the P19 checks on the Mac runner for every PR. Branch protection requires that check, and GitHub auto-merges when it passes. | The owner prefers automation over reviewing every PR. Using required checks means a failed or skipped check cannot merge, and the owner's own PRs get the same checks. | Owner reviews and merges every PR (recommended). The agent job merges its own PR. See ADR-0007. |
| P23 | Only squash merges are allowed, so each issue lands as one commit on `main` with a meaningful message. | The owner wants bite-size commits with meaningful messages. One commit per issue also pushes specs to stay small. | Several commits per issue with a merge commit. |
| P24 | GitHub Actions runs only for integrations the owner builds. The 53 inherited OpenEMR workflows are disabled in GitHub settings with `gh workflow disable`, and their files stay untouched. | Keeps OpenEMR as close to upstream as possible and avoids retesting untouched code. Actions must stay on for P11. | Turning Actions off repo-wide (recommended before P11, now incompatible). Deleting the workflow files. |

### Process

| # | Decision | Why | Rejected |
|---|---|---|---|
| P25 | Deployment is out of scope and gets a separate design once the first integration exists. | Nothing exists to deploy yet. | Deploying to the local Kubernetes cluster now. |
| P26 | The pipeline is built from dependency-ordered issues. The first issues are implemented by hand or with "just change it" until the pipeline can take over. | The build follows the workflow it creates and tests the specs before anything depends on them. | Building it in one session, then switching to issues. |
| P27 | Review of this design does not gate the build. The reviewer comments while work proceeds, and the agent uses the P7 rules to work with the owner on spec correctness. | One person cannot review and approve every issue within the time available. | Design PR approval before creating issues (recommended). Creating issues but holding labels until approval. |
| P28 | Decisions are recorded in this document with rationale, rejected options, and overrides, plus ADRs 0004–0007. | A reviewer needs to see what was weighed, not only what was chosen. | One ADR per decision. A GitHub epic issue. |

## Overrides of the recommendation

The owner chose differently from the recommendation in these decisions. Each is a deliberate trade toward speed and automation.

1. **P2** Small fixes are exempt. Recommended: no exemption.
2. **P4** No issue linking. Recommended: branch name and `Closes #N`.
3. **P10** Local subscription. Recommended: GitHub-hosted Actions with an API key.
4. **P11** Self-hosted runners. Recommended: launchd polling.
5. **P22** Auto-merge. Recommended: owner merges every PR.
6. **P27** No review gate. Recommended: approve the design before creating issues.

## Findings

1. **F1** The repo `bryanjbelanger/openemr-base-clean` is public, and GitHub does not link it to upstream as a fork.
2. **F2** Checks with no database exist: `composer php-syntax-check`, `phpstan`, `phpcs`, `phpunit-isolated`, `npm run lint:js`, `npm run test:js`.
3. **F3** `claude` and `gh` are installed on the Mac.
4. **F4** PHP and Composer were not installed on the Mac, and `vendor/` was absent. Node and `node_modules` were present.
5. **F5** No git hooks or `.claude/settings.json` existed.
6. **F6** `composer php-syntax-check` lints every PHP file and `composer phpstan` analyzes the whole project with a 4G memory limit. Both need per-file variants for hooks.
7. **F7** MacPorts installed PHP 8.5 as `php85` only, with no `php` link and no Composer.
8. **F8** `composer.json` requires PHP `>=8.2` with platform `8.2`. Upstream CI tests 8.2 through 8.6, most often 8.5.
9. **F9** Standard GitHub-hosted runners are free for public repos, so the inherited workflows cost noise, not Actions minutes.

## Risks

1. **R1** The repo is public, and the owner not accepting pull requests does not stop anyone from opening one. Agent workflows must trigger only on label events applied by the owner, and outside-contributor workflow runs must require approval. See ADR-0006.
2. **R2** A runner running as a system service may not reach the Claude Code login stored in the user keychain. Runners must run as a user-level LaunchAgent.
3. **R3** Three parallel agents consume subscription usage limits faster. P16 handles the limit being reached.
4. **R4** Git hooks can be skipped with `--no-verify`. The P22 required check is the actual gate.
5. **R5** `composer install` may report missing PHP extensions on the Mac.
6. **R6** Under P22 and P27, a change to auth or PHI access can reach `main` with no human review unless P8 routes it to the owner.
7. **R7** Whether the subscription plan's terms allow unattended headless use on self-hosted runners was not verified during the session. See ADR-0005.

## Open items for implementation specs

1. Measure `phpstan` time on changed files. If it is too slow for the finish hook, move it to the pre-push layer (P18).
2. List the exact PHP extensions `composer install` needs on the Mac (R5).
3. Verify R7 before relying on P10.
