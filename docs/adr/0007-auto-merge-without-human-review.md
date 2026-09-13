# Auto-merge agent PRs without human review

This is an EHR that handles PHI, run by one person who cannot review every agent PR in the time available.

**Decision**: a PR check workflow on the self-hosted runner runs the fast checks with no database (PHP syntax, `phpstan`, `phpcs`, `phpunit-isolated`, `lint:js`, `test:js`) on every PR. Branch protection requires that check, only squash merges are allowed, and GitHub auto-merges when it passes (`docs/agent-pipeline-design.md` P19, P22, P23).

**Why**: the owner prioritizes automation and throughput. Required status checks mean a failed or skipped check cannot merge, and the owner's own PRs get the same gate.

**Consequences**: the spec (ADR-0004) and the fast checks are the only barriers before `main`. API and end-to-end suites do not gate merges yet. A change to auth or PHI access could reach `main` with no human review. The one remaining human checkpoint is that specs touching auth, access control, PHI, database schema, or secrets wait for the owner to apply `ready-for-agent` (P8). Revisit this decision if a merged change causes a PHI or auth incident.

## Considered options

- **Owner reviews and merges every PR.** Recommended for an EHR with PHI, rejected by the owner on time and cognitive load.
- **The agent job merges its own PR after local checks.** Rejected: no branch protection, so a skipped check could still merge, and the owner's own PRs would not be checked.
