# ==========================
# HOME SCREEN
# ==========================

## >>>>>>>>> MODIFY assignment data accoding to final schema
get_jobs_for_user = """

	// Get jobs assigned directly to user
	LET user_jobs = (
    // Traverse assignments graph
    FOR j,e IN 1..1 INBOUND @user assigned_to 
      // filter non-job assignments (Department, etc.)
      FILTER e._from LIKE "Job%" 
      // Get jobs in order according to queue
      SORT e._key 
      RETURN j)

	// Same thing for jobs assigned to the user's department
	LET dep_jobs = (
		FOR j,e IN 2..2 ANY @user assigned_to 
			FILTER e._from LIKE "Job%" 
			SORT e._key 
			RETURN j)

	RETURN { assigned_to_user: user_jobs, assigned_to_dep: dep_jobs }

"""

# >>>>> TO BE TESTED
get_last_job_for_user = """

	// Starting from work session
	LET last_job = LAST(
		FOR ws in WorkSession
			FILTER ws.user === @user
			SORT ws.end
			RETURN ws._to
		)
	
	FOR j in Job
		FILTER j._id == last_job AND j.status == 'started'
		
	RETURN j

"""



# ==========================
# WORK SESSION SCREEN
# ==========================

# Products Docs are to be fetched as static docs served by NGINX
# Job data should already be available
# get Product BoM

get_product_bom = """
	
	LET subassemblies = (
		FOR v,e IN 1..1 ANY @phase requires
			FILTER e._to LIKE 'Product/%'
			RETURN {'code': v.code, "description": v.description, 'required_qt': e.required_qt}
	)

	LET other_materials = (
		FOR v,e IN 1..1 ANY @phase requires
			FILTER e._to LIKE 'ProductionItem%'
			COLLECT class = v.class INTO items_by_class = {
				"code": v.code, 
				"description": v.description,
				"required_qt": e.required_qt
			}
			RETURN { [class]: items_by_class }
	)
	
	RETURN MERGE({"subassemblies": subassemblies}, MERGE(FLATTEN(other_materials)))
	
"""

# Get tasks
	""" 
	besides calling results from DB, files should be fetched 
	from the following folder: 
	
	app/files/products/<Product_key>/Procedure/<Phase_key>/
	
	"""
get_job_tasks = """
	
	// Draft - final implementation will depend on how forms will be rendered
	FOR t in Task
		FILTER t.phase = @phase
		SORT t.sequence
		RETURN t

"""

# Get issues related to Product/WL/Job and relative updates
	""" 
	besides calling results from DB, files should be fetched 
	from the following folder: 
	
	app/files/issues/<first three digits of the issue _key>/<Issue _key>/
	
	"""
get_issues_for_user = """

	LET job_issues = (FOR i IN Issues FILTER i.job == @job RETURN i)
	LET product_issues = (FOR i IN Issues FILTER i.product == @product RETURN i)
	LET wl_issues = (FOR i IN Issues FILTER i.wo_line == @wo_line RETURN i)
	LET phase_issues = (FOR i IN Issues FILTER i.phase == @phase RETURN i)
	LET operation_issues = (FOR i IN Issues FILTER i.operation == @operation RETURN i)

	RETURN {job_issues, product_issues, wl_issues, phase_issues, operation_issues}

"""

"""

