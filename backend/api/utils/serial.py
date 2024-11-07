
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

  GET_ALL_COMPONENTS_IN_BATCH = """
    FOR linked_serial IN contains
      FILTER linked_serial._from == @from_id
      RETURN DOCUMENT(Serial, linked_serial._to)
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
      && (@include_unreleased ? true : s.released != null)
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
      FILTER (@serial_key ? s._key != @serial_key : true) && UPPER(s.code) == UPPER(@serial)
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
        FOR phase IN NOT_NULL(process_phases, [])
        LET steps = NOT_NULL(phase.step_sequence[* RETURN document(Step, CURRENT)], [])
        FOR step IN steps
        FILTER step.type == 'form'
        FOR step_field in NOT_NULL(step.form_fields, [])
        LET value = FIRST(
            FOR serial_field in NOT_NULL(s.data, [])
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

  FIND_WO_SERIALS = """
    FOR s IN Serial

    // FILTER BY DOCUMENT PROPERTIES
    FILTER
      (@work_order_key ? s.wo_key == @work_order_key : true)
      && s.deleted == false

    LET data = (
        FOR serial_field in NOT_NULL(s.data, [])
          let step = DOCUMENT(Step, serial_field.step_key)
          let phase = DOCUMENT(Phase, serial_field.phase_key)
          let customField = DOCUMENT(CustomField, serial_field.custom_field_key)
          RETURN MERGE(serial_field, {
              step_title: step !=null ? step.title : null,
              step_description: step !=null ? step.description : null,
              phase_alias: phase !=null ? phase.alias : null,
              phase_description: phase !=null ? phase.description : null,
              custom_field_type: customField!= null ? customField.type : null,
              custom_field_name: customField!= null ? customField.name : null
          })
    )

    // PRODUCT
    let product_code = FIRST(
        FOR product IN Product
        FILTER product._key == s.product_key
        RETURN product.code
    )

    let batch = FIRST(
        FOR edge IN batch_serial
         FILTER edge._to == s._id
         LET batch = DOCUMENT(Batch, edge._from)

         RETURN batch

    )

    let user = FIRST(
        FOR user IN User
        FILTER user._key == s.created_by
        RETURN user
    )

    LET original_data = (
        LET job = FIRST( FOR j IN Job FILTER j._key == batch.job_key RETURN j )

        LET batch_step_data = (
          FOR step IN job.step_sequence
            LET step_data = KEEP(step, '_key', 'type')
            LET execution_data = FIRST(
              FOR sed IN StepExecutionData
              FILTER
                sed.batch_key == batch._key
                && sed.step_key == step._key
                && sed.canceled == null
              RETURN KEEP(sed, 'form_data')
            )
          RETURN execution_data ? execution_data.form_data : []
        )
        RETURN FLATTEN(batch_step_data, 3)
    )

    let merged_data = (
        FOR serial_data_field in data
            let wo_field = FIRST(
                FOR original_field in FIRST(original_data)
                        FILTER original_field.form_field_key == serial_data_field.form_field_key
                    RETURN original_field
                )
        RETURN MERGE(serial_data_field, { wo_value: wo_field!=NULL ? wo_field.value: null})
    )


    // RETURN RESULTS, WITH LINKS IF REQUESTED
    return MERGE(s, {
      data: merged_data,
      product_code,
      wo_code: DOCUMENT(WorkOrder, s.wo_key).wo_code,
      batch_key: batch._key,
      job_key: batch.job_key,
      phase_key: batch.phase_key,
      user_name: user.name,
      user_surname: user.surname,
    })

  """

  FIND_WO_BATCH = """
    FOR b in Batch
        FILTER b.work_order_key == @work_order_key

        let phase = DOCUMENT(Phase, b.phase_key)
        LET job = FIRST( FOR j IN Job FILTER j._key == b.job_key RETURN j )

        LET original_data = (
            LET batch_step_data = (
              FOR step_seq IN job.step_sequence
                let step = DOCUMENT(Step, step_seq._key)
                LET execution_data = FIRST(
                  FOR sed IN StepExecutionData
                  FILTER
                    sed.batch_key == b._key
                    && sed.step_key == step_seq._key
                    && sed.canceled == null
                  RETURN KEEP(sed, 'form_data', 'user_key')
                )

                LET aug_data = (
                    FOR data in NOT_NULL(execution_data.form_data, [])
                        let customField = DOCUMENT(CustomField, data.custom_field_key)
                        LET user = FIRST( FOR u IN User FILTER u._key == execution_data.user_key RETURN u )
                        return MERGE(data, {
                              step_title: step !=null ? step.title : null,
                              step_description: step !=null ? step.description : null,
                              phase_alias: phase !=null ? phase.alias : null,
                              phase_description: phase !=null ? phase.description : null,
                              custom_field_type: customField!= null ? customField.type : null,
                              custom_field_name: customField!= null ? customField.name : null,
                              user_name: user.name,
                              user_surname: user.surname,
                            })
                )
              RETURN aug_data
            )
            RETURN FLATTEN(batch_step_data, 3)
        )


        FILTER original_data != [[]]



        RETURN {
            data: FIRST(original_data),
            wo_code: DOCUMENT(WorkOrder, @work_order_key).wo_code,
            product_code: job.product_code,
            batch_key: b._key,
            job_key: b.job_key,
            phase_key: b.phase_key,
            quantity: b.qt_total,
            created: b.start
        }
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
