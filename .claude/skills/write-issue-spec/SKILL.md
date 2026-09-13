---
name: write-issue-spec
description: Write an implementation spec as a GitHub issue that a no-context agent can implement, review it with a fresh sub-agent, and label it for the agent pipeline. Use when a change needs an issue under CLAUDE.md section 4, or the user asks for a spec, ticket, or issue.
---

# Write an Issue Spec

The spec is the only review artifact before an agent implements and auto-merges the change (`docs/agent-pipeline-design.md` P22, P27). Write it so a new agent with only the issue and the repo implements it without guessing.

## Steps

1. **Gather facts.** Read the code the change touches and record exact paths and line numbers. Look up every command, version, and setting in the repo or environment rather than recalling it. Done when every file the change will modify is known.
2. **Check overlap.** List open issues and their `Files to change` sections:
   ```sh
   gh issue list --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner)" --state open --json number,title,body
   ```
   Every open issue that lists a file this spec also changes becomes a blocker. Done when every open issue has been compared.
3. **Size it.** The work must fit one squash commit with one meaningful title (P23). If it needs two titles, split it into several specs linked by blockers and run these steps for each.
4. **Settle decisions.** Ask the user only under the conditions in CLAUDE.md section 4. Decide everything else and record it under Assumptions. Done when no requirement contains "TBD", "or", or "as appropriate".
5. **Write the body** from the template below into a scratchpad file.
6. **Create the issue** without a label:
   ```sh
   gh issue create --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner)" --title "<type(scope): summary>" --body-file <file>
   ```
7. **Link blockers** from step 2 with GitHub's native dependencies (details in `docs/agents/issue-tracker.md`):
   ```sh
   R=$(gh repo view --json nameWithOwner -q .nameWithOwner)
   gh api --method POST repos/$R/issues/<this>/dependencies/blocked_by -F issue_id="$(gh api repos/$R/issues/<blocker> --jq .id)"
   ```
8. **Run the no-context review.** Dispatch a fresh general-purpose sub-agent with only this prompt: "Read GitHub issue #N in this repo with `gh issue view N`. Do not implement it. List every point where you would have to guess, look something up that the spec should have stated, or choose between interpretations. Return an empty list if there are none." Fix each gap in the issue body with `gh issue edit N --body-file <file>`, then dispatch one new sub-agent for round 2. After round 2, fix only gaps that would produce a wrong or unsafe result and record the rest under Assumptions. Done after round 2's fixes, or earlier if a sub-agent returns an empty list.
9. **Label.** If the spec touches auth, access control, PHI, database schema, or secrets, leave it unlabeled and tell the user it is waiting for their `ready-for-agent` label (P8). Otherwise run `gh issue edit N --add-label ready-for-agent`.
10. **Report** the issue URL, its blockers, and whether it is labeled or waiting on the user.

## Template

```markdown
## Goal

<One or two sentences: the outcome, not the steps.>

## Background

<Current state with `path:line` references and why the change is needed. Link related P codes or ADRs.>

## Requirements

1. <Exact, testable action. Name files, values, and commands.>

## Files to change

- `path/to/file` (create | modify | delete)

## Acceptance criteria

- [ ] `<command>` <expected result>

## Checks

Run the checks matching the changed file types and make them pass: `php -l`, `composer phpcs`, `composer phpstan`, `composer phpunit-isolated`, `npm run lint:js`, `npm run test:js`.

## Commit title

`<type(scope): summary>`

## Assumptions

- <Each decision made without asking the user, and why.>

## Constraints

- <Things the implementer must preserve or stop and report on.>

## Out of scope

- <Adjacent work the implementer leaves alone.>

## Blocked by

- #<n>, or "None"
```

## Rules

- The repo is public, so issue bodies are public. Describe secrets and patient data by name and location, never by value.
- Acceptance criteria are commands with expected results. A criterion an agent cannot run is a gap.
- Leave upstream OpenEMR files untouched unless the requirement names them (P24).
