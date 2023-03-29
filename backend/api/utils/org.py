class Queries:
  GET_USER_LIST = """
    FOR u IN User
      LET active_filter = @active_only ? 'true' : '%'
      FILTER LIKE(TO_STRING(u.active), active_filter) && !u.trash
      SORT u.surname, u.name
      LET dep_data = DOCUMENT(Department, u.department_key)
      RETURN MERGE(u, { department: dep_data })
  """
