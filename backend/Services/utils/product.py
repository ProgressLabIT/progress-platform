class Queries:

  GET_PRODUCT_LIST = """
    LET search = CONCAT('%', @code, '%')
    FOR p IN Product
      FILTER !p.trash && LIKE(p.code, search, true)
      LIMIT @limit
      SORT p.code
      RETURN p
  """