# Training Team — Template Scaffold

> **Runtime code lives in the submodule**, not here.

This directory is a placeholder so `TEAM_TEMPLATES['training']` in
`agents/orchestrator/orchestrator.py` resolves to a real path, but
project spinup should generally not include training-team —
training is a global, cross-project knowledge service, not a
per-project asset.

The real training-team runtime is at:

- `teams/training-team/` — git submodule at `github.com/mfelkey/training-team`

Per LL-040: `templates/` is reference/scaffolding only, never runtime.
The `invoke_team_flow()` dispatcher always resolves training-team to
`teams/training-team/`, never to this directory.

If a project genuinely needs its own scoped training curators in the
future, populate this scaffold by copying from the submodule and
parameterising with `PROJ-TEMPLATE` and `PROJECT_NAME_PLACEHOLDER`
tokens, matching the other `templates/*-team/` structures.
