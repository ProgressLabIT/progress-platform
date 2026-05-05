| Env var | Type | Default | Notes |
|---------|------|---------|-------|
| `PROGRESS_ARANGO_URL` | `str` | `'http://localhost:8529'` |  |
| `PROGRESS_API_ROOT_PATH` | `str` | `'/api'` |  |
| `PROGRESS_MEDIA_PATH` | `str` | `'/media'` |  |
| `PROGRESS_DB_NAME` | `str` | `'PROGRESS_TEST'` |  |
| `PROGRESS_WEBAPP_URL` | `str` | `'http://localhost:9000'` |  |
| `PROGRESS_API_DB_USERNAME` | `str` | `'root'` |  |
| `PROGRESS_API_DB_PWD` | `str` | `_(empty)_` | **Provided as Docker secret** |
| `PROGRESS_JWT_SECRET` | `str` | `_(empty)_` | **Provided as Docker secret** |
| `PROGRESS_CORS_ALLOWED_ORIGINS` | `list[str]` | `['*']` |  |
| `PROGRESS_NATS_URL` | `str` | `'nats://broker:4222'` |  |

### Docker secrets

These values are provided via Docker secrets (mounted under `/run/secrets/`) and are read directly from those files at startup:

- `progress_api_db_pwd`
- `progress_admin_pwd`
- `progress_jwt_secret`
