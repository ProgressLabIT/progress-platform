class Queries:

  GET_PRODUCT_KPIS = """
    LET now = DATE_NOW()

    LET product = DOCUMENT(Product, @product_key)
    LET w_type = product.kpi_window_type
    LET w_size = product.kpi_window_size

    LET window_data = (
      FOR wo IN WorkOrder
      FILTER wo.product_key == @product_key
      SORT wo.end DESC

      FILTER w_type == 'time' ? DATE_DIFF(wo.end, now, 'd') < w_size : true

      LET MAX_COUNT = 100
      LIMIT count_filter = w_type == 'count' ? w_size : MAX_COUNT

      RETURN wo
    )

    LET product_processing_time = AVERAGE(FOR wo IN window_data RETURN wo.processing_time / wo.qt_completed)

    LET product_processing_cost = AVERAGE(FOR wo IN window_data RETURN wo.processing_cost / wo.qt_completed)

    LET product_material_cost = AVERAGE(FOR wo IN window_data RETURN wo.material_cost / wo.qt_completed)

    LET product_total_cost = AVERAGE(FOR wo IN window_data RETURN wo.total_cost / wo.qt_completed)

    LET wo_keys = (FOR wo IN window_data RETURN wo._key)
    LET phases = UNIQUE(FLATTEN(FOR wo IN window_data RETURN wo.phase_sequence))

    LET overall_kpis = {
      product_processing_time,
      product_processing_cost,
      product_material_cost,
      product_total_cost,
    }

    LET phase_data = (
      FOR b IN Batch
      FILTER POSITION(phases, b.phase_key) && POSITION(wo_keys, b.work_order_key)
      COLLECT phase = b.phase_key
      AGGREGATE
        processing_time = AVERAGE(b.unit_processing_time),
        processing_cost = AVERAGE(b.unit_processing_cost),
        material_cost = AVERAGE(b.unit_material_cost),
        total_cost = AVERAGE(b.unit_processing_cost + b.unit_material_cost)

      RETURN {
        phase_key: phase,
        processing_time,
        processing_cost,
        material_cost,
        total_cost
      }
    )

    RETURN MERGE ([overall_kpis, phase_data])
  """

  GET_PRODUCT_STATS = """
    LET product_id = CONCAT('Product/', @product_key)
    LET last_year = DATE_SUBTRACT(DATE_NOW(), 1, 'y')

    LET work_orders = (
      FOR wo IN WorkOrder
      FILTER wo.product_key == @product_key && wo.end >= last_year
      LIMIT 100
      RETURN MERGE(KEEP(wo, '_key', 'end'), { unit_processing_time: wo.processing_time / wo.qt_completed })
    )

    LET phases = (
      // process may change over time. Use current process data.
      FOR phase IN 1..1 OUTBOUND product_id requires
      RETURN KEEP(phase, '_key', 'alias')
    )

    LET batches = (
      FOR b in Batch
      FILTER
        b.end >= last_year
        && b.phase_key IN phases[*]._key
        && !b.canceled
      RETURN b
    )

    LET unit_order_processing_times = work_orders[*].unit_processing_time
    LET product_processing_time = {
      standard: SUM(phases[*].parameters.std_processing_time),
      median: MEDIAN(unit_order_processing_times),
      min: MIN(unit_order_processing_times),
      p10: PERCENTILE(unit_order_processing_times, 10),
      p20: PERCENTILE(unit_order_processing_times, 20),
      p30: PERCENTILE(unit_order_processing_times, 30),
      p40: PERCENTILE(unit_order_processing_times, 40),
      p50: PERCENTILE(unit_order_processing_times, 50),
      p60: PERCENTILE(unit_order_processing_times, 60),
      p70: PERCENTILE(unit_order_processing_times, 70),
      p80: PERCENTILE(unit_order_processing_times, 80),
      p90: PERCENTILE(unit_order_processing_times, 90),
      max: MAX(unit_order_processing_times),
      std_dev: STDDEV_SAMPLE(unit_order_processing_times)
    }

    LET phase_processing_times = (
      FOR p IN phases
      LET phase_batch_times = batches[* FILTER CURRENT.phase_key == p._key].unit_processing_time
      RETURN MERGE(p,
        {
          processing_time: {
            standard: p.parameters.std_processing_time,
            median: MEDIAN(phase_batch_times),
            min: MIN(phase_batch_times),
            p10: PERCENTILE(phase_batch_times, 10),
            p20: PERCENTILE(phase_batch_times, 20),
            p30: PERCENTILE(phase_batch_times, 30),
            p40: PERCENTILE(phase_batch_times, 40),
            p50: PERCENTILE(phase_batch_times, 50),
            p60: PERCENTILE(phase_batch_times, 60),
            p70: PERCENTILE(phase_batch_times, 70),
            p80: PERCENTILE(phase_batch_times, 80),
            p90: PERCENTILE(phase_batch_times, 90),
            max: MAX(phase_batch_times),
            std_dev: STDDEV_SAMPLE(phase_batch_times)
          }
        }
      )
    )

    LET issues = (
      FOR v, e, p IN 2..2 ANY product_id issue_rel
      LET issue = p.vertices[1]
      FILTER
        issue.created >= last_year
        && LENGTH(p.edges[* FILTER PARSE_IDENTIFIER(CURRENT._to).collection == 'Phase'])
      RETURN MERGE(issue, { phase_key: p.vertices[2]._key })
    )

    RETURN { product_processing_time, phase_processing_times, issues }
  """

