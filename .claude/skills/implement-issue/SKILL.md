---
name: implement-issue
description: Implement a GitHub issue spec written by write-issue-spec, make its checks pass, and leave exactly one commit. Use when the agent pipeline asks to implement a GitHub issue with this skill, or the user asks to implement a spec issue.
---

# Implement an Issue Spec

Run headless inside the agent pipeline (`.github/workflows/agent-implement.yml`), on a branch already created from `origin/main`. The workflow pushes, opens the PR, and enables auto-merge. This skill ends at one local commit.

## Steps

1. **Read the spec** with `gh issue view N`. Done when you can name every file in `Files to change` and every command in `Acceptance criteria`.
2. **Confirm the ground.** Read each file the spec names and check the Background facts against the repo. If a blocker's work is missing or a fact is wrong in a way the spec's Constraints say to stop on, stop now with a one-paragraph explanation and no commit.
3. **Implement** the Requirements in order, changing only the files in `Files to change`. The edit hook reports lint failures after each edit. Fix them before moving on.
4. **Verify** every Acceptance criterion that can run on this machine without the owner, and every command in the spec's `Checks` section. Done when each has run and passed. Criteria that need the owner, a merged PR, or GitHub state this job cannot create are listed as "not run here" in your final message.
5. **Commit** all changes as one commit whose subject is exactly the spec's `Commit title`. The body lists any choice you made that the spec did not state.
6. **Finish.** The finish hook runs the changed-file checks and blocks until they pass. Fix what it reports and try again.

## Rules

- The spec is the whole instruction. When it is silent on a detail, choose the option closest to the surrounding code and record it in the commit body.
- When the spec contradicts itself or the repo in a way that changes the outcome, stop with no commit and explain the contradiction. The workflow labels the issue `agent-blocked` for the owner.
- Keep to the spec's `Out of scope` and `Constraints` sections, and leave upstream OpenEMR files unchanged unless a requirement names them.
- The repo is public. Keep secret values and patient data out of commits, commit messages, and output.
