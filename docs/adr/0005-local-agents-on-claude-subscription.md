# Local agents on the Claude Code subscription

Implementing issues automatically needs somewhere to run Claude Code agents and a way to pay for them. The owner already pays for a Claude subscription and has a Mac that can host the work.

**Decision**: agents run on the owner's Mac using Claude Code authenticated with the owner's subscription, not an Anthropic API key. At most three run at once (`docs/agent-pipeline-design.md` P13). When a usage limit is reached, the agent labels the issue `agent-paused` and retries after the limit resets (P16).

**Why**: API-key billing for parallel agents costs far more than the subscription already paid for. Local execution also keeps checks next to the code (P18, P20).

**Consequences**: throughput is bounded by subscription usage limits and Mac resources, not by budget. The Mac must be on and logged in for work to progress. Whether the subscription terms allow unattended headless use on self-hosted runners was not verified and must be checked before relying on this decision.

## Considered options

- **GitHub-hosted Actions with `anthropics/claude-code-action` and an API key.** Recommended, rejected on cost. Would run in parallel without the Mac.
- **Scheduled cloud routines** polling for ready issues. Rejected: adds latency and does not keep checks local.
