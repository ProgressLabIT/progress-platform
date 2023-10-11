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
      FILTER field_definition
      RETURN MERGE(f, { type: field_definition.type })
    )
    SORT i.name
    RETURN MERGE(i, { form_template })
  """

  FIND_ISSUES = """

    FOR i IN Issue

    // FILTER BY DOCUMENT PROPERTIES
    FILTER
      // When filtering by document key, parameters will be arrays
      (@issue_key ? POSITION(@issue_key, i._key) : true)
      && (@issue_key_search ? CONTAINS(i._key, @issue_key_search) : true)
      && (@issue_type_key ? POSITION(@issue_type_key, i.issue_type_key) : true)
      && (@created_by ? POSITION(@created_by[* RETURN CONCAT('User/', CURRENT)], i.created_by) : true)
      && (@closed_by ? POSITION(@closed_by[* RETURN CONCAT('User/', CURRENT)], i.closed_by) : true)
      && (@time_created_from ? i.created >= @time_created_from : true)
      && (@time_created_to ? i.created <= @time_created_to : true)
      && (@time_closed_from ? i.closed >= @time_closed_from : true)
      && (@time_closed_to ? i.closed <= @time_closed_to : true)
      && (@issue_open != null ? i.open == @issue_open : true)
      && (@issue_closed != null ? i.open == !@issue_closed : true)
      && (@issue_critical != null ? i.critical == @issue_critical : true)
      && (@issue_non_critical != null ? i.critical == !@issue_non_critical : true)
      && (@advanced_filters
        ? LENGTH((
            // This subquery returns match true/false for each filter
            FOR advanced_filter IN NOT_NULL(@advanced_filters.filters, [])
            RETURN i.data
              ? i.data[* FILTER CURRENT._key == advanced_filter._key
                && advanced_filter.value == (
                  CURRENT.type == "choice" ? CURRENT.value.value
                  : CURRENT.type == "boolean" ? !!CURRENT.value
                  : CURRENT.value
                )]
              : []
          )[**]) >= (@advanced_filters.operator == "OR" ? 1 : LENGTH(@advanced_filters.filters))
        : true
      )

    LET type_data = FIRST(
      FOR it IN IssueType
      FILTER it._key == i.issue_type_key
      RETURN it
    )

    LET issue_data = (
      FOR field IN NOT_NULL(i.data, [])
      FOR fdef IN NOT_NULL(type_data.form_template, [])
      FILTER
        fdef._key == field._key
        && DOCUMENT(CustomField, field._key)
      RETURN MERGE(fdef, field)
    )

    // FILTER BY LINKS

    // PRODUCT
    LET product = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Product'
      RETURN l
    )

    FILTER
      (@product_key ? product._key IN @product_key : true)
      && (@product_code_search ? CONTAINS(LOWER(product.code), LOWER(@product_code_search)) : true)

    // PHASE
    LET phase = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Phase'
      RETURN l
    )

    FILTER
      (@phase_key ? phase._key IN @phase_key : true)
      && (@phase_alias_search ? CONTAINS(LOWER(phase.alias), LOWER(@phase_alias_search)) : true)

    // OPERATION
    LET operation = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Operation'
      RETURN l
    )

    FILTER @operation_key ? operation && operation._key IN @operation_key : true

    // WORK ORDER
    LET work_order = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'WorkOrder'
      RETURN l
    )

    FILTER
      (@work_order_key ? work_order._key IN @work_order_key : true)
      && (@work_order_code_search ? CONTAINS(LOWER(work_order.wo_code), LOWER(@work_order_code_search)) : true)
      && (@project_search ? CONTAINS(LOWER(work_order.project_code), LOWER(@project_search)) : true)

    // JOB
    LET job = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Job'
      RETURN l
    )

    FILTER @job_key ? job._key IN @job_key : true

    // LIMIT FILTERED ISSUE RECORDS
    SORT i.created
    LIMIT @limit || null

    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(i, {
      icon: type_data.icon,
      issue_type_name: type_data.name,
      data: issue_data,
      phase_alias: phase.alias
    })

    LET issue_links = { product, operation, phase, work_order }

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
