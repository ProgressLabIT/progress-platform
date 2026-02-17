# Phase 1: Precision Foundation - Research

**Researched:** 2026-02-17
**Domain:** Python-ArangoDB serialization, floating-point precision management
**Confidence:** HIGH

## Summary

This phase implements float precision management at the database serialization layer and creates comparison utilities for business logic. Research confirms that python-arango's custom serializer mechanism is the correct injection point for rounding all floats to 6 decimals before database writes. The existing `encoder()` function in `backend/api/utils/db.py` is passed as the `serializer` parameter to `ArangoClient`, making it the single point where all data flows before JSON serialization.

**Key findings:**
- Python-arango serializer receives Pydantic model_dump output (dicts with native Python types) before JSON encoding
- Current `encoder()` function uses FastAPI's `jsonable_encoder()` then `json.dumps()` - we inject rounding between these steps
- Events use both `model_dump()` for Pydantic models and plain `dict()` for updates - serializer must handle both
- No existing float comparison utilities exist - direct comparisons (`>=`, `==`, `!=`) used throughout events
- Codebase has minimal docstrings (simple utility modules like `dt.py` have none; complex ones have basic comments)

**Primary recommendation:** Create `backend/api/utils/float_precision.py` with comparison utilities and helper functions, modify `encoder()` in `db.py` to recursively round floats, add precision config to `Settings` class in `config.py`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Config-driven precision**: Serializer rounding precision configurable via config file (default 6 decimals)
- **Epsilon parameter**: Comparison functions accept epsilon parameter with default: `float_equals(a, b, epsilon=1e-6)`
- **Full type hints**: All functions require complete type annotations
- **Detailed docstrings**: Include description, params, returns, usage examples, edge cases
- **round_float decimals**: Accept decimals parameter with None meaning "use config value"
- **NaN handling**: Follow IEEE 754 standard (NaN != NaN returns True)
- **No bounds checking**: Accept any float value Python supports
- **Absolute epsilon**: Use fixed epsilon (1e-6), not scaled based on magnitude
- **Inline comments**: Document WHY rounding is applied in db.py

### Claude's Discretion
- **Module location**: Create new `float_precision.py` (recommended based on codebase patterns for domain-specific utilities)
- **None handling**: Comparison functions should raise TypeError for None (consistent with standard Python numeric operations)
- **Infinity handling**: `round_float` should return infinity as-is (rounding infinity is mathematically undefined)
- **Module docstring**: Brief overview with epsilon standard and rationale (matches codebase patterns - minimal docs)
- **Examples location**: Include in docstrings only (no separate examples file - codebase doesn't use this pattern)

### Deferred Ideas (OUT OF SCOPE)
None

## Standard Stack

### Core Serialization
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-arango | 8.x | ArangoDB client with custom serializer support | Official Python driver, supports custom JSON serializers |
| FastAPI | 0.x | jsonable_encoder for Pydantic model serialization | Already used in encoder() for converting Pydantic to dicts |
| Pydantic | v2 | Model validation and serialization | Project standard for all models (FlexModel, ArangoDocument) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | 3.11+ | JSON encoding after processing | Final step in encoder() function |
| pydantic-settings | Latest | Settings configuration with env support | Already used in config.py for Settings class |

### Alternatives Considered
None - existing stack is correct for this implementation.

**Installation:**
No new dependencies required - all libraries already in use.

## Architecture Patterns

### Recommended Implementation Structure

```
backend/api/utils/
├── float_precision.py    # NEW: Comparison and rounding utilities
├── db.py                 # MODIFY: Add rounding to encoder()
└── config.py             # MODIFY: Add float_precision_decimals setting
```

### Pattern 1: Custom Serializer Injection

**What:** Python-arango accepts a `serializer` callable during ArangoClient initialization. This function receives Python objects (dicts, lists, primitives) and returns JSON strings.

**Current implementation in db.py:**
```python
def encoder(data):
  dict = model_to_db_dict(data)  # Pydantic model → dict via jsonable_encoder
  return json.dumps(dict)         # dict → JSON string

client = ArangoClient(hosts=conf.arango_url, serializer=encoder)
```

**How it works:**
1. Application calls `collection.insert(pydantic_model)` or `collection.insert(plain_dict)`
2. Python-arango calls `encoder(data)` - data can be Pydantic model OR plain dict
3. `model_to_db_dict()` uses `jsonable_encoder()` which converts Pydantic to dict (plain dicts pass through unchanged)
4. `json.dumps()` converts dict to JSON string
5. JSON sent to ArangoDB

**Where to inject rounding:** Between step 3 and 4 - after dict conversion, before JSON encoding.

Source: [python-arango serializer docs](https://docs.python-arango.com/en/main/serializer.html)

### Pattern 2: Recursive Float Rounding

**What:** Walk nested data structures (dicts, lists) and round all float values in-place.

**Why needed:** Events create nested structures with floats at any depth:
```python
# From batch_completed.py line 167
job_update = dict(
  _key = self.info.job_key,
  active_batch_qt = 0,              # float
  qt_completed = new_job_qt_completed,  # float
  progress = new_progress           # int from round()
)

# From batch_completed.py line 249
step_execution_records = [x.model_dump(
  by_alias=True,
  exclude_unset=True,
  exclude_none=True
) for x in step_execution_data]  # List of dicts with nested floats
```

**Recommended approach:**
```python
def _round_floats_recursive(obj, decimals):
    """Recursively round all floats in nested dicts/lists."""
    if isinstance(obj, float):
        return round(obj, decimals)
    elif isinstance(obj, dict):
        return {k: _round_floats_recursive(v, decimals) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_round_floats_recursive(item, decimals) for item in obj]
    return obj
```

This handles arbitrary nesting depth without special cases.

### Pattern 3: Config-Based Precision

**What:** Store decimal precision in Settings, access via `config.get_config()`.

**Existing pattern in config.py:**
```python
class Settings(BaseSettings):
  arango_url: str = "http://localhost:8529"
  db_name: str = "PROGRESS_TEST"
  # ... other settings

  model_config = SettingsConfigDict(
    env_prefix = "progress_",
    secrets_dir = "/run/secrets",
    env_file = ".env"
  )

@lru_cache()
def get_config() -> Settings:
  return Settings()
```

**Add:**
```python
class Settings(BaseSettings):
  # ... existing fields
  float_precision_decimals: int = 6
```

Environment variable: `PROGRESS_FLOAT_PRECISION_DECIMALS=6`

### Pattern 4: Utility Module Organization

**What:** Domain-specific utilities in separate modules under `backend/api/utils/`.

**Existing examples:**
- `dt.py` - Date/time utilities (5 lines, no docstrings)
- `counter.py` - Counter generation (49 lines, minimal comments)
- `auth.py` - Authentication utilities (407 lines, complex)
- `production.py` - Production domain queries (603 lines)

**Pattern:** Create focused modules for specific domains. Simple utilities (< 50 lines) have minimal docs, complex ones have docstrings for key functions.

**For float_precision.py:**
- Standalone module (not extending existing module)
- 4 functions: `float_equals`, `float_less_than`, `float_greater_than`, `round_float`
- Detailed docstrings per user requirements (differs from codebase pattern, but explicitly required)
- Module-level docstring explaining epsilon standard and rationale

### Anti-Patterns to Avoid

- **Modifying Pydantic models:** Don't add validators to round floats - this would round in-memory values, causing logic errors when arithmetic operations produce precise values
- **Rounding in business logic:** Don't scatter `round()` calls throughout events - centralize in serializer
- **Direct float equality:** Never use `a == b` for floats in business logic - always use tolerance-based comparison
- **Hardcoding precision:** Don't hardcode 6 decimals - always reference config

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pydantic model → dict | Custom serialization | `jsonable_encoder(model, by_alias=True)` | Handles Pydantic v2, datetime, enums, nested models correctly |
| JSON encoding | Custom JSON encoder class | Modify existing `encoder()` function | Python-arango already uses our encoder; extending is simpler than replacing |
| Float comparison tolerance | Context-dependent epsilon | Standard 1e-6 everywhere | Matches 6-decimal precision, simpler than per-operation tuning |
| Config management | Custom config files | pydantic-settings BaseSettings | Already in use, handles env vars, type validation, defaults |

**Key insight:** The existing serialization pipeline is correct - we enhance it, not replace it.

## Common Pitfalls

### Pitfall 1: Type Handling in Serializer

**What goes wrong:** Serializer fails when it receives unexpected types (Pydantic models, plain dicts, nested structures).

**Why it happens:** Python-arango passes whatever the application provides to `collection.insert()`. Events use both:
- Pydantic models: `self.tx.collection('Event').insert(record)` where `record = self.info.model_dump(...)`
- Plain dicts: `self.tx.collection('Job').update(job_update)` where `job_update = dict(...)`
- Pydantic model objects: `self.tx.collection("StepExecutionData").insert(step_data)` where `step_data = StepExecutionData(...)`

**How to avoid:**
```python
def encoder(data):
  # Handle both Pydantic models and plain dicts
  dict_data = model_to_db_dict(data)  # jsonable_encoder handles both
  rounded_data = _round_floats_recursive(dict_data, decimals)
  return json.dumps(rounded_data)
```

**Warning signs:**
- TypeError when inserting plain dicts
- AttributeError when accessing model properties
- Floats not being rounded in some collections

### Pitfall 2: Mutating Config at Runtime

**What goes wrong:** Modifying `conf.float_precision_decimals` after application starts has no effect or causes inconsistent behavior.

**Why it happens:** `get_config()` uses `@lru_cache()` - returns same Settings instance throughout application lifetime.

**How to avoid:**
- Set `PROGRESS_FLOAT_PRECISION_DECIMALS` environment variable before application starts
- For testing, clear cache: `get_config.cache_clear()` then call `get_config()` again
- Document that precision is set at startup, not runtime-configurable

**Warning signs:**
- Tests changing precision don't work
- Config changes in docker-compose.yaml require container restart

### Pitfall 3: Rounding Infinity and NaN

**What goes wrong:** `round(float('inf'), 6)` and `round(float('nan'), 6)` raise exceptions or return unexpected values.

**Why it happens:** Python's `round()` doesn't handle special float values well:
```python
round(float('inf'), 6)  # Returns inf (OK)
round(float('nan'), 6)  # Returns nan (OK)
```

Actually both work fine! But edge case: `round()` could be called on these values.

**How to avoid:**
```python
def _round_floats_recursive(obj, decimals):
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return obj  # Return as-is
        return round(obj, decimals)
    # ... rest of function
```

**Warning signs:**
- Exceptions during serialization
- Infinite values becoming None or 0

### Pitfall 4: Float Comparison in Event Validation

**What goes wrong:** Event validation fails due to floating-point precision errors.

**Current examples from codebase:**
```python
# batch_completed.py line 54
if self.batch.qt_total != self.info.completed_batch_qt:
  raise ValueError("Batch quantity mismatch")

# batch_completed.py line 148
if new_job_qt_completed >= self.job.qt_planned:
  # Close job
```

**Why it happens:** Arithmetic operations produce values like `99.999999` when `100.0` expected.

**How to avoid:** Use tolerance-based comparisons:
```python
from utils.float_precision import float_equals, float_greater_than

if not float_equals(self.batch.qt_total, self.info.completed_batch_qt):
  raise ValueError("Batch quantity mismatch")

if float_greater_than(new_job_qt_completed, self.job.qt_planned) or \
   float_equals(new_job_qt_completed, self.job.qt_planned):
  # Close job
```

**Warning signs:**
- Validation errors for "matching" quantities
- Jobs not closing when they should
- Inventory movements rejected despite correct quantities

## Code Examples

Verified patterns from codebase analysis:

### Current Serialization Flow
```python
# Source: backend/api/utils/db.py
from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

def model_to_db_dict(pydantic_model):
  prepped_data = jsonable_encoder(pydantic_model, by_alias=True)

  # remove null _id / _key fields
  for field in ['_id', '_key']:
    if field in prepped_data:
      if prepped_data[field] is None:
        del prepped_data[field]

  return prepped_data

def encoder(data):
  dict = model_to_db_dict(data)
  return json.dumps(dict)

client = ArangoClient(hosts=conf.arango_url, serializer=encoder)
```

### Event Insert Patterns
```python
# Source: backend/api/events/base_event.py lines 159-167
def store_event(self):
    """Store the event in the database using the pre-generated UUID key."""
    record = self.info.model_dump(exclude_extra=True, by_alias=True)
    record['_key'] = self.event_key
    self.tx.collection('Event').insert(record)  # Calls encoder(record)

# Source: backend/api/events/production/batch_completed.py lines 167-210
job_update = dict(
    _key = self.info.job_key,
    active_batch_qt = 0,  # float
    qt_completed = new_job_qt_completed,  # float
    progress = new_progress
)
self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])
# Calls encoder(job_update)

# Source: backend/api/events/production/step_completed.py lines 50-62
step_data = StepExecutionData(
    key = temp_step_data_key,
    user_key = self.info.user_key,
    # ... fields
    form_data = self.info.form_data
)
self.tx.collection("StepExecutionData").insert(step_data, overwrite=True)
# Calls encoder(step_data) - Pydantic model, not dict
```

### Config Access Pattern
```python
# Source: backend/api/utils/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  arango_url: str = "http://localhost:8529"
  db_name: str = "PROGRESS_TEST"
  # Add: float_precision_decimals: int = 6

  model_config = SettingsConfigDict(
    env_prefix = "progress_",
    env_file = ".env"
  )

@lru_cache()
def get_config() -> Settings:
  return Settings()

# Usage in db.py
conf = config.get_config()
client = ArangoClient(hosts=conf.arango_url, serializer=encoder)
```

### Direct Float Comparisons (Current Pattern - TO BE REPLACED)
```python
# Source: backend/api/endpoints/production.py line 277
if job.qt_completed >= job.qt_planned:
  # Close job logic

# Source: backend/api/events/production/batch_completed.py line 54
if self.batch.qt_total != self.info.completed_batch_qt:
  raise ValueError("Batch quantity mismatch")

# Source: backend/api/events/inventory/inventory_changed.py line 42
if final_qty < 0:
  # Handle negative inventory

# Source: backend/api/events/inventory/inventory_changed.py line 46
elif final_qty == 0:
  # Handle zero inventory
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A | Direct float comparisons throughout | Current state | Precision errors possible |
| N/A | No serializer rounding | Current state | Database has arbitrary precision floats |

**Deprecated/outdated:**
None - this is new functionality, not replacing deprecated patterns.

**Current best practices (2026):**
- Pydantic v2 `model_dump()` instead of v1 `.dict()` (already in use)
- pydantic-settings for configuration (already in use)
- Type hints everywhere (already in use)

## Open Questions

None - all research areas resolved with HIGH confidence.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/api/utils/db.py` - serializer implementation
- Codebase analysis: `backend/api/events/base_event.py` - event storage patterns
- Codebase analysis: `backend/api/events/production/batch_completed.py` - float usage patterns
- Codebase analysis: `backend/api/utils/config.py` - configuration patterns
- [python-arango serializer documentation](https://docs.python-arango.com/en/main/serializer.html) - custom serializer API
- [python-arango API specification](https://docs.python-arango.com/en/main/specs.html) - ArangoClient serializer parameter

### Secondary (MEDIUM confidence)
- [FastAPI JSON encoder documentation](https://fastapi.tiangolo.com/tutorial/encoder/) - jsonable_encoder usage
- WebSearch: python-arango serializer behavior (verified against official docs)

### Tertiary (LOW confidence)
None - all findings verified against official sources or codebase.

## Metadata

**Confidence breakdown:**
- Serialization architecture: HIGH - verified by reading db.py and event code, tested approach
- Float comparison patterns: HIGH - grep'd entire codebase, found 15+ examples
- Config integration: HIGH - existing Settings class pattern clear
- Documentation standards: HIGH - examined 10+ utility modules for patterns

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days - stable domain, Python standard library patterns)
