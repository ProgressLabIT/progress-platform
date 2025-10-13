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
        FILTER fdef._key == f.custom_field_key
        RETURN fdef
      )
      FILTER field_definition
      RETURN MERGE(f, { type: field_definition.type })
    )

    LET print_templates = (
      FOR v IN 1..1 OUTBOUND i can_use_print_template
      RETURN v
    )

    SORT i.name
    RETURN MERGE(i, { form_template, print_templates })
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
        ? LENGTH(
            // This subquery returns match true/false for each filter
            FOR advanced_filter IN NOT_NULL(@advanced_filters.filters, [])
            FOR d IN i.data
            FILTER d.custom_field_key == advanced_filter._key
            LET type = DOCUMENT(CustomField, d.custom_field_key).type
            FILTER (
              type == "text" ? CONTAINS(LOWER(d.value), LOWER(advanced_filter.value))
              : type == "choice" ? d.value._key == advanced_filter.value._key
              : type == "boolean" ? !!d.value
              : type == "files" ? !!LENGTH(d.value)
              : d.value == advanced_filter.value
            )
            RETURN 1
          ) >= (@advanced_filters.operator == "OR" ? 1 : LENGTH(@advanced_filters.filters))
        : true
      )

    LET type_data = FIRST(
      FOR it IN IssueType
      FILTER it._key == i.issue_type_key
      RETURN it
    )

    LET issue_data = (
      FOR field_value IN NOT_NULL(i.data, [])
      FOR field IN NOT_NULL(type_data.form_template, [])
      FILTER
        field._key == field_value.form_field_key
        && DOCUMENT(CustomField, field.custom_field_key)
      RETURN MERGE(field, { value: field_value.value })
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

    // SERIAL
    LET serial = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Serial'
      RETURN l
    )

    FILTER
      (@serial_search ? CONTAINS(LOWER(serial.code), LOWER(@serial_search)) : true)

    // JOB
    LET job = FIRST(
      FOR l IN 1..1 OUTBOUND i issue_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Job'
      RETURN l
    )

    FILTER @job_key ? job._key IN @job_key : true

    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(i, {
      icon: type_data.icon,
      issue_type_name: type_data.name,
      data: issue_data,
      phase_alias: phase.alias
    })

    LET issue_links = { job, product, operation, phase, work_order, serial }

    LET result = @with_links ? MERGE(base_result, { links: issue_links }) : base_result

    // LIMIT FILTERED ISSUE RECORDS
    SORT result.<sort_by> @sorting_order
    LIMIT @offset, @limit || null

    return result
  """

  FETCH_TASK_TYPES = """
    FOR t IN TaskType
    FILTER
      @active_only ? t.active == @active_only : true
      && @name ? t.name == @name : true

    LET form_fields = (
      FOR f IN t.form_fields
      LET field_definition = FIRST(
        FOR fdef IN CustomField
        FILTER fdef._key == f.custom_field_key
        RETURN fdef
      )
      FILTER field_definition
      RETURN MERGE(f, { type: field_definition.type })
    )

    LET print_templates = (
      FOR v IN 1..1 OUTBOUND t can_use_print_template
      RETURN v
    )

    SORT t.name
    RETURN MERGE(t, { form_fields, print_templates })
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


  FIND_TASKS = """
    LET link_type = {
      Issue: { type: 'issue', code: 'code' },
      WorkOrder: { type: 'work_order', code: 'wo_code' },
      Product: { type: 'product', code: 'code' },
      Equipment: { type: 'equipment', code: 'code' },
      Serial: { type: 'serial', code: 'code' },
      Task: { type: 'task', code: 'code' }
    }
    FOR t IN Task
    FILTER
      @search ? CONTAINS(LOWER(CONCAT(t.code, ' ', t.title)), LOWER(@search)) : true
      && (@task_type_key ? t.task_type_key == @task_type_key : true)
      && (@status_pending == false ? t.status != 'pending' : true)
      && (@status_open == false ? t.status != 'open' : true)
      && (@status_completed == false ? t.status != 'completed' : true)
      && (@status_canceled == false ? t.status != 'canceled' : true)
      && (@owner_key ? t.owner_key == @owner_key : true)
      && (@assigned_to ? @assigned_to ALL IN t.assigned_to[* RETURN CURRENT.user_key] : true)
      // Gather all links once (ANY direction on task_rel)


      && (@start_from ? t.start_from >= @start_from : true)
      && (@due_by ? t.due_by <= @due_by : true)
      && (@created_from ? t.created >= @created_from : true)
      && (@created_to ? t.created <= @created_to : true)
      && (@closed_from ? t.closed >= @closed_from : true)
      && (@closed_to ? t.closed <= @closed_to : true)

      // LINK FILTERS using precomputed links
      LET links = (
        FOR l IN 1..1 ANY t task_rel
        LET meta = link_type[PARSE_IDENTIFIER(l._id).collection]
        RETURN {
          type: meta.type,
          key: l._key,
          code: l[meta.code]
        }
      )

      FILTER
      (@issue_key ? links[? ANY FILTER CURRENT.type == 'issue' && CURRENT.key == @issue_key] : true)
      && (@work_order_key ? links[? ANY FILTER CURRENT.type == 'work_order' && CURRENT.key == @work_order_key] : true)
      && (@product_key ? links[? ANY FILTER CURRENT.type == 'product' && CURRENT.key == @product_key] : true)
      && (@serial_key ? links[? ANY FILTER CURRENT.type == 'serial' && CURRENT.key == @serial_key] : true)
      && (@linked_task_key ? links[? ANY FILTER CURRENT.type == 'task' && CURRENT.key == @linked_task_key] : true)

      // ADVANCED FILTERS
      && (@advanced_filters
        ? LENGTH(
            // This subquery returns match true/false for each filter
            FOR advanced_filter IN NOT_NULL(@advanced_filters.filters, [])
            FOR f IN NOT_NULL(t.form_fields, [])
            FILTER f.custom_field_key == advanced_filter._key
            LET type = DOCUMENT(CustomField, f.custom_field_key).type
            FILTER (
              type == "text" ? CONTAINS(LOWER(f.value), LOWER(advanced_filter.value))
              : type == "choice" ? f.value._key == advanced_filter.value._key
              : type == "boolean" ? !!f.value
              : type == "files" ? !!LENGTH(f.value)
              : f.value == advanced_filter.value
            )
            RETURN 1
          ) >= (@advanced_filters.operator == "OR" ? 1 : LENGTH(@advanced_filters.filters))
        : true
      )

    LET type_data = FIRST(
      FOR tt IN TaskType
      FILTER tt._key == t.task_type_key
      RETURN tt
    )

    SORT t.due_by
    LIMIT @offset, @limit || null
    RETURN MERGE(t, { icon: type_data.icon, task_type_name: type_data.name, links })
  """

  GET_TASK_DATA = """
    FOR t IN Task
    FILTER t._key == @task_key

    LET task_type = FIRST(
      FOR tt IN TaskType
      FILTER tt._key == t.task_type_key
      RETURN tt
    )

    LET work_sessions = (
      FOR ws IN WorkSession
      FILTER ws.task_key == t._key
      RETURN ws
    )

    LET time_spent = (
      LET now = DATE_NOW()
      FOR user_key IN NOT_NULL(t.assigned_to, [])
      LET active = work_sessions[? ANY FILTER CURRENT.active]
      LET duration = SUM(
        FOR ws IN work_sessions
        FILTER ws.user_key == user_key
        RETURN ws.active ? ws.duration : DATE_DIFF(ws.start, now, 'f')
      )
      RETURN { user_key, duration, active }
    )

    LET task_links = (
      LET link_type = {
        Issue: { type: 'issue', code: 'code' },
        WorkOrder: { type: 'work_order', code: 'wo_code' },
        Product: { type: 'product', code: 'code' },
        Equipment: { type: 'equipment', code: 'code' },
        Serial: { type: 'serial', code: 'code' },
        Task: { type: 'task', code: 'code' }
      }
      FOR l IN 1..1 ANY t task_rel
      LET meta = link_type[PARSE_IDENTIFIER(l._id).collection]
      RETURN {
        type: meta.type,
        key: l._key,
        code: l[meta.code]
      }
    )

    RETURN MERGE(t, {
      time_spent,
      links: task_links,
      icon: task_type.icon,
      task_type_name: task_type.name,
      allowed_linked_entities: task_type.link_settings[*].type
    })
  """
