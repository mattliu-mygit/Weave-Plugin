# claude-weave specs

Detailed specs behind [`../DESIGN.md`](../DESIGN.md). Each is self-contained; `DESIGN.md` stays the high-level map.

| # | Spec | Status |
|---|---|---|
| 01 | [Data model](01-data-model.md) — sidecar state + Weave-call mapping | draft |
| 02 | Wire protocol — hook↔sidecar socket, framing, spool fallback | todo |
| 03 | Sidecar lifecycle — spawn, singleton, idle shutdown, crash recovery | todo |
| 04 | Hook dispatcher — event routing, exit-0, detach, timeout | todo |
| 05 | Correlation — `tool_use_id` resolution + fallbacks | todo |
| 06 | Weave mapping — op names, per-span attribute schema | todo |
| 07 | Config — `config.toml`/env, redaction, sampling, WAL | todo |
| 08 | Integration & packaging — plugin manifest, installer | todo |
| 09 | OTLP-direct fallback (daemonless) | todo |

Convention: specs describe *intended* behavior. Anything unverified against Claude Code / Weave runtime is marked **OPEN** and resolved by M0 capture or a spike.
