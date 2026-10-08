# Portable contract schemas

These JSON Schemas are draft repository contracts, not proof of a working harness. They use JSON Schema 2020-12 and `schema_version: 1` so a future importer can reject unknown versions. `bundle.schema.json` describes a portable release; `agent.schema.json` a role request; `task.schema.json` a task; `result.schema.json` a structured outcome; and `trace-event.schema.json` a correlated observed event.

Identifiers and capability names are data. No schema grant authorizes a tool by itself. The future harness computes effective permissions from host restrictions, administrator policy, exact task approval, and these requests. When changing a schema, update the importer, adapters, conformance cases, and migration notes together.
