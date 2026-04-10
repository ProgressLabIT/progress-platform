# Webapp Cache Strategy

The `app` and `warehouse` services are SPAs served by nginx. To avoid users getting stuck on stale frontend bundles after a deployment, caching is split by file type:

- **`/assets/*`** (hashed bundle files): `Cache-Control: public, immutable`, long TTL.
- **`/index.html`** (SPA entrypoint): `Cache-Control: no-cache, no-store, must-revalidate`.
- **`/config.js`** (runtime config mounted from host): `Cache-Control: no-cache, no-store, must-revalidate`.

Why: `index.html` decides which hashed bundles are loaded. If it is cached, clients can keep requesting old bundle names after a rollout. Keeping only `index.html` and `config.js` non-cacheable guarantees clients pick up new releases without manual cache clearing, while still allowing aggressive caching of immutable assets.
