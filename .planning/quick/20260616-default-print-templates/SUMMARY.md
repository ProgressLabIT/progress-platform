---
slug: default-print-templates
status: complete
branch: DEV
committed: false
---

# Summary — Default product & position print templates

Re-created the warehouse app's pre-v2 hard-coded product/position labels as pdfme
templates for the current print service. Source of truth: legacy ZPL in
`webapps/warehouse/src/lib/print.js` @ commit `39f0b18c^` (deleted by "printing v2").

## Added (not committed)
- `deploy/scripts/print-templates/default_product_label.json` — `_key=default_product_label`;
  product code (text, fontSize 21) → Code 128 barcode → description (text, fontSize 7).
  basePdf 73×35 mm.
- `deploy/scripts/print-templates/default_position_label.json` — `_key=default_position_label`;
  position code (text, fontSize 18) → Code 39 barcode. basePdf 50×32 mm.
- `deploy/scripts/seed_default_print_templates.py` — idempotent upsert of every
  `print-templates/*.json` into the `PrintTemplate` collection (db_init connection style).
- `deploy/scripts/print-templates/README.md` — usage + config wiring + deltas.

## Method
Ported ZPL dot geometry → mm at 203 DPI (`mm=dots·25.4/203`), dot-heights → pt
(`pt=dots·72/203`); folded the product label's `^LH30,30` home offset into field
positions; barcode baseline (`^FT`) → top-left (`^FO`) for the position label.
Fields bound via the warehouse-supported presets `product.code` / `product.description`
/ `position.code`.

## Verified
- Both JSON files parse; shape matches `PrintTemplateRecord` (text/visual FieldSpec).
- Round-tripped through the real `webapps/warehouse/src/lib/print/zpl.js` `generateZpl()`:
  output `^FO` coords + barcode commands match the legacy ZPL within ±1 dot rounding.

## Deltas from originals (documented in README)
- Code 128 now shows HRI line (v2 renderer forces it on); legacy suppressed it. Cosmetic.
- Description uses scalable font 0 (v2 renderer) vs legacy bitmap font 1. Same size.

## To use
1. `python3 deploy/scripts/seed_default_print_templates.py PROGRESS` (inside the network).
2. Set app config `product_label_template=default_product_label`,
   `position_label_template=default_position_label`.
