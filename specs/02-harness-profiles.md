# Spec 02 — Harness profiles (harness-agnostic core)

The tracer's concepts — session, turn, tool call, permission — are generic to agent harnesses. Only the *surface* differs per harness: event names, payload field locations, and how hooks get registered. A **harness profile** is a declarative file capturing exactly that surface, so the core never hard-codes a specific harness.

**New harness = new profile, no code.**

---

## Canonical events

The core operates on these; profiles map a harness's native events onto them.

| Canonical | Meaning |
|---|---|
| `session_start` | session begins |
| `turn_start` | user input begins a turn (in-turn ⇒ steering) |
| `tool_pre` | before a tool runs |
| `tool_post` | tool finished ok |
| `tool_error` | tool failed |
| `permission_request` | approval prompt shown |
| `permission_denied` | user denied |
| `turn_end` | assistant finished the turn |
| `session_end` | session ends |

Unmapped native events are ignored (still captured in M0).

## Canonical fields

Pulled from the raw payload via the profile's paths:

`session_id`, `event_name`, `tool_name`, `tool_input`, `tool_output`, `tool_use_id`, `transcript`, `permission_mode`, `cwd`.

---

## Profile schema (TOML)

```toml
[harness]
name       = "claude-code"
transport  = "stdin-json"        # how the payload reaches the hook

[events]                         # native event -> canonical
SessionStart       = "session_start"
UserPromptSubmit   = "turn_start"
PreToolUse         = "tool_pre"
PostToolUse        = "tool_post"
PostToolUseFailure = "tool_error"
PermissionRequest  = "permission_request"
PermissionDenied   = "permission_denied"
Stop               = "turn_end"
SessionEnd         = "session_end"

[fields]                         # canonical -> dotted path in payload
session_id  = "session_id"
event_name  = "hook_event_name"
tool_name   = "tool_name"
tool_input  = "tool_input"
tool_output = "tool_response"
tool_use_id = "tool_use_id"      # OPEN — confirm exists via M0 capture
transcript  = "transcript_path"
permission_mode = "permission_mode"
cwd         = "cwd"

[registration]                   # how the installer wires hooks for this harness
kind    = "claude-code-settings" # target format
command = "claude-weave hook --harness claude-code"
events  = ["SessionStart","UserPromptSubmit","PreToolUse","PostToolUse",
           "PostToolUseFailure","PermissionRequest","PermissionDenied","Stop","SessionEnd"]
```

---

## How it's used

- **Active harness** chosen once in `config.toml` (`active_harness = "claude-code"`); profiles live in `profiles/<name>.toml`.
- **Hook stays dumb** (spec 01): it sends the raw payload plus a `--harness <name>` tag. No normalization in the hook.
- **Sidecar normalizes:** loads the profile, maps `event_name` → canonical event and resolves canonical fields via `[fields]` paths, producing the state transitions in spec 01. All harness-specific knowledge lives in the profile.
- **Installer** reads `[registration]` to wire hooks in the harness's own format — so "setup" is: pick a profile → installer does the rest.

## Open

- Field paths for Claude Code are provisional (esp. `tool_use_id`) → confirmed by M0 capture.
- Other harnesses: add a profile each once their event/payload surface is known. Registration `kind`s beyond `claude-code-settings` are defined as we add them.
