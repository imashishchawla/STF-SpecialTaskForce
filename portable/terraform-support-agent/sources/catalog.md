---
schema_version: 1
last_updated: "2026-10-02"
maintainer: operator
---

# Source Catalog

Approved sources for the Source Researcher specialist. Entries are checked in priority order for each claim type. All URLs verified at last_updated date above.

---

## Priority Order by Claim Type

| Claim type | First check | Second check | Third check |
|---|---|---|---|
| Product behavior | Official HashiCorp Docs (versioned) | Provider/API reference | Release notes |
| Bug / regression | Release notes (exact version) | GitHub issues (hashicorp/<repo>) | Support KB |
| Current incident | Status page (status.hashicorp.com) | — | — |
| Provider-specific behavior | Provider docs (registry.terraform.io) | Provider GitHub releases | Provider GitHub issues |
| IBM support process | `memory/ops/` (session only, not persisted) | — | — |
| Community workaround | Not authoritative — label as unconfirmed | — | — |

---

## Tier 1 — Official HashiCorp Documentation

### Terraform Core

| Source | URL | Notes |
|---|---|---|
| Terraform Docs (all) | https://developer.hashicorp.com/terraform | Start here for CLI and core behavior |
| Terraform CLI Reference | https://developer.hashicorp.com/terraform/cli | Commands, flags, environment variables |
| Terraform Language Reference | https://developer.hashicorp.com/terraform/language | HCL syntax, modules, expressions |
| Terraform Internals | https://developer.hashicorp.com/terraform/internals | State format, graph, provider protocol |

### HCP Terraform (Terraform Cloud)

| Source | URL | Notes |
|---|---|---|
| HCP Terraform Docs | https://developer.hashicorp.com/terraform/cloud-docs/overview | Primary reference |
| HCP TF API Reference | https://developer.hashicorp.com/terraform/cloud-docs/api-docs | REST API for runs, workspaces, state |
| HCP TF Agents | https://developer.hashicorp.com/terraform/cloud-docs/agents | Agent pool config, private networking |
| HCP TF VCS | https://developer.hashicorp.com/terraform/cloud-docs/vcs | GitHub, GitLab, Bitbucket, Azure DevOps |
| HCP TF SSO/SCIM | https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/single-sign-on | SSO enforcement, SCIM provisioning |
| HCP TF Policies | https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement | Sentinel and OPA |
| HCP TF Run Tasks | https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/run-tasks | Run task pipeline |
| HCP TF Private Registry | https://developer.hashicorp.com/terraform/cloud-docs/registry | Private modules and providers |
| HCP TF State | https://developer.hashicorp.com/terraform/cloud-docs/workspaces/state | Remote state management |
| HCP TF Variables | https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables | Variable sets, workspace variables |
| HCP TF Cost Estimation | https://developer.hashicorp.com/terraform/cloud-docs/cost-estimation | Supported resources, limitations |

### Terraform Enterprise

| Source | URL | Notes |
|---|---|---|
| TFE Admin Docs | https://developer.hashicorp.com/terraform/enterprise | Self-hosted TFE administration |
| TFE Release Notes | https://developer.hashicorp.com/terraform/enterprise/releases | Version-specific changes |

---

## Tier 1 — Provider Documentation

### Provider Registry

| Source | URL | Notes |
|---|---|---|
| Public Provider Registry | https://registry.terraform.io/browse/providers | Browse all providers |
| AWS Provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs | Latest docs |
| AzureRM Provider | https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs | Latest docs |
| Google Provider | https://registry.terraform.io/providers/hashicorp/google/latest/docs | Latest docs |
| AzureAD / Entra Provider | https://registry.terraform.io/providers/hashicorp/azuread/latest/docs | Azure AD / Entra ID |
| Random Provider | https://registry.terraform.io/providers/hashicorp/random/latest/docs | |
| TFE Provider | https://registry.terraform.io/providers/hashicorp/tfe/latest/docs | Terraform Enterprise API |
| Kubernetes Provider | https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs | |
| Helm Provider | https://registry.terraform.io/providers/hashicorp/helm/latest/docs | |
| Vault Provider | https://registry.terraform.io/providers/hashicorp/vault/latest/docs | |

---

## Tier 1 — Release Notes and Changelogs

| Source | URL | Notes |
|---|---|---|
| Terraform Core Changelog | https://github.com/hashicorp/terraform/blob/main/CHANGELOG.md | Exact version fixes |
| AWS Provider Releases | https://github.com/hashicorp/terraform-provider-aws/releases | Use for exact fix version |
| AzureRM Provider Releases | https://github.com/hashicorp/terraform-provider-azurerm/releases | |
| Google Provider Releases | https://github.com/hashicorp/terraform-provider-google/releases | |
| HCP TF Release Notes | https://developer.hashicorp.com/terraform/cloud-docs/overview#release-notes | |

---

## Tier 1 — Status and Incidents

| Source | URL | Notes |
|---|---|---|
| HashiCorp Status Page | https://status.hashicorp.com | Current incidents ONLY — not historical causes |
| AWS Status | https://health.aws.amazon.com/health/status | For AWS-side issues |
| Azure Status | https://azure.status.microsoft/en-us/status | For Azure-side issues |
| GCP Status | https://status.cloud.google.com | For GCP-side issues |
| GitHub Status | https://githubstatus.com | For VCS webhook delivery issues |
| GitLab Status | https://status.gitlab.com | |
| Bitbucket Status | https://bitbucket.status.atlassian.com | |

---

## Tier 2 — GitHub Issue Trackers (official hashicorp repos)

Use only for: confirmed bugs with a fix version in release notes, or to check if an exact issue is known.
**Not authoritative**: open issues, unconfirmed comments, closed issues without a confirmed fix version.

| Source | URL |
|---|---|
| Terraform Core Issues | https://github.com/hashicorp/terraform/issues |
| AWS Provider Issues | https://github.com/hashicorp/terraform-provider-aws/issues |
| AzureRM Provider Issues | https://github.com/hashicorp/terraform-provider-azurerm/issues |
| Google Provider Issues | https://github.com/hashicorp/terraform-provider-google/issues |
| AzureAD Provider Issues | https://github.com/hashicorp/terraform-provider-azuread/issues |
| TFE Provider Issues | https://github.com/hashicorp/terraform-provider-tfe/issues |
| Kubernetes Provider Issues | https://github.com/hashicorp/terraform-provider-kubernetes/issues |

---

## Tier 2 — Support Knowledge Base

| Source | URL | Notes |
|---|---|---|
| HashiCorp Support KB (Terraform) | https://support.hashicorp.com/hc/en-us/categories/115001973588-Terraform | Known issues, workarounds |

---

## Tier 3 — Cloud Provider Documentation (for integration-specific behavior)

| Source | URL | Notes |
|---|---|---|
| AWS IAM Docs | https://docs.aws.amazon.com/iam/ | For OIDC, assume-role, permissions |
| AWS EC2 Docs | https://docs.aws.amazon.com/ec2/ | |
| Azure Resource Manager | https://learn.microsoft.com/en-us/azure/azure-resource-manager/ | |
| Azure Managed Identity | https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/ | |
| Azure DevOps Webhooks | https://learn.microsoft.com/en-us/azure/devops/service-hooks/services/webhooks | VCS trigger issues |
| GCP IAM | https://cloud.google.com/iam/docs | |
| GCP Workload Identity | https://cloud.google.com/iam/docs/workload-identity-federation | For OIDC with GCP |
| GitHub Webhooks | https://docs.github.com/en/webhooks | For VCS trigger issues |
| GitLab Webhooks | https://docs.gitlab.com/ee/user/project/integrations/webhooks.html | |

---

## Internal Sources (session only — not persisted in case outputs)

| Source | Path | Notes |
|---|---|---|
| Registry routing process | `memory/ops/registry-routing.md` | Interim — verify currency before use |
| Escalation paths | `memory/ops/escalation-paths.md` | To be created in Phase 3 |
| Entitlement checks | `memory/ops/entitlement-checks.md` | To be created in Phase 3 |

> Internal sources are loaded for the current session only. They are never included in customer-visible outputs.

---

## Source Usage Rules

1. **Always use versioned or version-specific URLs** when the behavior depends on a version.
2. **Never mix findings from different versions** without explicit version labelling.
3. **Status page is for current incidents only** — not historical failure causes.
4. **GitHub issues require a confirmed fix version** from release notes to be cited as resolved.
5. **Unconfirmed GitHub comments are not authoritative** — label as `community / unconfirmed`.
6. **Internal sources are session-only** — never persist or reference in customer outputs.
7. **Record retrieval date** for all findings — sources can change.
