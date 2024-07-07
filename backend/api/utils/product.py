from commons.models.product import ProductDoc, ProductFull
from commons.utils.db import db
from utils.file import FileHandler

class Queries:
  GET_PRODUCT_LIST = """
    LET search = CONCAT('%', LOWER(@search), '%')

    FOR product IN Product
      // find active products matching the search pattern provided
      LET search_context = LOWER(CONCAT(product.code, ' ', 'product.description'))
      FILTER !product.trash && LIKE(search_context, search, true)
      && (@active? product.active == @active: true)
      && (@tag
        ? LENGTH(
            // This subquery returns match true/false for each filter
            FOR edge IN has_tag
                FILTER edge._from == product._id
                FILTER edge._to == CONCAT('Tag/', @tag)
            RETURN 1
          ) >= 1
        : true
      )

      FILTER !@has_operation_key || FIRST(
        LET operation = Document(Operation, @has_operation_key)
        FOR phase, phase_edge IN 1..1 INBOUND operation requires
          FILTER phase_edge.type == 'PhaseOperation'
          FOR product_vertex, product_edge IN 1..1 INBOUND phase requires
            FILTER product_edge.type == 'ProductPhase'
              && product_vertex._id == product._id
            LIMIT 1
            RETURN true
      )

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )

      // keep only required attributes
      LET result = @details ? product : KEEP(product, ["_key", "code", "description", "active"])

      SORT result.code
      LIMIT @offset, @limit

      RETURN MERGE(product, { tags })
  """


def get_product_data_from_code(product_code: str) -> ProductFull:
  cursor = db.collection('Product').find(dict(code=product_code, trash=False))
  try:
    return ProductFull(**cursor.next())
  except StopIteration:
    raise HTTPException(
      status_code=404,
      detail=f"No product found with the code provided: {product_code}"
    )

def get_product_docs(product_key):
  folder_obj = FileHandler.product_media(product_key)
  doc_list = folder_obj.get_folder_contents('doc', name_only=False)

  def doc_data(doc):
    return ProductDoc(
      name=doc.name,
      size=doc.stat().st_size
    )

  result = list(map(doc_data, doc_list))
  return result
