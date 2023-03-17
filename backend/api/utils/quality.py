class Queries:

  FIND_ISSUES = """
    // Filter first issue properties...
    FOR i IN Issues
    FILTER
      i._key == @key
      && @issue_type ? i.issue_type == @issue_type : true
      && @creator_id ? i.created_by == @creator_id : true
      && @time_created_from ? i.created >= @time_created_from : true
      && @time_created_to ? i.created <= @time_created_to : true
      && @time_closed_from ? i.closed >= @time_closed_from : true
      && @time_closed_to ? i.closed_to <= @time_closed_to : true
      && @issue_open ? i.open == @issue_open : true

      // ...and then in relationships
      FOR ir IN issue_rel
      FILTER
        ir._from == i._id
        && @product_key ? ir._to == CONCAT('Product/', @product_key) : true
        && @work_order_key ? ir._to == CONCAT('WorkOrder/', @work_order_key) : true
        && @job_key ? ir._to == CONCAT('Job/', @job_key) : true
        && @phase_key ? ir._to == CONCAT('Phase/', @phase_key) : true
        && @operation_key ? ir._to == CONCAT('Operation/', @operation_key) : true
    LIMIT @limit || null
    LET rels = (FOR ir IN issue_rel FILTER i._id == ir._from RETURN ir._to)
    LET messages = (FOR m IN messages FILTER m._to == i._id RETURN m)
    RETURN { ...i, linked_to: rels, messages }
  """
