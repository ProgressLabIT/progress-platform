# Phase 1: Precision Foundation - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase creates the core infrastructure for float precision management: serializer rounding in db.py to round all floats to 6 decimals before writing to ArangoDB, comparison utility functions (float_equals, float_less_than, float_greater_than) with tolerance-based equality, helper function (round_float) for explicit rounding, and documentation of the 6-decimal / 1e-6 epsilon standard.

**Not in scope:** Migrating existing business logic to use these utilities (Phase 2), updating frontend display (Phase 3), or changing the precision standard from 6 decimals.

</domain>

<decisions>
## Implementation Decisions

### Module Organization
- **Import availability**: Utilities must be importable everywhere in backend/api (events, endpoints, utils, all modules)
- **Function naming**: Use descriptive names - `float_equals`, `float_less_than`, `float_greater_than`, `round_float` (not abbreviated forms)
- **Configuration**: Serializer rounding precision should be configurable via config file (not hardcoded to 6 decimals)

### Function API Design
- **Epsilon parameter**: Make epsilon a parameter with default value: `float_equals(a, b, epsilon=1e-6)` - allows override when needed
- **Type hints**: Full type annotations required: `def float_equals(a: float, b: float, epsilon: float = 1e-6) -> bool`
- **round_float decimals**: Accept decimals parameter with default based on config: `round_float(value, decimals=None)` where None means "use config value"

### Edge Case Behavior
- **NaN handling**: Follow IEEE 754 standard - NaN is not equal to anything including itself (NaN != NaN returns True)
- **Bounds checking**: No bounds checking - accept any float value Python supports (no warnings for extreme values)
- **Epsilon type**: Use absolute epsilon (always 1e-6), not relative/scaled epsilon based on magnitude

### Documentation Depth
- **Function docstrings**: Detailed documentation with full examples - include description, params, returns, usage examples, edge cases
- **Serializer comments**: Include inline comments in db.py explaining why rounding is applied (rationale for 6-decimal precision)

### Claude's Discretion
Areas where Claude should make implementation choices:
- **Module location**: Choose whether to create new `float_precision.py` or extend existing module based on codebase patterns
- **None handling**: Determine whether comparison functions should accept None values or raise TypeError based on usage patterns
- **Infinity handling**: Decide whether `round_float` should return infinity as-is or raise ValueError based on domain needs
- **Module docstring depth**: Determine appropriate level (full rationale vs brief overview) based on codebase documentation standards
- **Examples location**: Choose whether to include examples in docstrings only or create separate examples file

</decisions>

<specifics>
## Specific Ideas

**Config-driven precision**: User explicitly wants the rounding precision (6 decimals) to be configurable via config file rather than hardcoded, allowing future flexibility without code changes.

**Overridable epsilon**: The default epsilon (1e-6) should be overridable via function parameter for cases where different tolerance is needed, while maintaining the standard for normal usage.

**Absolute not relative tolerance**: Comparisons should use fixed absolute epsilon (1e-6) rather than scaling based on number magnitude - simpler and sufficient for manufacturing domain.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-precision-foundation*
*Context gathered: 2026-02-17*
