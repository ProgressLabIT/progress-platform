from fastapi.encoders import jsonable_encoder

from models.bom import *

class Queries:

  GET_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
      FILTER e.type like 'BomLine'
      LET phase = e._from
      
      RETURN {
          product_key: v._key,
          bom_line_key: e._key,
          product_code: v.code,
          product_description: v.description,
          phase_key: PARSE_IDENTIFIER(phase).key,
          phase_name: DOCUMENT(phase).alias,
          qt: e.qt
      }
  """

  DELETE_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
    FILTER e.type=="BomLine"
    REMOVE e IN requires
  """


def get_bom_from_db(db, product_key):
  db_result = db.aql.execute(
    Queries.GET_PRODUCT_BOM, 
    bind_vars=dict(product_key=product_key)
  )
  return [BomLineRead(**i) for i in db_result]


def define_bom_line_for_db(bom_line_in):
  bom_line_out = BomLineWriteOut(
    product_id=f"Product/{bom_line_in.product_key}",
    phase_id=f"Phase/{bom_line_in.phase_key}",
    qt=bom_line_in.qt
  )

  return jsonable_encoder(bom_line_out, by_alias=True, exclude_none=True)

