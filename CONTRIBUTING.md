# Contributing to Progress Platform

Progress Platform's canonical home is GitLab at `https://gitlab.com/progresslab/progress-platform`. **GitHub is a read-only mirror** maintained for discoverability.

We accept contributions through:

1. **GitHub Issues** — bug reports and feature requests. Maintainers triage and may file the corresponding work item on internal GitLab.
2. **GitHub Discussions** — questions and design conversations.
3. **Patches** — please open an issue first; for code contributions, attach a patch to the issue. Direct PRs against the mirror cannot be merged here and will be closed with a pointer to the issue flow.

We expect to revisit this flow once contribution velocity warrants a full GitLab→GitHub migration.

## Mirror update flow (for maintainers)

The GitLab → GitHub push-mirror runs automatically every 5 minutes. To force-push immediately:

1. Open GitLab: **Settings → Repository → Mirroring repositories**
2. Click the **Update now** button (half-circle arrows icon) next to the GitHub mirror entry.

To verify mirror sync, run from any machine:

```bash
git ls-remote https://gitlab.com/progresslab/progress-platform DEV
git ls-remote https://github.com/ProgressLabIT/progress-platform DEV
```

Both must resolve to the same SHA.
