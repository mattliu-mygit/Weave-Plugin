"""Installer: settings.json merge/idempotency and plugin generation."""
from __future__ import annotations

import json
import os

from weave_agent_adapter.install import install, uninstall, write_plugin


def _read(p):
    with open(p) as f:
        return json.load(f)


def test_install_wires_all_events(tmp_path):
    path = str(tmp_path / "settings.json")
    install("claude-code", path=path)
    hooks = _read(path)["hooks"]
    for ev in ("SessionStart", "PreToolUse", "SubagentStop", "PreCompact", "SessionEnd"):
        assert ev in hooks
        cmd = hooks[ev][0]["hooks"][0]["command"]
        assert cmd.endswith(f"--event {ev}")


def test_install_is_idempotent(tmp_path):
    path = str(tmp_path / "settings.json")
    install("claude-code", path=path)
    install("claude-code", path=path)                 # twice
    hooks = _read(path)["hooks"]
    assert len(hooks["PreToolUse"]) == 1               # not duplicated


def test_install_preserves_foreign_hooks(tmp_path):
    path = str(tmp_path / "settings.json")
    with open(path, "w") as f:
        json.dump({"hooks": {"PreToolUse": [
            {"hooks": [{"type": "command", "command": "someone-elses-hook"}]}]}}, f)
    install("claude-code", path=path)
    cmds = [h["command"] for e in _read(path)["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert "someone-elses-hook" in cmds                # foreign entry kept
    assert any("weave-agent-adapter" in c for c in cmds)


def test_uninstall_removes_only_ours(tmp_path):
    path = str(tmp_path / "settings.json")
    with open(path, "w") as f:
        json.dump({"hooks": {"PreToolUse": [
            {"hooks": [{"type": "command", "command": "someone-elses-hook"}]}]}}, f)
    install("claude-code", path=path)
    uninstall("claude-code", path=path)
    hooks = _read(path).get("hooks", {})
    cmds = [h["command"] for e in hooks.get("PreToolUse", []) for h in e["hooks"]]
    assert cmds == ["someone-elses-hook"]


def test_install_resolves_target_from_profile_no_code(tmp_path):
    # a brand-new harness installs with only a profile: the registration names
    # its own target path, so no installer code (no target map) is touched.
    prof_dir = tmp_path / "profiles"
    prof_dir.mkdir()
    target = tmp_path / "myh-hooks.json"
    (prof_dir / "myh.toml").write_text(
        '[harness]\nname = "myh"\nadapter = "command-hook"\n'
        '[events]\nSessionStart = "session_start"\nPreToolUse = "tool_pre"\n'
        "[registration]\n"
        f'user_path = "{target}"\n'
        'local_path = ".myh/hooks.json"\n'
        'command = "weave-agent-adapter hook --harness myh"\n'
        'events = ["SessionStart", "PreToolUse"]\n'
    )
    p = install("myh", user=True, profiles_dir=str(prof_dir))   # no explicit path
    assert p == str(target)
    hooks = _read(str(target))["hooks"]
    assert set(hooks) == {"SessionStart", "PreToolUse"}


def test_write_plugin_emits_manifest_and_hooks(tmp_path):
    dest = str(tmp_path / "plugin")
    write_plugin("claude-code", dest)
    manifest = _read(os.path.join(dest, ".claude-plugin", "plugin.json"))
    assert manifest["name"] == "weave-agent-adapter"
    hooks = _read(os.path.join(dest, "hooks", "hooks.json"))["hooks"]
    assert "SessionStart" in hooks and "PreCompact" in hooks
