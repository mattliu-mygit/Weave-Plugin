# Spec 02: Harness profiles & adapters (harness-agnostic core)

The core is surface-agnostic: canonical actions → tracer → Weave. A harness plugs in through two pieces, an **adapter** (its hook mechanism) and a declarative **profile** (its event/field mapping). Assumption: the harness has a hook, or hook-like, system we can attach to.

## 1. Contract: canonical actions

Every harness maps its native events into this fixed vocabulary; it never changes per harness:

| Canonical action | Meaning |
|---|---|
| `session_start` / `session_end` | session begins / ends |
| `turn_start` / `turn_end` | user input begins / assistant finishes a turn |
| `tool_pre` / `tool_post` / `tool_error` | before / after-ok / after-failed tool run |
| `permission_request` / `permission_denied` | approval prompt shown / user denied |

**Derived, not hooks:** steering (mid-turn input, denial-with-feedback, input rewrite) and approval (a tool that ran was allowed). **Graceful degradation:** a harness that lacks an action simply never emits it, that span type is absent, the rest of the tree is intact. No harness must support all nine.

## 2. Adapters: one per hook *mechanism* (reused across harnesses)

Most hook systems share one shape: *run a command on an event, hand it the event payload as JSON on stdin.* One adapter covers the whole family:

- **`command-hook`** (default), our `weave-agent-adapter hook` dispatcher (spec 03) *is* this adapter. It works for any harness whose hooks invoke a command and pass the payload as JSON on stdin (Claude Code and Codex both do).
- Exotic mechanisms (payload as argv/env/file, in-process plugin callback, HTTP webhook) would get their own small adapter. None are implemented; stdin JSON is the only mode today, and the common one, so it is assumed rather than configured.

A command-hook harness needs **no new code**, just a profile.

## 3. Profile: declarative, per harness (usually the only thing you write)

```toml
[harness]
name    = "claude-code"
adapter = "command-hook"          # runs a command per event, payload as JSON on stdin

[events]                          # native event -> canonical action
SessionStart       = "session_start"
UserPromptSubmit   = "turn_start"
PreToolUse         = "tool_pre"
PostToolUse        = "tool_post"
PostToolUseFailure = "tool_error"
PermissionRequest  = "permission_request"
PermissionDenied   = "permission_denied"
Stop               = "turn_end"
SessionEnd         = "session_end"

[fields]                          # canonical field -> dotted path in payload
session_id  = "session_id"
tool_name   = "tool_name"
tool_input  = "tool_input"
tool_output = "tool_response"
tool_use_id = "tool_use_id"       # OPEN, confirm exists via M0 capture
transcript  = "transcript_path"
permission_mode = "permission_mode"
cwd         = "cwd"

[registration]                    # how the installer wires the harness's hook config
user_path  = "~/.claude/settings.json"     # install (default scope)
local_path = ".claude/settings.json"       # install --local
command    = "weave-agent-adapter hook --harness claude-code"  # installer appends --event <event>
events  = ["SessionStart","UserPromptSubmit","PreToolUse","PostToolUse",
           "PostToolUseFailure","PermissionRequest","PermissionDenied","Stop","SessionEnd"]
```

### Canonical fields

`session_id`, `tool_name`, `tool_input`, `tool_output`, `tool_use_id`, `transcript`, `permission_mode`, `cwd`. (The event isn't a field, it arrives via the adapter's `--event`.)

## How it's used

- **Hook stays dumb** (spec 03): forwards the raw payload; `--harness`/`--event` come from launch args.
- **Sidecar** loads the profile, maps native event → canonical action, resolves fields via `[fields]` paths.
- **Installer** merges `<command> --event <event>` per event into the file named by `[registration].user_path` (or `local_path` with `--local`), preserving other keys. No installer code per harness.

## Adding a harness

1. **Command-hook mechanism** → write a profile (events, fields, registration). No code.
2. **New delivery mechanism** (payload not on stdin as JSON) → add one adapter, then profiles reuse it.

## Open

- Each new harness's hook surface (event names, payload schema, hook-file location), confirm per harness via a capture spike. Claude Code's field paths are provisional until M0.
- Whether any GPT-based harness delivers payloads off-stdin (`argv`/`env`/a `notify`-program path), which would need a second adapter.
