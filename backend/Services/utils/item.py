class Queries:

  GET_ACTIVE_PRODUCTS_FOR_BOM = """
    FOR p IN Product
    FILTER p.active
    RETURN {
      type: 'subassembly',
      _key: p._key,
      code: p.code,
      description: p.description
    }
  """