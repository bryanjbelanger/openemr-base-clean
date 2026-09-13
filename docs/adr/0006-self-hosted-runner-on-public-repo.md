# Self-hosted GitHub Actions runners on a public repo

Local agents (ADR-0005) need a trigger when an issue gets the `ready-for-agent` label. The repo `bryanjbelanger/openemr-base-clean` is public.

**Decision**: three self-hosted GitHub Actions runners on the owner's Mac run the agent jobs, dependency dispatch, and the PR check workflow (`docs/agent-pipeline-design.md` P11, P13, P22). The 53 inherited OpenEMR workflows are disabled in GitHub settings so only the owner's integration workflows run (P24).

**Why**: runners react to GitHub events immediately, and GitHub queues jobs beyond three, so no scheduler code is needed. The owner does not accept outside pull requests on this temporary project.

**Consequences and required mitigations**:

- On a public repo, workflows triggered by outside users can run code on the Mac. Agent workflows must trigger only on `issues: labeled` and check that the actor is the owner. Outside-contributor workflow runs must require approval. Not accepting pull requests does not prevent them from being opened.
- Runners must run as a user-level LaunchAgent so jobs can reach the Claude Code login in the user keychain.
- Actions must stay enabled, so the inherited workflows are disabled individually instead of turning Actions off.

## Considered options

- **launchd job polling `gh issue list` every 60 seconds.** Recommended, rejected by the owner. Needs no Actions and no inbound path, at the cost of up to a minute of latency.
- **GitHub webhook forwarded to the Mac through a tunnel.** Rejected: a tunnel into the Mac must stay open.
