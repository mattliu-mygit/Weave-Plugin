# Weave agent spans design

## Goal

Emit every finalized coding-agent turn through Weave's supported agent-span
API so it appears in the Agents conversations and spans views and is eligible
for Signals. A successfully accepted generic OTLP trace is not sufficient.

The adapter remains a best-effort observer. It must not delay or break the
agent harness, and reducer handoff remains one-shot.

## Product behavior

- One finalized user-to-agent turn becomes one Weave `Turn` span.
- Turns from the same harness conversation share a stable conversation ID.
- Observed model calls become `LLM` spans, tools become `Tool` spans, and
  delegated agents become `SubAgent` spans.
- Prompts, steering messages, assistant replies, reasoning, tool calls, tool
  results, usage, timestamps, and relevant operational metadata are retained
  when the harness exposes them.
- Existing adapter redaction runs before values reach Weave.
- Export or initialization failure is diagnosed locally and never retained for
  a reducer retry.

## Architecture

The event reducer and its harness profiles remain the authoritative source for
turn boundaries, correlation, timing, redaction, and finalization. The export
boundary changes from a handwritten OTLP tree to a single SDK-backed emitter.

The emitter lazily imports `weave`, initializes the resolved `entity/project`,
maps the finalized domain turn to public `weave.conversation` types, and calls
`weave.log_turn` once. The sidecar is synchronous, so switching projects is
serialized; Weave owns flushing before rerouting its exporter.

`weave.log_turn` is the only production export path. The handwritten OTLP
endpoint, authentication, provider cache, recursive span walker, and direct
OpenTelemetry dependencies are removed.

## Span mapping

### Turn

The root call supplies:

- `conversation_id`: stable thread ID, falling back to the harness session ID.
- `agent_name`: harness name.
- `model`: the last observed model for the turn, when available.
- `messages`: initial user prompt, mid-turn steering messages in order, and the
  final assistant response.
- `started_at` and `ended_at`: hook-captured turn bounds.
- custom attributes: integration name, harness session ID, incomplete state,
  steering/denial/tool-error/compaction counts, configuration version, branch,
  and effort level when known.

### LLM

Each observed model call supplies model, provider, input/output messages when
available, output text, reasoning, finish reason, response model, token usage
including cache and reasoning tokens, and transcript-derived timestamps.

Claude transcript enrichment additionally retains `thinking` blocks as
reasoning and `tool_use` blocks as typed tool-call message parts. Provider is
`anthropic`. Codex-derived model calls use provider `openai` when available.

### Tool

Each tool supplies name, call ID, redacted arguments and result/error, and
captured timestamps. Permission decision/reason and adapter terminal status
remain filterable custom turn metadata and are also preserved in the tool
result when relevant.

### Subagent

Each delegated agent supplies its type as the name, stable observed agent ID,
captured timestamps, and any final output the SDK type can represent without
using private attributes.

The current public batch API accepts a flat list of child spans. Tools observed
inside a subagent therefore remain typed `Tool` spans in the same turn trace
but are siblings of the `SubAgent` span. We do not replay completed work through
the live context-manager API or depend on private SDK internals merely to
preserve nesting.

## Reference integration findings

The official Claude Code and Codex integrations confirm these useful fields:

- GenAI structured input/output messages rather than legacy numbered fields.
- Per-call model, provider, finish reason, token usage, cache usage, reasoning,
  and tool-call message parts.
- Tool type/call ID/arguments/result and error information.
- Stable conversation ID on all agent activity.
- Agent name/version, integration identity, accurate historical timestamps,
  permission information, and compaction metadata.

This change adopts fields already available from our hooks and Claude
transcript enrichment. It does not copy the plugins' detached workers,
per-session cursors, retry queues, or a second Codex rollout collector. Those
solve different delivery problems and would violate the adapter's one-shot
sidecar contract.

References:

- <https://docs.wandb.ai/weave/guides/tracking/trace-agents-batch>
- <https://docs.wandb.ai/weave/custom-agents-quickstart>
- <https://docs.wandb.ai/weave/guides/integrations/agents/claude-code-harness>
- <https://docs.wandb.ai/weave/guides/integrations/agents/codex-harness>

## Runtime and dependencies

- Require Python 3.10 or newer.
- The sidecar extra depends on `weave>=0.53.1`.
- Direct `wandb`, `opentelemetry-sdk`, and OTLP exporter declarations are
  removed because Weave owns authentication, routing, span typing, and export.
- Hook commands remain standard-library-only until they launch the sidecar.

## Failure behavior

Initialization and `log_turn` exceptions are caught at the emitter boundary,
diagnosed, and reported as a failed one-shot handoff. A later turn may still be
attempted. Shutdown requests a bounded OpenTelemetry provider flush when the
provider supports it.

## Testing and acceptance

Tests inject fake `weave.init` and `weave.log_turn` boundaries and assert the
actual public SDK objects and arguments:

- a turn is grouped by the intended conversation ID;
- messages include user, steering, and assistant content in order;
- LLM, Tool, and SubAgent objects carry available content, usage, and timing;
- redacted values never reach the SDK call;
- project changes initialize the correct project without redundant re-init;
- one failed SDK call does not block the next turn;
- no production path references the generic OTLP endpoint.

Focused tests cover the mapper and enrichers. The final gate runs the full
suite, builds the wheel and source distribution, inspects package contents,
checks documentation links, and removes this temporary design and its
implementation plan after their durable decisions are consolidated into the
canonical specifications.
