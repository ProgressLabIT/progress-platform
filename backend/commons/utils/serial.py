
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

  GET_SERIALS_IN_BATCH = """
    FOR edge IN batch_serial
      FILTER edge._from == @from_id
      RETURN DOCUMENT(Serial, edge._to)
  """

  GET_SERIALS_IN_WORK_ORDER = """
    FOR s IN Serial
      FILTER s.wo_key == @wo_key
      RETURN s
  """

  GET_ALL_SERIALS = """
    FOR s IN Serial
    FILTER
       (@wo_key? s.wo_key == @wo_key: true)
       && (@product_key? s.product_key == @product_key: true)
       && (@search ? (
        CONTAINS(LOWER(s.code), LOWER(@search))
        ) : true)
    LIMIT @limit
    RETURN s
  """

  GET_SERIALS_IN_PRODUCT = """
    FOR s IN Serial
      FILTER s.product_key == @product_key
      RETURN s
  """

  GET_SERIALS_FOR_SERIAL_NO = """
    FOR s IN Serial
      FILTER s._key != @serial_key && s.code == @serial
      RETURN s
  """

  GET_ALL_SERIALS_IN_WORK_ORDER = """
    FOR s IN Serial
      FILTER s.wo_key == @wo_key
      RETURN s
  """

  GET_AVAILABLE_SERIALS_IN_WORK_ORDER = """
    FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && w._from == @phase_key
        && LIKE(w._to, "Serial%")
        && !w.active
      LET serial = DOCUMENT(Serial, w._to)
      return serial
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
            FILTER serial_field.custom_field_key == step_field.custom_field_key
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

    // LIMIT FILTERED RECORDS
    SORT s.created


    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(s, {
      data,
      product,
      grid_data,
      wo_code: DOCUMENT(WorkOrder, s.wo_key).wo_code
    })

    FILTER
      (@work_order_search ? CONTAINS(LOWER(base_result.wo_code), LOWER(@work_order_search)) : true)

    LIMIT @offset, @limit || null
    return base_result

  """
