---
title: progress {command}
description: progress {command} reference — Progress Platform.
cli_validated: {true|false}   # remove `cli_validated: false` and Coming-soon callout when cli/{command}.py ships
---

<!-- Pattern 1 template — copy structure into docs/cli/{command}.md.
     Do NOT modify this template; do NOT publish it to the site. -->

# `progress {command}`

> One-paragraph what-it-does (business intent, not implementation).
> Ground every claim in cli/{command}.py source OR the locked sparkplug-demo
> ADR (0006 for init; S4-owned ADR or in-flight source for restore / tap).

<!-- If cli_validated: false, immediately follow with: -->
<!-- > 🚧 Coming soon — `progress {command}` is in active development; this -->
<!--   page will be promoted to validated content when the underlying source lands. -->

## When to use it

Bullet list of presenter / integrator scenarios. 2-4 bullets.

- When a fresh-VM operator needs ...
- When ...

## Usage

```bash
progress {command} [OPTIONS]
```

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--{flag}` | `TEXT` | `{default}` | Description copied verbatim from Typer help output. |

Source: `cli/{command}.py` (Typer-decorated function signature).
For absent commands, source the ADR option list verbatim.

## Example

```bash
$ progress {command} --{flag} value
{annotated output transcript}
```

Annotate non-obvious lines with `# {what this proves}` comments.

<!-- CLI-01 only — remove this section for restore / tap. -->
## How it maps to the Compose stack

| Step | Compose target | Volume / Secret |
|------|----------------|-----------------|
| {step} | `{service or compose file}` | `{volume or secret name}` |

## Related

- [Deployment basics](/admins/deployment) — what `progress init` provisions
- [Operations](/admins/operations) — `progress tap` as a diagnostic
- [ADR-0006](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0006-progress-init-ux.md) — Source of truth for `progress init` UX
