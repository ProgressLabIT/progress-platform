from fastapi.encoders import jsonable_encoder

from models.bom import *

class Queries:

  GET_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
      FILTER e.type like 'BomItem'
      LET phase = e._from
      
      RETURN {
          item_key: v._key,
          bom_line_key: e._key,
          code: v.code,
          description: v.description,
          item_type: v.type,
          phase_key: PARSE_IDENTIFIER(phase).key,
          phase_name: DOCUMENT(phase).alias,
          qt: e.qt
      }
  """

  DELETE_PRODUCT_BOM = """
    FOR v,e IN 2..2 OUTBOUND DOCUMENT('Product', @product_key) requires
    FILTER e.type=="BomItem"
    REMOVE e IN requires
  """


def get_bom_from_db(db, product_key):
  return db.aql.execute(
    Queries.GET_PRODUCT_BOM, 
    bind_vars=dict(product_key=product_key)
  )


def define_bom_line_for_db(bom_line_in):
  if bom_line_in.item_type == 'assembly':
    target_collection = 'Product'  
  else:
    target_collection = 'ProductionItem'
  
  bom_line_out = BomLineWriteOut(
    item_id=f"{target_collection}/{bom_line_in.item_key}",
    phase_id=f"Phase/{bom_line_in.phase_key}",
    qt=bom_line_in.qt
  )

  return jsonable_encoder(bom_line_out, by_alias=True, exclude_none=True)

