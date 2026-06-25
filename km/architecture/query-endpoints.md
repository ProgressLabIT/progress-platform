# Query-Derived Read Endpoints (AQL + FastAPI gotchas)

Read endpoints often clone an existing list query — e.g. an **export/report** endpoint that must return exactly the rows a list screen shows. The temptation is "copy the list AQL verbatim, change only the `RETURN`." Two non-obvious failure modes bite this pattern. Both are invisible to static review and only surface against a live ArangoDB; the worked example is `GET /product/export` (`backend/api/endpoints/product.py`, cloned from `Queries.GET_PRODUCT_LIST` in `backend/api/utils/product.py`).

## 1. ArangoDB rejects undeclared bind vars (`ERR 1552`)

ArangoDB errors on **any** bind parameter passed that the query text does not reference:

```
[HTTP 400][ERR 1552] AQL: bind parameter 'details' was not declared in the query (while parsing)
```

The list endpoint calls `db.aql.execute(Queries.GET_PRODUCT_LIST, bind_vars=params.model_dump())`, relying on the query referencing all of `ProductSearchParams`' fields. But `GET_PRODUCT_LIST` references `@details` **inside its `RETURN` clause** (to switch `ProductDetails` vs `ProductBaseData`) — exactly the clause an export replaces. The cloned query then references 14 of 15 vars, and passing the full `model_dump()` 500s.

**Rule:** when reusing `model_dump()` against a modified query, diff the `@`-bind-vars the *final* query actually references against the model's keys and drop the extras. Pay special attention to vars used only inside a `RETURN`/`LET` you rewrote.

```python
bind_vars = params.model_dump()
bind_vars.pop("details", None)   # export RETURN never uses it
db.aql.execute(Queries.EXPORT_PRODUCT, bind_vars=bind_vars)
```

## 2. FastAPI flattens a `Query()` model only when it is the sole parameter

A Pydantic model as query params works via `Annotated[Model, Query()]` — **but only when the model is the endpoint's single parameter.** Add any other scalar query param (e.g. `format`) and FastAPI stops flattening and treats the model as one required field:

```
422  {"detail":[{"type":"missing","loc":["query","params"],"msg":"Field required"}]}
```

This is why `get_product_list(params: Annotated[ProductSearchParams, Query()])` works but `export_products(params: Annotated[ProductSearchParams, Query()], format: Literal[...] = "xlsx")` 422s. (Observed on FastAPI 0.135.)

**Rule:** if a handler has a model query-param **and** any other scalar query param, annotate the model with `Depends()`, not `Query()`. `Depends()` flattens regardless of sibling params:

```python
async def export_products(
    params: Annotated[ProductSearchParams, Depends()],
    format: Literal["xlsx", "csv", "template"] = "xlsx",
):
```

## Testing note

Both bugs above were caught only by running the integration suite against a live ArangoDB. On macOS the testcontainer needs `DOCKER_HOST=unix:///Users/$USER/.docker/run/docker.sock` (see `testing/pytest/README.md`); a "tests infra-unavailable" report usually just means that override is missing, not that Docker is down. Never close a query-endpoint task on static checks alone — route placement, AQL validity, and param binding all pass inspection while failing at runtime.
