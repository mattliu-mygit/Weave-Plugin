"""RoutingSink: each trace goes to its stamped project; children route by trace."""
from __future__ import annotations

from weave_agent_adapter.core.model import WeaveCall
from weave_agent_adapter.sinks.recording import RecordingSink
from weave_agent_adapter.sinks.routing import RoutingSink


def _call(cid, trace, project=None, parent=None):
    return WeaveCall(id=cid, trace_id=trace, op_name="op", started_at=0.0,
                     parent_id=parent, project=project)


def test_routes_by_project_and_caches_by_trace():
    made = {}

    def make(project):
        made[project] = RecordingSink()
        return made[project]

    rs = RoutingSink(make, default_project="default")
    # trace A stamps project "repo-a" on its root; child has no project
    rs.start(_call("root-a", "A", project="repo-a"))
    rs.start(_call("child-a", "A"))               # routes by cached trace -> repo-a
    # trace B stamps "repo-b"
    rs.start(_call("root-b", "B", project="repo-b"))
    rs.end(_call("root-b", "B"))                  # end routes by trace too

    assert set(made) == {"repo-a", "repo-b"}      # one client per project, lazily
    a_ids = [c.id for k, c in made["repo-a"].events]
    assert a_ids == ["root-a", "child-a"]
    b_ids = [c.id for k, c in made["repo-b"].events]
    assert b_ids == ["root-b", "root-b"]


def test_unstamped_trace_uses_default():
    made = {}
    rs = RoutingSink(lambda p: made.setdefault(p, RecordingSink()), default_project="default")
    rs.start(_call("x", "T"))                     # never stamped
    assert list(made) == ["default"]
