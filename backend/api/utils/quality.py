class Queries:
  FETCH_ISSUE_TYPES = """
    FOR i IN IssueType
    FILTER
      @key ? i._key == @key : true
      && @code ? i.code == @code : true
      && @critical ? i.critical == @critical : true
      && @active_only ? i.active == @active_only : true
    LET form_template = (
      FOR f IN i.form_template
      LET field_definition = FIRST(
        FOR fdef IN CustomField
        FILTER fdef._key == f._key
        RETURN fdef
      )
      RETURN MERGE(f, { type: field_definition.type })
    )
    SORT i.name
    RETURN MERGE(i, { form_template })
  """

  FIND_ISSUES = """
    // Graph results will return the same issue for each link
    LET link_filtered = UNIQUE(
      FOR i IN Issue
      FOR v, e IN 1..1 OUTBOUND i issue_rel
      FILTER
        // Here the keys must be turned into document ids
        @product_key ? POSITION(@product_key[* RETURN CONCAT('Product/', CURRENT)], e._to) : true
        && @work_order_key ? POSITION(@work_order_key[* RETURN CONCAT('WorkOrder/', CURRENT)], e._to) : true
        && @job_key ? POSITION(@job_key[* RETURN CONCAT('Job/', CURRENT)], e._to) : true
        && @phase_key ? POSITION(@phase_key[* RETURN CONCAT('Phase/', CURRENT)], e._to) : true
        && @operation_key ? POSITION(@operation_key[* RETURN CONCAT('Operation/', CURRENT)], e._to) : true
      RETURN i
    )

    FOR i IN link_filtered
    FILTER
      // When filtering by document key, parameters will be arrays
      @issue_key ? POSITION(@issue_key, i._key) : true
      && @issue_type_key ? POSITION(@issue_type_key, i.issue_type_key) : true
      && @creator_id ? POSITION(@creator_id, i.created_by) : true
      && @time_created_from ? i.created >= @time_created_from : true
      && @time_created_to ? i.created <= @time_created_to : true
      && @time_closed_from ? i.closed >= @time_closed_from : true
      && @time_closed_to ? i.closed_to <= @time_closed_to : true
      && @issue_open ? i.open == @issue_open : true

    LIMIT @limit || null

    LET type_data = FIRST(
      FOR it IN IssueType
      FILTER it._key == i.issue_type_key
      RETURN it
    )

    LET issue_data = (
      FOR field IN NOT_NULL(i.data, [])
      FOR fdef IN NOT_NULL(type_data.form_template, [])
      FILTER fdef._key == field._key
      RETURN MERGE(fdef, field)
    )

    SORT i.created
    RETURN MERGE(i, { icon: type_data.icon, issue_type_name: type_data.name, data: issue_data })
  """

  CHECK_PRODUCTION_CRITICAL_STATUS = """
    // Find WorkOrder and Job related to Issue
    LET docs = (
      FOR v, e in 1..1 OUTBOUND @issue_id issue_rel
      LET collection = PARSE_IDENTIFIER(e._to).collection
      FILTER POSITION(['WorkOrder', 'Job'], collection)
      RETURN v._id
    )

    /* Check if there are open critical issue associated with each
    and update critical status accordingly */
    FOR d IN docs
    LET critical = TO_BOOL(COUNT(
      FOR v, e in 1..1 INBOUND d issue_rel
      FILTER v.critical && v.open
      RETURN 1
    ))
    RETURN { _id: d, critical }
  """
