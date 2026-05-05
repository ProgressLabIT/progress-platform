# Progress Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-progresslabit.github.io-blue)](https://progresslabit.github.io/progress-platform/)
[![GitHub release](https://img.shields.io/github/v/release/ProgressLabIT/progress-platform)](https://github.com/ProgressLabIT/progress-platform/releases)
[![Discussions](https://img.shields.io/github/discussions/ProgressLabIT/progress-platform)](https://github.com/ProgressLabIT/progress-platform/discussions)

> **Manufacturing Operations Management** for discrete manufacturing — event-sourced, on-premise, single-tenant.
> Production tracking, inventory, traceability, quality. FastAPI + ArangoDB + Vue 3 + NATS.

> ⚠️ **This is a read-only mirror.** Canonical: [GitLab](https://gitlab.com/progresslab/progress-platform). See [CONTRIBUTING.md](CONTRIBUTING.md).

<!-- Recording slot: replace the image below with an asciinema player or SVG after May 14 rehearsal.
     Cast file committed to docs/public/recordings/install.cast (D-07/D-11).
     Example embed: [![asciicast](https://asciinema.org/a/<ID>.svg)](https://asciinema.org/a/<ID>)
     Or local VitePress player via vite-plugin-asciinema (if wired in docs/).
     Until the cast is recorded, this image slot is intentionally left as a placeholder. -->
![Install demo — recorded May 14, 2026](docs/public/recordings/install-preview.png)

## Try it in 5 minutes

> Requires Docker and Docker Compose v2. Tested on Ubuntu 24.04 and macOS 14.

<!-- GSD:5min-lock-start — re-lock this block from May 14 fresh-VM rehearsal (LAUNCH-CHECKLIST.md §4) -->
```bash
curl -fsSL https://progresslabit.github.io/progress-platform/install.sh | sh
progress init
progress restore --demo sparkplug
progress tap
# open http://progress.localhost
```
<!-- GSD:5min-lock-end -->

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
