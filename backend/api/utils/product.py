from models.product import ProductDoc, ProductFull
from utils.db import db
from utils.file import FileHandler

class Queries:
  GET_PRODUCT_LIST = """
    LET search = CONCAT('%', LOWER(@search), '%')
    LET products_with_operation = (
      FOR product, edge IN 2..2 INBOUND CONCAT('Operation/', @has_operation_key) requires
      FILTER product != null
      RETURN product._key
    )

    FOR product IN Product
      // find active products matching the search pattern provided
      FILTER @has_operation_key == null || product._key IN products_with_operation
      FILTER @active_only ? product.active == true : true
      FILTER @traceability_only ? LENGTH(product.traceability_level) : true

      LET search_context = LOWER(CONCAT(product.code, ' ', product.description))
      FILTER !product.trash && LIKE(search_context, search, true)

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )

      FILTER @tag == null || @tag IN tags[*]._key

      // keep only required attributes
      LET result = @details ? product : KEEP(product, ["_key", "code", "description", "active", "traceability_level", "serialcode_on_batchstart"])

      SORT result.code
      LIMIT @offset, @limit

      RETURN MERGE(product, { tags })
  """

  SEARCH_PRODUCT = """
    LET search_include = CONCAT('%', LOWER(@textToInclude), '%')
    LET search_exclude = CONCAT('%', LOWER(@textToExclude), '%')

    LET products_with_operation = (
      FOR product, edge IN 2..2 INBOUND CONCAT('Operation/', @has_operation_key) requires
      FILTER product != null
      RETURN product._key
    )

    FOR product IN Product
      FILTER !product.trash
      FILTER @has_operation_key == null || product._key IN products_with_operation

      LET search_context = LOWER(CONCAT(product.code, ' ', 'product.description'))

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )

      FILTER
        (@textToInclude ? LIKE(search_context, search_include, true) : <def>) <g_o>
        (@textToExclude ? !LIKE(search_context, search_exclude, true) : <def>) <g_o>
        (@tagsToInclude ? TOKENS(@tagsToInclude, "text_en") <it_o>  tags[*]._key : <def>) <g_o>
        (@tagsToExclude ? TOKENS(@tagsToExclude, "text_en") <et_o>  tags[*]._key : <def>)

      SORT product.code
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
