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
