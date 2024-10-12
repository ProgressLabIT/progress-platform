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
      LET search_context = LOWER(CONCAT(product.code, ' ', product.description))
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

      FILTER !@has_operation_key || product._key IN products_with_operation

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )

      // keep only required attributes
      LET result = @details ? product : KEEP(product, ["_key", "code", "description", "active", "traceability_level"])

      SORT result.code
      LIMIT @offset, @limit

      RETURN MERGE(product, { tags })
  """

  SEARCH_PRODUCT = """
    LET search_include = CONCAT('%', LOWER(@textToInclude), '%')
    LET search_exclude = CONCAT('%', LOWER(@textToExclude), '%')

    FOR product IN Product
      LET search_context = LOWER(CONCAT(product.code, ' ', 'product.description'))

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )

      LET search_tags = (
        FOR tag IN tags
          RETURN tag._key
      )

      FILTER !product.trash

      FILTER
        (@textToInclude?LIKE(search_context, search_include, true):<def>) <g_o>
        (@textToExclude?!LIKE(search_context, search_exclude, true):<def>) <g_o>
        (@tagsToInclude?TOKENS(@tagsToInclude, "text_en") <it_o>  search_tags:<def>) <g_o>
        (@tagsToExclude?TOKENS(@tagsToExclude, "text_en") <et_o>  search_tags:<def>)

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
