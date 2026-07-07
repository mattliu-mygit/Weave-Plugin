# Spec 07 — What we send to Weave

Each span (spec 01, layer C) becomes **two requests**: a `call_start` at open and a `call_end` at close. In the sidecar these go through the SDK (`create_call` / `finish_call`); the OTLP fallback sends the equivalent OTEL span. All `inputs`/`output` pass through redaction (spec 08) first.

## Common call shape

`call_start`:
```json
{
  "project_id": "<entity>/<project>",
  "id":        "<span call id>",
  "trace_id":  "<session trace id>",
  "parent_id": "<parent call id | null for session>",
  "op_name":   "claude_code.<kind>",
  "started_at":"<ISO8601>",
  "attributes":{ "claude_code": { ...static metadata... } },
  "inputs":    { ...span-specific... }
}
```
`call_end`:
```json
{
  "id":       "<span call id>",
  "ended_at": "<ISO8601>",
  "output":   { ...span-specific | null... },
  "exception":"<str | null>",                 // set only on tool_error
  "summary":  { "claude_code": { ...computed... } }
}
```

- `attributes` = static facts known at open; `summary` = computed at close (status, duration, decision).
- `started_at`/`ended_at` come from the hooks' `captured_at`, not sidecar time.

## Per-span payloads

| op_name | inputs | output | key attributes / summary |
|---|---|---|---|
| `claude_code.session` | `{session_id}` | `{turn_count, status}` | attr: `permission_mode, model, cwd` |
| `claude_code.turn` | — | `{status, tool_count, had_steering}` | attr: `index` |
| `claude_code.input` | `{prompt}` (redacted) | — | attr: `kind=input` |
| `claude_code.tool.<name>` | `{tool_name, tool_input}` (redacted) | `{...tool_output}` (redacted) or none | summary: `status, duration_s, permission_decision, permission_source` |
| `claude_code.permission` | `{tool_name}` | `{reason}` if denied | summary: `decision, source, prompt_shown` |
| `claude_code.steering` | `{text}` or `{input_diff}` | — | attr: `steering_kind, related_tool` |
| `claude_code.stop` | — | — | attr: `kind=stop` |

## Example: an approved Bash tool call

`call_start`:
```json
{
  "project_id": "your-entity/claude-code",
  "id": "c-9f2…", "trace_id": "t-3ab…", "parent_id": "c-turn1…",
  "op_name": "claude_code.tool.Bash",
  "started_at": "2026-07-07T19:00:00.000Z",
  "attributes": { "claude_code": { "kind": "tool", "tool_name": "Bash", "session_id": "cafe12…" } },
  "inputs": { "tool_name": "Bash", "tool_input": { "command": "grep -n login auth.py" } }
}
```
`call_end`:
```json
{
  "id": "c-9f2…",
  "ended_at": "2026-07-07T19:00:00.400Z",
  "output": { "stdout": "12: def login(", "exit_code": 0 },
  "exception": null,
  "summary": { "claude_code": { "status": "ok", "permission_decision": "allow", "permission_source": "auto", "duration_s": 0.4 } }
}
```

## Example: a rejected Edit + its permission child

Tool `call_end` (no output; not an exception — a decision):
```json
{ "id": "c-ed1…", "ended_at": "2026-07-07T19:00:01.100Z", "output": null, "exception": null,
  "summary": { "claude_code": { "status": "rejected", "permission_decision": "deny", "permission_source": "user", "duration_s": 1.1 } } }
```
Permission `call_end`:
```json
{ "id": "c-perm1…", "ended_at": "2026-07-07T19:00:01.100Z",
  "output": { "reason": "use the logger, not print" },
  "summary": { "claude_code": { "decision": "deny", "source": "user", "prompt_shown": true } } }
```

## Notes

- **Redaction** (spec 08): `tool_input`, `tool_output`, and `prompt` are scrubbed before appearing in `inputs`/`output`.
- **Timing rule** (spec 01): long-open spans (session, turn) may `call_start` early so the UI shows them live; short spans emit start+end together at close.
- **OPEN:** exact `tool_output` shape per tool (Bash vs Edit vs Read …) and whether a tool-call id is present — confirmed by M0 capture.
- **OTLP fallback:** same data as an OTEL span — `op_name`→span name, `attributes`+`summary`→span attributes, `started_at`/`ended_at`→span times, `exception`→span status, `parent_id`→parent span.
