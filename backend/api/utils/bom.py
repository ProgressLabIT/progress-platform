from fastapi.encoders import jsonable_encoder

from models.bom import *

class Queries:

  GET_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
      FILTER e.type == 'BomLine'
      LET phase = DOCUMENT(e._from)
      SORT v.code, phase.alias
      RETURN {
          component_key: v._key,
          bom_line_key: e._key,
          component_code: v.code,
          component_description: v.description,
          phase_key: phase._key,
          phase_name: phase.alias,
          traceability_level: v.traceability_level,
          traceability_mandatory: e.traceability_mandatory,
          consumption_options: e.consumption_options,
          qt: e.qt,
          extra: e.extra
      }
  """

  DELETE_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
    FILTER e.type=="BomLine"
    REMOVE e IN requires
  """

  CHECK_BOM_LOOP = """
    LET start = CONCAT('Product/', @product_key)
    FOR v, e, p in 1..30 OUTBOUND start requires
    // Find loop by filtering edges going back to product
    FILTER e._to == start

    // Return product codes generating the loop
    LET loop = (
        FOR item in p.vertices
        FILTER IS_SAME_COLLECTION(Product, item)
        RETURN item.code
    )
    RETURN loop
  """


def get_bom_from_db(db, product_key):
  db_result = db.aql.execute(
    Queries.GET_PRODUCT_BOM,
    bind_vars=dict(product_key=product_key)
  )
  return [BomLineRead(**i) for i in db_result]


def define_bom_line_for_db(bom_line_in: BomLineWriteIn):
  bom_line_out = BomLineWriteOut(
    component_id = f"Product/{bom_line_in.component_key}",
    phase_id = f"Phase/{bom_line_in.phase_key}",
    qt = bom_line_in.qt,
    traceability_mandatory = bom_line_in.traceability_mandatory,
    consumption_options = bom_line_in.consumption_options,
    traceability_level = bom_line_in.traceability_level,
    extra = bom_line_in.extra
  )

  return jsonable_encoder(bom_line_out, by_alias=True, exclude_none=True)


def find_bom_loops(db, product_key):
  """Make sure the product BoM has no loops in it"""
  bind_vars = dict(product_key=product_key)
  cursor = db.aql.execute(Queries.CHECK_BOM_LOOP, bind_vars=bind_vars)
  loops = [' -> '.join(l) for l in cursor]
  return loops

