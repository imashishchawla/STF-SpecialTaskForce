# Record lifecycle

## Record status

- `candidate`: lead found; claims are preliminary.
- `needs_review`: a proposal has enough source material for independent review, but required claims are incomplete or unresolved.
- `verified`: an independent curator has accepted all required material claims with current authoritative evidence.
- `superseded`: replaced by a new version/credential; retain history and link successor.

Record lifecycle is separate from each claim's status: `verified`, `not_found`, `conflicting`, `unavailable`, `stale`, or `unknown`.

## Update protocol

Workers create isolated proposals only. An independent curator checks evidence and duplicates, then returns a patch and decision. The coordinator applies accepted patches serially to the knowledge index or prepares website content. Human review is required before any public site content change is merged or published. Do not self-review or silently overwrite evidence.

## Freshness

Every source claim carries an access date and, when available, source publication/update date. Recheck time-sensitive availability, price, assessment, and enrollment claims for each report that presents them as current. If no fresh evidence is found, mark stale or unknown and exclude from current verified totals.
