# Issue-first workflow for code and config changes

Agents will implement work from GitHub issues without the owner reviewing each change (see `docs/agent-pipeline-design.md` P22, P27). Without a rule, agents change code directly from conversation and nothing records what was asked or why.

**Decision**: application code and deploy or runtime config (compose files, Dockerfiles, `.gitignore`, env templates, CI) change only through a GitHub issue whose spec a new agent with no prior context can implement. Docs, ADRs, agent-instruction files, investigation, and discovery do not need an issue. A change is a small fix, committed without an issue, unless it changes behavior, touches auth, access control, PHI, database schema, or secrets, needs a new or changed test, or spans more than one file or about 20 lines. The owner saying "just change it" skips the issue.

**Why**: the spec becomes the only review artifact before automated merge, so it must exist and be complete. Config is included because a compose or `.gitignore` change can break production or leak secrets as easily as code. The owner excluded small fixes to keep tracking manageable, and the triggers are mechanical so agents don't judge what counts as small.

## Considered options

- **Application code only.** Rejected: config changes such as replacing production credentials would bypass the spec, and nothing reviews them before merge.
- **Every tracked file.** Rejected: docs and agent instructions are written during discussion, and issues for them add overhead without value.
- **No small-fix threshold.** Rejected by the owner: every typo would need an issue, which makes tracking unwieldy.
