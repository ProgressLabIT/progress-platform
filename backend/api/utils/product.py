from models.product import ProductDoc
from utils.file import UserFile

class Queries:

  GET_PRODUCT_LIST = """
    LET search = CONCAT('%', @code, '%')
    FOR p IN Product
      FILTER !p.trash && LIKE(p.code, search, true)
      LIMIT @limit
      SORT p.code
      RETURN p
  """



def get_product_docs(product_key):
  folder_obj = UserFile.product_media(product_key)
  doc_list = folder_obj.get_folder_contents('doc', name_only=False)

  def doc_data(doc):
    return ProductDoc(
      name=doc.name,
      size=doc.stat().st_size
    )

  result = list(map(doc_data, doc_list))
  return result
