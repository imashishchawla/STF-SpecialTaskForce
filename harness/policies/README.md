# Policy contract (future)

Policy is data evaluated by the harness, not instructions entrusted to an LLM. Deny by default. Match an action against the authenticated runner, agent version, task, exact target, requested capability, admin policy, current approval token, budget, and trace requirement.

The precedence is: host/OS hard restrictions and STF hard denials → administrator policy → exact task approval → bundle capability request → agent suggestion. Lower layers narrow authority only. An approval token is short lived and bound to action, target, version, and expiry. A changed target or action invalidates it.

Policy decisions must produce a reason code and policy version in the trace. Critical failures, missing identity, unavailable approval checks, or required trace gaps pause side effects. This directory contains no enabled policy engine yet.
