# memory/patterns/

Sanitized issue patterns. Each file is one pattern entry.

**Naming**: `<category>-<short-description>.md`  
**Example**: `vcs-azdevops-webhook-missed-events.md`

## Schema (YAML front matter + prose section)

```yaml
---
pattern_alias: <slug>
schema_version: 1
category: <authentication|webhook|run_lifecycle|provider|state|registry|vcs|networking|policy|agent>
sub_category: <optional>
affected_products:
  - hcp_terraform | terraform_enterprise | terraform_core | provider_<name>
affected_versions: "<semver range or 'all'>"
confidence: candidate   # candidate | validated | outdated | rejected
last_reviewed: "YYYY-MM-DD"
superseded_by: null     # or pattern_alias of newer entry
source_refs:
  - title: "<source title>"
    url: "<full URL>"
    retrieved: "YYYY-MM-DD"
    version_applicability: "<version or range>"
    publication_status: released | beta | open_issue | community
    visibility: public | internal_session_only
---
```

## Empty — patterns are added by the Memory Curator after confirmed resolutions, with human approval.
