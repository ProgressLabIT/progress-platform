# Progress Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-progresslabit.github.io-blue)](https://progresslabit.github.io/progress-platform/)
[![GitHub release](https://img.shields.io/github/v/release/ProgressLabIT/progress-platform)](https://github.com/ProgressLabIT/progress-platform/releases)
[![Discussions](https://img.shields.io/github/discussions/ProgressLabIT/progress-platform)](https://github.com/ProgressLabIT/progress-platform/discussions)

> **Manufacturing Operations Management** for discrete manufacturing — event-sourced, on-premise, single-tenant.
> Production tracking, inventory, traceability, quality. FastAPI + ArangoDB + Vue 3 + NATS.

> ⚠️ **This is a read-only mirror.** Canonical: [GitLab](https://gitlab.com/progresslab/progress-platform). See [CONTRIBUTING.md](CONTRIBUTING.md).

<!-- Phase 4 deliverable: replace with asciinema/SVG of `progress init` (D-11) -->
![Demo placeholder — captured during May 14 fresh-VM rehearsal](https://via.placeholder.com/800x300?text=Demo+GIF+coming+soon)

## Try it in 5 minutes

> **Note:** the `progress` CLI is part of the Sparkplug demo bundle, in active development.
> Daily-locked surface as of 2026-04-29 (placeholder — coordinated with sparkplug-demo workstream;
> Phase 4 launch-prep does the final lock against the May 14 fresh-VM rehearsal):

```bash
# placeholder — coordinated with sparkplug-demo workstream
curl -fsSL https://progresslabit.github.io/progress-platform/install.sh | sh
progress init
progress restore --demo sparkplug
progress tap
# open http://progress.localhost
```

## Documentation

Full docs: **https://progresslabit.github.io/progress-platform/**

- API reference (every public endpoint, parameters, errors, emitted events)
- Events reference (50+ events; top 10 with sequence diagrams)
- CLI reference (`progress init`, `progress restore`, `progress tap`)
- User walkthroughs (production, inventory, counting, warehouse)
- Admin / integrator docs (deployment, configuration, NATS taxonomy)

## Architecture (1-paragraph)

Event-sourced backend (FastAPI + Pydantic v2) on ArangoDB (multi-model: documents + graph). Inter-service messaging via NATS JetStream. Frontends: Vue 3 + Quasar 2 (main desktop SPA + warehouse mobile app). Workflows on Prefect 3. Single-tenant, on-premise via Docker. See [ARCHITECTURE.md](ARCHITECTURE.md) for layer details.

## Contributing

GitHub is a read-only mirror — direct PRs cannot be merged. Open an issue or discussion. See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Found a vulnerability? Use [GitHub Private Vulnerability Reporting](https://github.com/ProgressLabIT/progress-platform/security/advisories/new). See [SECURITY.md](SECURITY.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
