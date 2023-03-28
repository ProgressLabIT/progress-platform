class Queries:

  FIND_ISSUES = """
    FOR i IN Issue
    FILTER
      // Filter first issue properties...
      @issue_key ? i._key == @issue_key : true
      && @issue_type ? i.issue_type == @issue_type : true
      && @creator_id ? i.created_by == @creator_id : true
      && @time_created_from ? i.created >= @time_created_from : true
      && @time_created_to ? i.created <= @time_created_to : true
      && @time_closed_from ? i.closed >= @time_closed_from : true
      && @time_closed_to ? i.closed_to <= @time_closed_to : true
      && @issue_open != null ? i.open == @issue_open : true

      // Then in relationships...
      FOR v, e IN 1..1 OUTBOUND i issue_rel
      FILTER
        @product_key ? e._to == CONCAT('Product/', @product_key) : true
        && @work_order_key ? e._to == CONCAT('WorkOrder/', @work_order_key) : true
        && @job_key ? e._to == CONCAT('Job/', @job_key) : true
        && @phase_key ? e._to == CONCAT('Phase/', @phase_key) : true
        && @operation_key ? e._to == CONCAT('Operation/', @operation_key) : true

    LIMIT @limit || null
    LET type_data = FIRST(
      FOR it IN IssueType
      FILTER it._key == i.issue_type
      RETURN it
    )
    RETURN MERGE(i, { icon: type_data.icon, type_name: type_data.name })
  """
