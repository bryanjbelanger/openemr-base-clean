# Self-hosted GitHub Actions runners on a public repo

The PR check workflow needs a runner with PHP and the repo's dependencies. The repo `bryanjbelanger/openemr-base-clean` is public.

**Decision**: three self-hosted GitHub Actions runners on the owner's Mac run the PR check workflow (`docs/agent-pipeline-design.md` P22). The 53 inherited OpenEMR workflows are disabled in GitHub settings so only the owner's integration workflows run (P24).

**Revised 2026-09-14**: agent jobs, dependency dispatch, and the `agent-paused` retry moved from these runners to GitHub-hosted runners (P10, P11, #8, #9, #10). Only the PR check job still runs on the Mac.

**Why**: runners react to GitHub events immediately, and GitHub queues jobs beyond three, so no scheduler code is needed. The owner does not accept outside pull requests on this temporary project.

**Consequences and required mitigations**:

- On a public repo, workflows triggered by outside users can run code on the Mac. The PR check job fails for pull requests from other repositories before checking out code. Agent workflows start only for the owner or the pipeline's GitHub App bot. Outside-contributor workflow runs must require approval. Not accepting pull requests does not prevent them from being opened.
- Runners run as a user-level LaunchAgent. Agent jobs no longer run on them, so they no longer need the Claude Code login in the user keychain.
- Actions must stay enabled, so the inherited workflows are disabled individually instead of turning Actions off.

## Considered options

- **launchd job polling `gh issue list` every 60 seconds.** Recommended, rejected by the owner. Needs no Actions and no inbound path, at the cost of up to a minute of latency.
- **GitHub webhook forwarded to the Mac through a tunnel.** Rejected: a tunnel into the Mac must stay open.
- **Agent jobs on these runners.** The original decision, replaced on 2026-09-14 by GitHub-hosted runners.
