
class Queries:

  GET_PRODUCT_STEPS = """
    FOR phase IN Phase
      FILTER phase.product_key == @product_key
      RETURN {
        alias: phase.alias,
        phase_key: phase._key,
        steps: (
          FOR step IN Step
            FILTER step._key in phase.step_sequence
            return step
        )}
  """



  FIND_SERIALS = """

     FOR s IN Serial

    // FILTER BY DOCUMENT PROPERTIES
    FILTER
      // When filtering by document key, parameters will be arrays
      (@serial_key ? POSITION(@serial_key, s._key) : true)
      && (@serial_key_search ? CONTAINS(s._key, @serial_key_search) : true)
      && (@created_by ? POSITION(@created_by[* RETURN CONCAT('User/', CURRENT)], s.created_by) : true)
      && (@time_created_from ? s.created >= @time_created_from : true)
      && (@time_created_to ? s.created <= @time_created_to : true)
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

      let fields = (
FOR field IN CustomField
        FILTER field.use_in_serial == True
        return merge (field)
        )

    LET serial_data = (
      FOR field_value IN NOT_NULL(s.data, [])
      for field IN fields
      FILTER
        field._key == field_value.form_field_key || field._key == field_value.custom_field_key
      RETURN MERGE(field, { value: field_value.value })
    )


    // FILTER BY LINKS

    // PRODUCT
    LET product = FIRST(
      FOR l IN 1..1 OUTBOUND s serial_rel
      FILTER PARSE_IDENTIFIER(l._id).collection == 'Product'
      RETURN l
    )

    FILTER
      (@product_key ? product._key IN @product_key : true)
      && (@product_code_search ? CONTAINS(LOWER(product.code), LOWER(@product_code_search)) : true)

    // LIMIT FILTERED ISSUE RECORDS
    SORT s.created
    LIMIT @limit || null

    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(s, {
      ext_data: s.data,
      data: serial_data
    })

    LET serial_links = { product }

    RETURN @with_links ? MERGE(base_result, { links: serial_links }) : base_result
  """
