# claude-weave specs

Detailed specs behind [`../DESIGN.md`](../DESIGN.md). Each is self-contained; `DESIGN.md` stays the high-level map.

| # | Spec | Status |
|---|---|---|
| 01 | [Data model](01-data-model.md) — sidecar state + Weave-call mapping | draft |
| 02 | [Harness profiles](02-harness-profiles.md) — harness-agnostic event/field/registration mapping | draft |
| 03 | Wire protocol — hook↔sidecar socket, framing, spool fallback | todo |
| 04 | Sidecar lifecycle — spawn, singleton, idle shutdown, crash recovery | todo |
| 05 | Hook dispatcher — event routing, exit-0, detach, timeout | todo |
| 06 | Correlation — `tool_use_id` resolution + fallbacks | todo |
| 07 | [Weave mapping](07-weave-mapping.md) — what we send: call_start/end per span | draft |
| 08 | Config — `config.toml`/env, active harness, redaction, sampling, WAL | todo |
| 09 | Integration & packaging — plugin manifest, installer | todo |
| 10 | OTLP-direct fallback (daemonless) | todo |

Convention: specs describe *intended* behavior. Anything unverified against a harness / Weave runtime is marked **OPEN** and resolved by M0 capture or a spike.
