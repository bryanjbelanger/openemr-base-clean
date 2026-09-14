# Agents on the Claude Code subscription

Implementing issues automatically needs somewhere to run Claude Code agents and a way to pay for them. The owner already pays for a Claude subscription.

**Decision**: agents run on GitHub-hosted runners with `anthropics/claude-code-action`, authenticated with the owner's subscription through the `CLAUDE_CODE_OAUTH_TOKEN` secret, not an Anthropic API key (`docs/agent-pipeline-design.md` P10). When a usage limit is reached, the agent labels the issue `agent-paused`, and a scheduled workflow retries it hourly (P16, #10).

**Revised 2026-09-14**: agents originally ran on the owner's Mac, at most three at once. The owner moved them to GitHub-hosted runners (#8).

**Why**: API-key billing for parallel agents costs far more than the subscription already paid for.

**Consequences**: throughput is bounded by subscription usage limits, not by budget. The Mac no longer needs to be on for agents, only for PR checks (ADR-0006). Whether the subscription terms allow unattended headless use in GitHub Actions has not been verified and must be checked before relying on this decision.

## Considered options

- **GitHub-hosted Actions with `anthropics/claude-code-action` and an API key.** Recommended, rejected on cost.
- **Agents on the owner's Mac with a local Claude Code login.** The original decision, replaced on 2026-09-14.
- **Scheduled cloud routines** polling for ready issues. Rejected: adds latency.
