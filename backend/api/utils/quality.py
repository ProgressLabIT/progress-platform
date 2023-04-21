class Queries:
  FETCH_ISSUE_TYPES = """
    FOR i IN IssueType
    FILTER
      @key ? i._key == @key : true
      && @code ? i.code == @code : true
      && @critical ? i.critical == @critical : true
      && @active_only ? i.active_only == @active_only : true
    LET form_template = (
      FOR f IN i.form_template
      LET field_definition = FIRST(
        FOR fdef IN CustomField
        FILTER fdef._key == f._key
        RETURN fdef
      )
      RETURN MERGE(f, { type: field_definition.type })
    )
    RETURN MERGE(i, { form_template })
  """

  FIND_ISSUES = """
    FOR i IN Issue
    FILTER
      // When filtering by document key, parameters will be arrays
      // Filter first issue properties...
      @issue_key ? POSITION(@issue_key, i._key) : true
      && @issue_type ? POSITION(@issue_type, i.issue_type) : true
      && @creator_id ? POSITION(@creator_id, i.created_by) : true
      && @time_created_from ? i.created >= @time_created_from : true
      && @time_created_to ? i.created <= @time_created_to : true
      && @time_closed_from ? i.closed >= @time_closed_from : true
      && @time_closed_to ? i.closed_to <= @time_closed_to : true
      && @issue_open != null ? i.open == @issue_open : true

      // Then in relationships...
      FOR v, e IN 1..1 OUTBOUND i issue_rel
      FILTER
        // Here the keys must be turned into document ids
        @product_key ? POSITION(@product_key[* RETURN CONCAT('Product/', CURRENT)], e._to) : true
        && @work_order_key ? POSITION(@work_order_key[* RETURN CONCAT('WorkOrder/', CURRENT)], e._to) : true
        && @job_key ? POSITION(@job_key[* RETURN CONCAT('Job/', CURRENT)], e._to) : true
        && @phase_key ? POSITION(@phase_key[* RETURN CONCAT('Phase/', CURRENT)], e._to) : true
        && @operation_key ? POSITION(@operation_key[* RETURN CONCAT('Operation/', CURRENT)], e._to) : true

    LIMIT @limit || null
    LET type_data = FIRST(
      FOR it IN IssueType
      FILTER it._key == i.issue_type
      RETURN it
    )
    SORT i.created
    RETURN MERGE(i, { icon: type_data.icon, type_name: type_data.name })
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
