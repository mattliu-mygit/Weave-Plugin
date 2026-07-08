"""Installer (spec 08): wire a harness's hooks from the profile's [registration].

Reads the active profile, emits one command per event, and merges them into the
settings file the profile names, idempotently (re-running replaces our entries;
`uninstall` removes only ours). Every harness's hook file uses the same
`{"hooks": {event: [entry]}}` shape, and the profile declares its own target
paths, so adding a harness needs no code here.
"""
from __future__ import annotations

import json
import os

from .profile import load_profile

MARKER = "weave-agent-adapter hook"      # identifies entries we own


def _target_path(reg: dict, user: bool) -> str:
    # the profile's [registration] names where its hooks live, per scope
    key = "user_path" if user else "local_path"
    p = reg.get(key)
    if not p:
        raise ValueError(f"profile [registration] is missing {key!r}")
    return os.path.expanduser(p) if user else os.path.join(os.getcwd(), p)


def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _is_ours(entry: dict) -> bool:
    return any(MARKER in h.get("command", "") for h in entry.get("hooks", []))


def _entry(command: str, ev: str) -> dict:
    return {"hooks": [{"type": "command", "command": f"{command} --event {ev}"}]}


def install(harness: str, user: bool = True, profiles_dir=None, path=None) -> str:
    reg = load_profile(harness, profiles_dir).registration
    command, events = reg["command"], reg.get("events", [])
    path = path or _target_path(reg, user)
    data = _read_json(path)
    hooks = data.setdefault("hooks", {})
    for ev in events:
        others = [e for e in hooks.get(ev, []) if not _is_ours(e)]
        others.append(_entry(command, ev))
        hooks[ev] = others
    _write_json(path, data)
    return path


def write_plugin(harness: str, dest: str, profiles_dir=None) -> str:
    """Emit a Claude Code plugin dir (manifest + hooks.json) for zero-config install.

    Same per-event commands as `install`, but packaged so a user adds the plugin
    once instead of editing settings.json, the hooks auto-register on load.
    """
    reg = load_profile(harness, profiles_dir).registration
    command, events = reg["command"], reg.get("events", [])
    manifest = {
        "name": "weave-agent-adapter",
        "description": "Trace agent-harness sessions to W&B Weave (session/turn/tool/permission).",
        "version": "0.1.0",
    }
    hooks = {ev: [_entry(command, ev)] for ev in events}
    _write_json(os.path.join(dest, ".claude-plugin", "plugin.json"), manifest)
    _write_json(os.path.join(dest, "hooks", "hooks.json"), {"hooks": hooks})
    return dest


def uninstall(harness: str, user: bool = True, profiles_dir=None, path=None) -> str:
    reg = load_profile(harness, profiles_dir).registration
    path = path or _target_path(reg, user)
    data = _read_json(path)
    hooks = data.get("hooks", {})
    for ev in list(hooks.keys()):
        hooks[ev] = [e for e in hooks[ev] if not _is_ours(e)]
        if not hooks[ev]:
            del hooks[ev]
    if hooks == {}:
        data.pop("hooks", None)
    _write_json(path, data)
    return path
