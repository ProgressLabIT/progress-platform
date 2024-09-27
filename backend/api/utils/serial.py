
class Queries:

  GET_PRODUCT_STEPS = """
    FOR phase IN Phase
      FILTER phase.product_key == @product_key
      RETURN {
        product_key: phase.product_key,
        alias: phase.alias,
        phase_key: phase._key,
        steps: (
          FOR step IN Step
            FILTER step._key in phase.step_sequence
            return step
        )}
  """

  GET_BATCH_SERIALS = """
    FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
    RETURN s
  """

  GET_ALL_SERIALS_IN_BATCH = """
    FOR edge IN batch_serial
      FILTER edge._from == @from_id
      LET serial = DOCUMENT(Serial, edge._to)

      LET childs = (
          FOR linked_serial IN contains
              FILTER linked_serial.wo_key == serial.wo_key
              && (linked_serial._from == serial.id || linked_serial.from_serial == serial._key)
              && linked_serial.replaced == false
              RETURN DOCUMENT(Serial, linked_serial._to)
          )

      RETURN MERGE(serial, { childs: childs })
  """


  GET_SERIAL_PARENTS = """
      LET start = @serial_id
        FOR v, e IN 0..9999 INBOUND start contains OPTIONS { uniqueVertices: "path" }
          LET product = DOCUMENT(Product, v.product_key)
          RETURN merge({
              serial_key: v._key,
              replaced: e.replaced,
              serial_code: v.code,
              product_key: product._key,
              product_code: product.code,
              product_description: product.description
      })

  """

  GET_SERIAL_HIERARCHY = """
      LET start = @serial_id
        FOR v, e IN 0..9999 ANY start contains OPTIONS { uniqueVertices: "path" }
          LET product = DOCUMENT(Product, v.product_key)
          FILTER v.deleted == false

          RETURN merge({
              serial_id: v._id,
              serial_key: v._key,
              replaced: e.replaced,
              serial_code: v.code,
              product_key: product._key,
              product_code: product.code,
              product_description: product.description,
              from: e._from,
              to: e._to
      })
  """

  GET_SERIAL_CHILDREN = """
      LET start = @serial_id
        FOR v, e IN 1..1 OUTBOUND start contains
            LET product = DOCUMENT(Product, v.product_key)
            RETURN merge({
                serial_key: v._key,
                replaced: e.replaced,
                serial_code: v.code,
                product_key: product._key,
                product_code: product.code,
                product_description: product.description
      })
  """

  GET_AVAILABLE_SERIALS_IN_BATCH = """
    FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && w.active == true
        && w._to == @job_key
      LET serial = DOCUMENT(Serial, w.serial_key)
      RETURN serial
  """

  GET_ALL_SERIALS = """
    LET batch_serials = @batch_key ? (
      FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
      RETURN s._key
    ) : null
    FOR s IN Serial
    FILTER
      (@wo_key? s.wo_key == @wo_key: true)
      && (@product_key? s.product_key == @product_key: true)
      && (@search ? CONTAINS(LOWER(s.code), LOWER(@search)) : true)
      && (@batch_key ? s._key IN batch_serials : true)

      LET used = (
        FOR linked_serial IN contains
            FILTER linked_serial._to == s._id
            && linked_serial.replaced == false
            RETURN linked_serial
        )

      FILTER @filter_used?(s.quantity == null ||  count(used) < s.quantity):true

    LIMIT @limit
    RETURN merge( { used: count(used) } , s)
  """

  GET_SERIALS_IN_PRODUCT = """
    FOR s IN Serial
      FILTER s.product_key == @product_key
      RETURN s
  """

  GET_SERIALS_FOR_SERIAL_CODE = """
    FOR s IN Serial
      FILTER (@serial_key ? s._key != @serial_key : true) && s.code == @serial
      && s.product_key == @product_key
      RETURN s
  """

  GET_ALL_SERIALS_IN_WORK_ORDER = """
    FOR s IN Serial
      FILTER s.wo_key == @wo_key
      RETURN s
  """

  GET_AVAILABLE_WIP_SERIALS = """
    FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && (
          w._to == CONCAT('Phase/', @phase_key )
          || ( @job_key ? w._to == CONCAT('Job/', @job_key) : false ) // add wip allocated to job if job_key is provided
        )
      LET serial = DOCUMENT(Serial, w.serial_key)
      LET active = PARSE_IDENTIFIER(w._to).collection == 'Job'
      SORT serial.code
      RETURN MERGE(KEEP(serial, '_key', 'code', 'counter_key'), { active })
  """

  GET_SERIALS_FOR_CODE = """
    FOR s IN Serial
      FILTER (s.code == @serial_code && s.product_key == @product_key)
      RETURN s
  """

  FIND_SERIALS = """

    FOR s IN Serial

    // FILTER BY DOCUMENT PROPERTIES
    FILTER
      // When filtering by document key, parameters will be arrays
      (@serial_key ? POSITION(@serial_key, s._key) : true)
      && (@serial_search ? CONTAINS(s.code, @serial_search) : true)
      && (@created_by ? POSITION(@created_by[* RETURN CONCAT('User/', CURRENT)], s.created_by) : true)
      && (@time_created_from ? s.created >= @time_created_from : true)
      && (@time_created_to ? s.created <= @time_created_to : true)
      && (@deleted ? true : s.deleted == false)
      && (@filter_unreleased ? s.released != null : true)
      && (@advanced_filters
        ? LENGTH(
            // This subquery returns match true/false for each filter
            FOR advanced_filter IN NOT_NULL(@advanced_filters.filters, [])
            FOR d IN s.data
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

    LET process_phases = document(Product, s.product_key).process_phases[* RETURN document(Phase, CURRENT)]

    LET data = (
        FOR phase IN process_phases
        FOR step IN phase.step_sequence[* RETURN document(Step, CURRENT)]
        FILTER step.type == 'form'
        FOR step_field in NOT_NULL(step.form_fields, [])
        LET value = FIRST(
            FOR serial_field in s.data
            FILTER serial_field.form_field_key == step_field._key
            RETURN serial_field.value
        )
        RETURN merge(step_field, { value })
    )

    LET grid_data = (
      FOR field_value IN NOT_NULL(s.data, [])
        FOR field IN NOT_NULL(@fields, [])
        FILTER
          field._key == field_value.form_field_key || field._key == field_value.custom_field_key
        RETURN MERGE(field, { value: field_value.value })
    )

    // FILTER BY LINKS

    // PRODUCT
    let product = FIRST(
        FOR product IN Product
        FILTER product._key == s.product_key
        RETURN product
    )

    FILTER
      (@product_key ? product._key IN @product_key : true)
      && (@product_code_search ? CONTAINS(LOWER(product.code), LOWER(@product_code_search)) : true)

    // FILTER BY COMPONENTS
    LET children=(
        FOR v, e IN 1..999 OUTBOUND s._id contains
            FILTER @contains ? (CONTAINS(LOWER(v.code), LOWER(@contains))) : true
            FILTER e.replaced == false
            RETURN v.code
        )

    LET parents=(
        FOR v, e IN 1..999 INBOUND s._id contains
            FILTER @is_contained_in ? (CONTAINS(LOWER(v.code), LOWER(@is_contained_in))) : true
            FILTER e.replaced == false
            RETURN v.code
        )

    FILTER @contains ? count(children)>0 : true
    FILTER @is_contained_in ? count(parents)>0 : true



    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(s, {
      data,
      product,
      grid_data,
      wo_code: DOCUMENT(WorkOrder, s.wo_key).wo_code
    })

    FILTER
      (@work_order_search ? CONTAINS(LOWER(base_result.wo_code), LOWER(@work_order_search)) : true)

     // LIMIT FILTERED RECORDS
    SORT base_result.@sort_by @sorting_order

    LIMIT @offset, @limit || null
    return base_result
  """


  BOOK_SERIAL_WIP = """
    FOR w IN wip
    FILTER w.serial_key IN @serial_keys
    UPDATE w WITH { _to: CONCAT('Job/', @job_key), active: true } IN wip
  """

  DELETE_BATCH_SERIALS = """
    FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
    SORT s.created DESC
    LIMIT @to_delete
    REMOVE s IN Serial
  """

  CLEANUP_SERIAL_BATCH_LINKS = """
    FOR bs IN batch_serial
    FILTER !DOCUMENT(bs._from) || !DOCUMENT(bs._to)
    REMOVE bs IN batch_serial
  """

  REMOVE_PHASE_DATA_FROM_SERIALS = """
    FOR s IN Serial
    FILTER s._key IN @serial_keys
    LET new_serial_data = (
      FOR form_field IN s.data
      RETURN form_field.phase_key IN @phase_keys
        ? MERGE(form_field, { value: null })
        : form_field
    )
    UPDATE s WITH { data: new_serial_data } IN Serial
  """
