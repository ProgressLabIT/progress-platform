# Default print templates

pdfme templates that reproduce the warehouse app's **pre-v2 hard-coded** product
and position labels (the originals lived in the old `webapps/warehouse/src/lib/print.js`,
removed by the "printing v2" migration). Re-created here as proper pdfme templates so
they can be loaded into the print-template library and used by the current
print service (`POST /print-job` → NATS → print-service).

| File | `_key` | Layout (ported from legacy ZPL @ 203 DPI) |
|------|--------|--------------------------------------------|
| `default_product_label.json` | `default_product_label` | Product code (large text) → Code 128 barcode of the code → product description |
| `default_position_label.json` | `default_position_label` | Position code (text) → Code 39 barcode of the code |

Field values are bound via presets (`product.code`, `product.description`,
`position.code`), the only presets the warehouse resolver supplies.

## Load them

Inside the `progress` network (e.g. the API container), after `db_init`:

```bash
python3 deploy/scripts/seed_default_print_templates.py PROGRESS
```

Idempotent — re-run to update the defaults in place.

## Wire the warehouse to them

Set the app config keys so the warehouse picks them up:

- `product_label_template`  → `default_product_label`
- `position_label_template` → `default_position_label`

## Notes / deltas from the originals

- Geometry converted from ZPL dots to millimetres at **203 DPI** (warehouse default);
  the product label's legacy `^LH30,30` home offset is folded into each field position.
- The product barcode now prints its **human-readable interpretation line** (the v2
  Code 128 renderer hard-codes HRI on); the legacy label suppressed it (`^BC,…,N`).
  Cosmetic only — same encoded data.
- Sizes/fonts approximate the legacy dot sizes; adjust per your label stock and tune
  per-printer `dpi` / `offset_x` / `offset_y` in printer config if needed.
