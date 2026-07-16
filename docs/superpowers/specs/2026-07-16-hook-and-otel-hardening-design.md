# Hook and OTel Hardening Design

## Goal

Make the Codex and Claude Code hooks reliably produce accurate OpenTelemetry
turn traces in the configured Weave project, including the Conversations view,
while keeping hooks fast, passive, and operationally simple.

## Scope

This pass fixes the current best-effort architecture rather than adding a
durable delivery system. It covers:

- Weave conversation indexing and documented OTLP export configuration.
- Bounded hook execution and observable sidecar/export failures.
- Safe, deterministic hook installation for Codex and Claude Code.
- Secret redaction, event validation, and reducer correctness.
- Generated plugin, package metadata, tests, and canonical documentation.

It does not add an ingress spool, export outbox, collector, second tracing
plane, or Weave SDK call emission.

## Architecture

The adapter keeps one tracing path:

```text
harness command hook
  -> bounded local socket handoff
  -> sidecar normalization and reduction
  -> OpenTelemetry span tree
  -> standard OTLP/HTTP exporter
  -> Weave
```

The hook remains standard-library-only. It reads one JSON payload within a
hard time and size limit, adds the wire envelope, attempts a bounded socket
send, and exits zero without writing to stdout. If the sidecar is unavailable,
the hook starts it and retries only within a short total deadline. Failure is
recorded locally; it never blocks the harness for seconds and does not persist
raw event payloads.

The sidecar remains the only component that understands harness profiles,
redacts data, correlates events, maintains session state, and performs network
I/O. It validates the wire version before reduction. It may scale to zero only
when no turn, tool, subagent, or accepted-but-unflushed emission remains.

The emitter creates OTel spans with hook-captured timestamps and exports them
using `BatchSpanProcessor` to the documented Weave OTLP endpoint. Root turn
spans carry both the applicable GenAI semantic-convention attributes and the
Weave attributes required for conversation indexing: `wandb.thread_id`,
`wandb.is_turn`, `input.value`, and `output.value`. Resource attributes route
the spans to the configured W&B entity and project.

The Weave Python SDK call API is not part of this path. The installed W&B
package may still supply authentication and default-entity discovery.

## Observable Behavior

### Hook execution

- A complete payload already available on stdin is forwarded immediately.
- Partial input cannot keep the hook alive past its read deadline.
- Oversized or malformed input is rejected without forwarding a fabricated
  empty event.
- Socket connection, sidecar startup, and retry work have one short bounded
  deadline. Hooks always remain passive and exit zero.
- `WEAVE_AGENT_ADAPTER_DISABLE` accepts explicit boolean values; `0`, `false`,
  and `no` do not disable tracing.
- Failures are written without payload contents to a protected, bounded local
  diagnostic log.

### Installation

- User/local installation preserves foreign settings and hook entries.
- Invalid or unreadable JSON fails closed and is never overwritten.
- Writes use a same-directory temporary file followed by atomic replacement.
- Installed commands use the resolved adapter executable so GUI applications
  do not depend on an interactive-shell `PATH`.
- Profile event lists are authoritative for installed and generated hooks.
- The obsolete raw capture hook and repository-local capture configuration are
  removed.

### Trace correctness

- Permission denial closes the matching tool as rejected and contributes to
  the denial count.
- Events with a stable tool-call ID use it. Fallback matching considers the
  tool name and compatible input; ambiguous parallel calls are not attached to
  an arbitrary running tool.
- Tool failures retain redacted error information in the tool span.
- A root turn span encloses every child timestamp, including subagents that
  finish after the harness stop event.
- Unsupported wire versions are rejected and diagnosed.
- Sidecar idle shutdown does not finalize active work merely because the
  socket has been quiet.

### Export behavior

- The default endpoint is `https://trace.wandb.ai/otel/v1/traces` and remains
  configurable.
- Provider/authentication initialization failure leaves the turn eligible for
  a later in-process retry rather than marking it emitted.
- OTel batching and its normal exporter retries remain responsible for network
  delivery. This design intentionally provides best-effort, not guaranteed,
  delivery.
- Shutdown requests a bounded flush and records failure locally.

## Error Handling and Privacy

The primary harness must never fail because observability failed. Hook and
sidecar boundaries therefore convert failures into concise diagnostics and
continue or exit cleanly. They no longer discard errors without any evidence.

Diagnostics contain event type, harness, phase, and exception class, but never
the raw hook payload, prompts, tool arguments, outputs, credentials, or API
keys. Log files and runtime directories are user-only. Log size is bounded by
rotation.

Redaction happens before debug or network sinks. Sensitive dictionary keys are
redacted recursively, token-shaped strings are scrubbed, and complete
multiline PEM private-key blocks are replaced.

## Testing and Acceptance

Each behavior change starts with a focused failing regression test. The final
suite covers bounded partial stdin, startup deadline, explicit disable values,
malformed installer input, atomic writes, executable resolution, full PEM
redaction, wire-version rejection, denial state, ambiguous parallel tool
correlation, tool errors, late subagent timing, active-work shutdown, Weave
turn attributes, endpoint routing, initialization failure, and flush failure.

Integration tests execute every registered Codex and Claude Code event through
the real CLI and Unix socket into a sidecar with a recording emitter. Generated
plugin hooks must match their profile exactly.

Final live acceptance sends a uniquely named authenticated turn to
`weave-team/agent-sessions`, flushes the provider, and verifies that it appears
in Weave Conversations with the expected thread, input, output, and tool tree.
If live verification is blocked by authentication, network access, or UI
access, all local acceptance checks still run and the external gate is reported
explicitly rather than inferred as successful.

## Documentation and Cleanup

`README.md` and the canonical specifications will describe the implemented
best-effort OTel/OTLP path and its actual lifecycle guarantees. Superseded SDK
calls-plane and dead-letter claims will be removed or retained only as clearly
labelled history where they explain an architectural decision. Package version
metadata will have one authoritative value. Generated plugin files will be
regenerated, and obsolete capture code and temporary implementation planning
artifacts will be removed before completion.
