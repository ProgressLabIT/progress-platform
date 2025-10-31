from fastapi import HTTPException
from models.product import ProductDoc, ProductFull
from utils.db import db
from utils.file import FileHandler

class Queries:
  GET_PRODUCT_LIST = """
    LET products_with_operation = (
      FOR product, edge IN 2..2 INBOUND CONCAT('Operation/', @has_operation_key) requires
      FILTER product != null
      RETURN product._key
    )

    FOR product IN Product
      FILTER !product.trash
      FILTER @has_operation_key == null || product._key IN products_with_operation
      FILTER @active_only != true || product.active == true
      FILTER @traceability_only != true || product.traceability_level

      LET search_context = @search_description ? product.description : product.code

      // Regex search mode
      LET text_match = @search_string == null || REGEX_TEST(search_context, @search_string, true) // true for case insensitive search
      FILTER text_match

      LET tags = (
        FOR edge IN has_tag
          FILTER edge._from == product._id
          RETURN DOCUMENT(Tag, edge._to)
      )
      LET tag_keys = NOT_NULL(tags[*]._key, [])

      // Simple tag search mode
      LET simple_tag_match = @tag_key == null || @tag_key IN tag_keys
      FILTER simple_tag_match

      // ADVANCED MODE FILTERS

      // Advanced text search mode
      LET include_text_match = @include_text == null || REGEX_TEST(search_context, @include_text, true)
      LET exclude_text_match = @exclude_text == null || !REGEX_TEST(search_context, @exclude_text, true)

      // Advanced tag matching logic
      LET include_tags_match = @include_tags == null || (
        @include_tags_operator == "ALL" ? @include_tags ALL IN tag_keys : @include_tags ANY IN tag_keys
      )

      LET exclude_tags_match = @exclude_tags == null || !(
        @exclude_tags_operator == "ALL" ? @exclude_tags ALL IN tag_keys : @exclude_tags ANY IN tag_keys
      )

      // Combine filters based on global operator
      LET adv_filters = [include_text_match, exclude_text_match, include_tags_match, exclude_tags_match]

      FILTER adv_filters ALL == true

      // keep only required attributes
      LET result = @details ? product : KEEP(product, ["_key", "code", "description", "active", "traceability_level", "serial_code_on_creation"])

      SORT result.code
      LIMIT @offset, @limit || null

      RETURN MERGE(result, { tags })
  """

  # DEPRECATED: Use GET_PRODUCT_LIST instead with the new parameters
  SEARCH_PRODUCT = GET_PRODUCT_LIST


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
