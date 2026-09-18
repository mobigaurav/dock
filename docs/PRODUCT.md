# Dock — product

Dock is not a code reviewer. Developers still review and still merge.

Dock answers a different question: **did the agent tell the truth about what it did?**

## The objection

> Enterprises have developers to review agent code. Why would they pay for this?

They would not — if Dock tried to replace those developers. That product already exists (CodeRabbit, Copilot review, Cursor Bugbot) and it competes with the people who sign the merge.

Dock competes with **reconstruction**, not with judgment.

## Two jobs that got glued together

| Job | Who is good at it | What it costs |
|---|---|---|
| Judgment — architecture, product fit, “should we ship this?” | Senior developers | What you hired them for |
| Reconstruction — “the agent said tests were added, were they?” | Nobody enjoys this | 15–40 minutes per agent PR before real review starts |

Agents did not remove the first job. They exploded the second. A human intern who writes a 200-line PR also writes a 6-line summary a reviewer can check by eye. An agent writes a 2,000-line PR and a confident novel. Developers *can* verify every sentence. They cannot do that eight extra times a day without becoming clerks.

Enterprises already buy this category for other floods: Snyk does not mean they fired security engineers. CI does not mean they fired QA. They buy a gate so expensive humans work on the remainder.

## What the buyer is actually buying

1. **Volume.** Cursor, Claude Code, and Copilot turned one PR into ten. Review capacity did not 10x. The merge queue is the new bottleneck.
2. **Claim verification.** Developers read diffs. They are slow at checking prose (“backward compatible”, “no extra queries”, “covers the empty state”) against the tree. Dock fail-closes those sentences against git paths and the patch. It does not run the test suite or call a model.
3. **Audit.** “A senior LGTM’d a 2,000-line agent PR” is a weak story after an incident. Pass/fail/unknown cards are a receipt. Unknown is not green.
4. **Morale.** Staff engineers did not join to babysit bots. If the clerical layer is mechanical, they keep doing the job only a human can do.

## Cost model (illustrative, not measured)

Assume a fully loaded senior at **$100/hour** and **8 extra agent PRs/week**.

If reconstruction is **25 minutes** per PR before judgment starts:

- 3.3 hours/week × 48 weeks ≈ **$16,000/year/engineer** spent proving the agent’s homework
- Dock at **$30/seat/month** is **$360/year**

The tool wins if it gives back two hours a week *or* catches one false “safe migration” that would have been an incident. Enterprises do not buy it to fire the reviewer. They buy it so the reviewer is not the intern’s proofreader.

## Who pays

- Engineering orgs that **already allowed** coding agents and now have a review bottleneck
- Platform / DevEx teams asked for an “AI code policy” with evidence, not a wiki
- Staff engineers who will install a Cursor skill themselves (bottom-up, like GitHub)

## Who does not pay

- Companies that banned AI-authored code
- Teams with two people and two PRs a week
- Anyone shopping for “AI that reviews instead of my team”

## Anti-pitch (never say this)

- “You don’t need developers to review agent PRs.”
- “Dock approves the merge.”
- “The model is confident, so the claim passes.”
- “This only works for Cursor.”

## Pitch (say this)

Developers still own the merge. Dock is the lie detector and the morning inbox for agent output — Cursor, Claude, Copilot, or anything else that opens a PR — so review time goes to judgment. When claims are ready, Dock shows a Merge button. A person has to click it.

## Surfaces (not Cursor-only)

| Client | What it is |
|---|---|
| CLI | `dock inbox` / `dock merge` on any git repo |
| Cursor skill | One front-end to that CLI |
| MCP | Same engine in Claude Desktop / Claude Code |
| GitHub merge button | The actual click. `dock merge --execute` is a typed-confirmation shortcut in a human terminal |

The engine reads git and `gh`. It does not require the project to have been built in Cursor.

## Human merge button

`dock merge --pr N` **never merges**. It prints claim cards and the GitHub Merge URL.

`dock merge --pr N --execute` only runs if stdin is a TTY and a person types `MERGE #N`. Failed claims block execute. Unknown claims block execute unless that person also passes `--accept-unknown`. Agents are instructed not to run `--execute` and cannot satisfy the TTY gate by piping.

## Surface

- Uncommitted work and recent commits (facts from git)
- Open PRs (facts from `gh` when available)
- `agent_source` when a tool can be detected
- Claims: **pass**, **fail**, or **unknown**
- Merge preview + human click. Pass is not an approve.
