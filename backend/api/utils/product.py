from models.product import ProductDoc
from utils.file import FileHandler

class Queries:

  GET_PRODUCT_LIST = """
    LET search = CONCAT('%', @search, '%')
    FOR p IN Product

      // find active products matching the search pattern provided
      LET search_context = CONCAT(p.code, ' ', 'p.description')
      FILTER !p.trash && LIKE(search_context, search, true)

      // keep only required attributes
      LET result = @details ? p : KEEP(p, ["_key", "code", "description", "active"])

      SORT result.code
      LIMIT @offset, @limit

      RETURN p
  """



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
