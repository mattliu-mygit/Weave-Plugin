# Friendly README and First Release Design

## Goal

Make the repository immediately usable by both package consumers and source
contributors, then publish the existing `0.1.0` package as its first PyPI
release.

## Audience and outcomes

The README serves two primary audiences:

- a user who wants to install the adapter and see a coding-agent turn in Weave;
- a contributor who wants to clone the repository, run the suite, and modify it.

A new user should be able to identify prerequisites, choose a published or
source installation, authenticate, configure one project, register one harness,
verify a trace, diagnose common setup failures, and uninstall without reading
the implementation.

## README structure

Keep the existing product explanation and span example, then organize the rest
of the README in task order:

1. prerequisites;
2. quickstart with PyPI and source installation alternatives;
3. W&B authentication and one canonical `entity/project` configuration;
4. harness registration and the Codex trust step;
5. verification and troubleshooting;
6. supported-harness differences;
7. runtime, configuration, extension, design, and contributor details.

The PyPI path is the normal consumer path. Until the first release is visible,
the README must explicitly say that the source path works immediately. The
source path must create and activate a virtual environment before installation.
The README must not require a new CLI command or dependency.

## Observable setup contract

- Python 3.10 or newer, a W&B account, and one supported harness are explicit
  prerequisites.
- Authentication supports `wandb login` and the existing `WANDB_API_KEY`
  environment variable.
- Configuration consistently uses `project = "my-entity/my-project"` in the
  README; the separate `entity` field remains a supported advanced form.
- Hook registration presents Claude Code, Codex, and Gemini CLI as explicit
  alternatives.
- Codex trust guidance distinguishes surfaces that expose `/hooks` and points
  users to the generated `~/.codex/hooks.json` when that command is unavailable.
- Verification asks the user to complete one normal harness turn and check the
  configured Weave project. Troubleshooting names the metadata-only diagnostic
  log and the user-local socket without claiming that either is permanent.
- Uninstall examples are valid shell commands, not documentation notation such
  as optional arguments in square brackets.

## Release design

The first release remains version `0.1.0`, which is already authoritative in
`pyproject.toml`. Build a fresh source distribution and wheel from the release
commit and confirm that the wheel contains all three harness profiles. Run the
full test suite before creating the tag.

The existing GitHub Actions workflow publishes tags matching `v*` through PyPI
trusted publishing. Push the README commit to `main`, create and push the
annotated `v0.1.0` tag from that exact commit, monitor the publish workflow, and
verify the PyPI JSON endpoint reports `0.1.0`. Do not create a later version
until the first release exists.

## Repository isolation and cleanup

The active checkout contains unrelated trace-role changes. Perform the README
and release work from a clean worktree based on current `origin/main`; do not
stage, commit, rewrite, or stash those existing changes.

This document and its implementation plan are temporary workflow artifacts.
Before the final release commit, ensure lasting guidance lives in `README.md`,
delete the temporary files, and verify the final tree contains no superseded or
duplicated setup documentation.

## Verification

- Review every README command against the CLI and package metadata.
- Check every relative README link resolves.
- Run the full pytest suite outside restrictions that prevent Unix-socket tests.
- Build both distribution formats and inspect the wheel profile inventory.
- Confirm the release commit is on `main` and the tag points to it.
- Confirm the GitHub publish job succeeds and PyPI serves version `0.1.0`.
