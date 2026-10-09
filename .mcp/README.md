# MCP integration registry (future)

No MCP server is configured or started by the repository foundation. A future registry should name each server, provenance, version, transport, authenticated identity, allowed tools/resources, data destinations, timeout, and approval class. Secrets belong in the destination credential store, never in this directory or portable exports.

An MCP connection exposes tools to a host; it does not by itself enforce STF policy. Side-effecting tools must be mediated by the harness and tested in every host adapter. The installer must preserve existing host settings and show the exact proposed config change before activation.
