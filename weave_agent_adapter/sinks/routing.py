"""Route each trace to a per-project sink (spec 07: per-repo separation).

The session-root call carries `project`; every child call in that trace has
`project=None`, so we cache `trace_id -> project` from the root and look children
up by trace. Downstream sinks are made lazily, one per distinct project, and
share the process (so one warm client per project).
"""
from __future__ import annotations

from ..core.model import WeaveCall
from ..core.sink import Sink


class RoutingSink(Sink):
    def __init__(self, make_sink, default_project: str):
        self._make = make_sink                 # project -> Sink
        self._default = default_project
        self._sinks: dict = {}
        self._trace_project: dict = {}

    def _sink_for(self, wc: WeaveCall) -> Sink:
        if wc.project:
            self._trace_project[wc.trace_id] = wc.project
        project = self._trace_project.get(wc.trace_id, self._default)
        sink = self._sinks.get(project)
        if sink is None:
            sink = self._sinks[project] = self._make(project)
        return sink

    def start(self, wc: WeaveCall) -> None:
        self._sink_for(wc).start(wc)

    def end(self, wc: WeaveCall) -> None:
        self._sink_for(wc).end(wc)

    def flush(self) -> None:
        for sink in self._sinks.values():
            try:
                sink.flush()
            except Exception:
                pass
