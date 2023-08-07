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
    LET first_filtered = (
      FOR i IN Issue
      FILTER
        // When filtering by document key, parameters will be arrays
        @issue_key ? POSITION(@issue_key, i._key) : true
        && @issue_key_search ? CONTAINS(i._key, @issue_key_search) : true
        && @issue_type_key ? POSITION(@issue_type_key, i.issue_type_key) : true
        && @created_by ? POSITION(@created_by[* RETURN CONCAT('User/', CURRENT)], i.created_by) : true
        && @closed_by ? POSITION(@closed_by[* RETURN CONCAT('User/', CURRENT)], i.closed_by) : true
        && @time_created_from ? i.created >= @time_created_from : true
        && @time_created_to ? i.created <= @time_created_to : true
        && @time_closed_from ? i.closed >= @time_closed_from : true
        && @time_closed_to ? i.closed <= @time_closed_to : true
        && @issue_open != null ? i.open == @issue_open : true
        && @issue_closed != null ? i.open == !@issue_closed : true
        && @issue_critical != null ? i.critical == @issue_critical : true
        && @issue_non_critical != null ? i.critical == !@issue_non_critical : true
      RETURN i
    )

    // Graph results will return the same issue for each link
    LET links_filtered = UNIQUE(
      FOR i IN first_filtered
      FOR v, e IN 1..1 OUTBOUND i issue_rel
      FILTER
        // Key Parameters are passed as lists. Keys must be turned into document ids
        @product_key ? POSITION(@product_key[* RETURN CONCAT('Product/', CURRENT)], e._to) : true
        && @work_order_key ? POSITION(@work_order_key[* RETURN CONCAT('WorkOrder/', CURRENT)], e._to) : true
        && @job_key ? POSITION(@job_key[* RETURN CONCAT('Job/', CURRENT)], e._to) : true
        && @phase_key ? POSITION(@phase_key[* RETURN CONCAT('Phase/', CURRENT)], e._to) : true
        && @operation_key ? POSITION(@operation_key[* RETURN CONCAT('Operation/', CURRENT)], e._to) : true
        // Substring search for entity names
        && @product_code_search ? (
          PARSE_IDENTIFIER(v).collection == 'Product'
          && CONTAINS(LOWER(v.code), LOWER(@product_code_search))
        ) : true
        && @work_order_code_search ? (
          PARSE_IDENTIFIER(v).collection == 'WorkOrder'
          && CONTAINS(LOWER(v.wo_code), LOWER(@work_order_code_search))
        ) : true
        && @project_search ? (
          PARSE_IDENTIFIER(v).collection == 'WorkOrder'
          && CONTAINS(LOWER(v.project_code), LOWER(@project_search))
        ) : true
        && @phase_alias_search ? (
          PARSE_IDENTIFIER(v).collection == 'Phase'
          && CONTAINS(LOWER(v.alias), LOWER(@phase_alias_search))
        ) : true
      RETURN i
    )

    // Limit and Enrich filtered issue records
    FOR i IN links_filtered
    SORT i.created
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

    // Phase alias is always required

    LET phase = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Phase'
      RETURN l
    )

    LET base_result = MERGE(i, {
      icon: type_data.icon,
      issue_type_name: type_data.name,
      data: issue_data,
      phase_alias: phase.alias
    })

    // Add other links data to record if requested


    LET product = @with_links ? FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Product'
      RETURN l
    ) : null

    LET operation = @with_links ? FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Operation'
      RETURN l
    ) : null

    LET work_order = @with_links ?FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'WorkOrder'
      RETURN l
    ) : null

    LET issue_links = @with_links ? { product, operation, phase, work_order } : null

    RETURN @with_links ? MERGE(base_result, { links: issue_links }) : base_result
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
