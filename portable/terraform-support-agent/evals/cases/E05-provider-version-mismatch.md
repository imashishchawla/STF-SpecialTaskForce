---
eval_id: E05
scenario: provider-version-mismatch
phase: 3
status: ready
created: "2026-10-02"
---

# E05 — Provider Version Mismatch (Fix Released in Newer Version)

## Scenario

The Source Researcher finds that the exact error the customer is hitting is a known bug in the AWS provider — and the fix was released in v5.31.0. The customer is on v5.28.0. The coordinator must identify the version-specific fix, provide the upgrade path, and state the discriminating check that confirms the upgrade resolves the issue (rather than claiming it as confirmed without the customer testing it).

---

## Input (paste this into coordinator)

```
Product: HCP Terraform
Terraform version: 1.5.7
AWS provider version: hashicorp/aws 5.28.0
Workspace: remote execution mode

Issue: Terraform plan errors on an aws_lb_listener resource with:
"Error: Invalid attribute combination: attribute 'default_action.0.forward.0.target_group' 
cannot be set when 'default_action.0.forward.0.stickiness' is not configured"

This worked fine 3 weeks ago. No HCL changes were made to this resource.
The only recent change was that the workspace pinned Terraform version was updated.

Evidence: Run log excerpt showing the above error at plan stage on aws_lb_listener resource.
No state lock. VCS connection not involved (manually triggered runs only).
```

---

## Expected output — key assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Source Researcher finds the relevant AWS provider changelog entry | Returns entry from hashicorp/terraform-provider-aws CHANGELOG referencing this specific error or the attribute behavior change |
| A2 | Source Researcher returns the exact fix version | States "fixed in v5.31.0" (or nearest applicable version) with full GitHub/changelog URL |
| A3 | Coordinator identifies version gap: customer on 5.28.0, fix in 5.31.0 | States the gap explicitly |
| A4 | Coordinator provides the upgrade path | `required_providers` version constraint update + `terraform init -upgrade` |
| A5 | Coordinator does NOT state this as confirmed resolved | States "this is likely resolved by upgrading to ≥5.31.0 — customer should test after upgrade" |
| A6 | Coordinator provides rollback guidance | What to do if the upgrade causes a different issue |
| A7 | Coordinator notes the Terraform version change as possibly related | 1.5.7 + AWS 5.28.0 interaction worth mentioning |

### Correct discriminating check (A5)

"After updating the `required_providers` constraint to `~> 5.31` and running `terraform init -upgrade`, trigger a new plan on the same workspace. If the error is gone, this confirms the fix. If the error persists on the new provider version, please share the updated run log."

### Correct upgrade path (A4)

```hcl
# In required_providers block:
aws = {
  source  = "hashicorp/aws"
  version = "~> 5.31"
}
```

Then:
1. Commit the version constraint change
2. Trigger a new run — HCP Terraform will download the updated provider
3. Confirm plan succeeds

Note: pinned workspace Terraform version (1.5.7) is not the cause — this is a provider-level bug fix.

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Fix version identified with URL | yes, with changelog URL | "upgrade the provider" without version |
| Version gap stated | yes (5.28.0 → ≥5.31.0) | vague "use a newer version" |
| Upgrade path correct | required_providers + init -upgrade | only mentions re-run without version change |
| Not stated as confirmed resolved | "likely resolved — test after upgrade" | "this will fix it" |
| Rollback guidance present | yes | no mention of what to do if upgrade causes issues |

---

## Evaluator notes

This eval tests whether the source researcher fetches version-specific changelog entries rather than generic documentation. The failure mode is returning "upgrade the provider" as advice without a specific version and without a URL. That is not actionable — the customer needs to know *which* version introduced the fix.

A secondary failure: claiming the Terraform version update (1.5.7) caused this. The Terraform Core version pinned in the workspace does not affect AWS provider attribute validation behavior — that is solely a provider SDK concern. The agent should not conflate these.
